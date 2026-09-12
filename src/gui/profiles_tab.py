"""Profiles tab: a profile picker, an editable form for profile-level
settings (name/window match/priority), and a bindings table with
add/edit/remove - plus the binding editor dialog.
"""
from __future__ import annotations

import copy
import json
import shutil

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src import tighc
from src.gui import workers
from src.ranges import VibeRange
from src.tighc import PROFILES_DIR, load_profiles

BINDING_COLUMNS = ("id", "keys", "devices", "vibe", "enabled")
BINDING_HEADERS = {"id": "ID", "keys": "Keys", "devices": "Devices", "vibe": "Vibe %", "enabled": "Enabled"}


def _binding_to_editable(binding: dict) -> dict:
    """Convert one of Profile.bindings' parsed dicts (VibeRange/frozenset objects) into a plain JSON/UI-friendly dict."""
    return {
        "id": binding["id"],
        "keys": list(binding["keys"]),
        "enabled": binding["enabled"],
        "devices": ["all"] if binding["devices"] is None else sorted(binding["devices"]),
        "vibe_low": binding["vibe"].low,
        "vibe_high": binding["vibe"].high,
    }


class BindingDialog(QDialog):
    """Modal add/edit dialog for one binding."""

    def __init__(self, parent=None, existing: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Binding")
        self.result_binding: dict | None = None

        layout = QFormLayout(self)
        self.id_field = QLineEdit(existing["id"] if existing else "")
        self.keys_field = QLineEdit(",".join(existing["keys"]) if existing else "")
        self.devices_field = QLineEdit(",".join(existing["devices"]) if existing else "all")
        self.vibe_low_field = QLineEdit(f"{existing['vibe_low'] * 100:.0f}" if existing else "30")
        self.vibe_high_field = QLineEdit(f"{existing['vibe_high'] * 100:.0f}" if existing else "60")
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(existing["enabled"] if existing else True)

        layout.addRow("Binding id:", self.id_field)
        layout.addRow("Keys (comma-separated):", self.keys_field)
        layout.addRow("Devices (nicknames or 'all'):", self.devices_field)
        layout.addRow("Vibe % low (0-100):", self.vibe_low_field)
        layout.addRow("Vibe % high (0-100):", self.vibe_high_field)
        layout.addRow(self.enabled_check)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_ok(self):
        try:
            bid = self.id_field.text().strip()
            if not bid:
                raise ValueError("binding id is required")
            keys = [k.strip().lower() for k in self.keys_field.text().split(",") if k.strip()]
            if not keys:
                raise ValueError("at least one key is required")
            devices_raw = [d.strip().lower() for d in self.devices_field.text().split(",") if d.strip()] or ["all"]
            vibe_low = float(self.vibe_low_field.text()) / 100.0
            vibe_high = float(self.vibe_high_field.text()) / 100.0
            VibeRange(vibe_low, vibe_high)
            self.result_binding = {
                "id": bid, "keys": keys, "enabled": self.enabled_check.isChecked(),
                "devices": devices_raw, "vibe_low": vibe_low, "vibe_high": vibe_high,
            }
            self.accept()
        except ValueError as e:
            QMessageBox.critical(self, "Binding", str(e))


class ProfilesTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.current_profile_id: str | None = None
        self.current_bindings: list[dict] = []

        outer = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self._on_profile_combo_changed)
        top.addWidget(self.profile_combo)
        new_btn = QPushButton("New profile...")
        new_btn.setProperty("accent", "true")
        new_btn.clicked.connect(self._on_new_profile)
        top.addWidget(new_btn)
        reload_btn = QPushButton("Reload all from disk")
        reload_btn.clicked.connect(self._on_reload_profiles)
        top.addWidget(reload_btn)
        restore_btn = QPushButton("Restore from GitHub...")
        restore_btn.clicked.connect(self._on_restore_profile)
        top.addWidget(restore_btn)
        update_btn = QPushButton("Update profiles from GitHub")
        update_btn.clicked.connect(self._on_update_profiles_from_github)
        top.addWidget(update_btn)
        open_folder_btn = QPushButton("Open profiles folder")
        open_folder_btn.clicked.connect(self._open_profiles_folder)
        top.addWidget(open_folder_btn)
        top.addStretch(1)
        outer.addLayout(top)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll, stretch=1)
        body = QWidget()
        scroll.setWidget(body)
        body_layout = QVBoxLayout(body)

        meta_group = QGroupBox("Profile settings")
        form = QFormLayout(meta_group)
        self.name_field = QLineEdit()
        form.addRow("Display name:", self.name_field)
        self.windows_field = QLineEdit()
        form.addRow("Window title match(es), comma-separated (case-sensitive):", self.windows_field)
        self.exact_match_check = QCheckBox("Exact window title match (prevents e.g. 'grounded' matching 'grounded 2')")
        form.addRow(self.exact_match_check)
        self.priority_field = QLineEdit()
        form.addRow("Binding priority order (comma-separated ids):", self.priority_field)
        save_btn = QPushButton("Save profile")
        save_btn.setProperty("accent", "true")
        save_btn.clicked.connect(self._on_save_profile)
        form.addRow(save_btn)
        body_layout.addWidget(meta_group)

        bindings_group = QGroupBox("Bindings")
        bindings_layout = QVBoxLayout(bindings_group)
        self.bindings_tree = QTreeWidget()
        self.bindings_tree.setHeaderLabels([BINDING_HEADERS[c] for c in BINDING_COLUMNS])
        bindings_layout.addWidget(self.bindings_tree)
        binding_btns = QHBoxLayout()
        add_btn = QPushButton("Add binding...")
        add_btn.clicked.connect(self._on_add_binding)
        binding_btns.addWidget(add_btn)
        edit_btn = QPushButton("Edit binding...")
        edit_btn.clicked.connect(self._on_edit_binding)
        binding_btns.addWidget(edit_btn)
        remove_btn = QPushButton("Remove binding")
        remove_btn.clicked.connect(self._on_remove_binding)
        binding_btns.addWidget(remove_btn)
        note = QLabel("(remember to Save profile above after changing bindings)")
        note.setProperty("hint", "true")
        binding_btns.addWidget(note)
        binding_btns.addStretch(1)
        bindings_layout.addLayout(binding_btns)
        body_layout.addWidget(bindings_group)
        body_layout.addStretch(1)

    # ------------------------------------------------------- id/display mapping
    def _profile_display_name(self, profile_id: str) -> str:
        profile = self.main_window.controller.profiles.get(profile_id)
        return profile.name if profile else profile_id

    def _profile_id_for_display(self, display_name: str) -> str:
        for profile_id, profile in self.main_window.controller.profiles.items():
            if profile.name == display_name:
                return profile_id
        return display_name

    # --------------------------------------------------------------- refresh
    def refresh_profile_list(self):
        """
        Repopulate this tab's, the Test tab's, and the Run tab's profile
        dropdowns from controller.profiles, keeping the current selection
        if it's still valid (falling back to the alphabetically first
        profile otherwise). Called after anything that adds, removes, or
        reloads profiles.
        """
        controller = self.main_window.controller
        ids = sorted(controller.profiles.keys())
        display_names = sorted(self._profile_display_name(pid) for pid in ids)

        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(display_names)
        self.profile_combo.blockSignals(False)

        self.main_window.test_tab.set_profile_choices(display_names)
        self.main_window.run_tab._refresh_override_choices()

        if not ids:
            self.current_profile_id = None
            self.main_window.test_tab.refresh_test_bindings()
            return
        if self.current_profile_id not in ids:
            self.current_profile_id = ids[0]
        self.profile_combo.setCurrentText(self._profile_display_name(self.current_profile_id))
        self._load_profile_into_form(self.current_profile_id)
        self.main_window.test_tab.ensure_valid_selection(ids, self._profile_display_name(self.current_profile_id))
        self.main_window.test_tab.refresh_test_bindings()

    def _on_profile_combo_changed(self, _index: int):
        self._load_profile_into_form(self._profile_id_for_display(self.profile_combo.currentText()))

    def _load_profile_into_form(self, profile_id: str | None):
        """Populate the form/bindings table from controller.profiles[profile_id], replacing any unsaved edits."""
        controller = self.main_window.controller
        if not profile_id or profile_id not in controller.profiles:
            return
        self.current_profile_id = profile_id
        profile = controller.profiles[profile_id]
        self.name_field.setText(profile.name)
        self.windows_field.setText(", ".join(profile.window_titles))
        self.exact_match_check.setChecked(profile.window_title_exact)
        self.priority_field.setText(", ".join(profile.priority))
        self.current_bindings = [_binding_to_editable(b) for b in profile.bindings]
        self._refresh_bindings_tree()

    def _refresh_bindings_tree(self):
        self.bindings_tree.clear()
        for b in self.current_bindings:
            vibe = f"{b['vibe_low'] * 100:.0f}-{b['vibe_high'] * 100:.0f}"
            item = QTreeWidgetItem([b["id"], "+".join(b["keys"]), ",".join(b["devices"]), vibe, "yes" if b["enabled"] else "no"])
            self.bindings_tree.addTopLevelItem(item)

    # ------------------------------------------------------------- profile CRUD
    def _on_new_profile(self):
        """Asks for a folder id, display name, and window-title match, seeding from profiles/minecraft/ as a template."""
        new_id, ok = QInputDialog.getText(self, "New profile", "Folder id (letters/numbers/underscores):")
        if not ok or not new_id:
            return
        new_id = tighc._slugify(new_id)
        new_dir = PROFILES_DIR / new_id
        if new_dir.exists():
            QMessageBox.critical(self, "New profile", f"profiles/{new_id} already exists.")
            return
        display_name, ok = QInputDialog.getText(self, "New profile", "Display name:", text=new_id.title())
        if not ok:
            return
        display_name = display_name or new_id
        window_title, ok = QInputDialog.getText(self, "New profile", "Window title to match (case-sensitive substring):", text=new_id)
        if not ok:
            return
        window_title = window_title or new_id

        template_dir = PROFILES_DIR / "minecraft"
        if (template_dir / "profile.json").exists():
            profile_data = json.loads((template_dir / "profile.json").read_text(encoding="utf-8"))
        else:
            profile_data = copy.deepcopy(tighc.DEFAULT_MINECRAFT_PROFILE)
        profile_data["name"] = display_name
        profile_data["window_titles"] = [window_title]

        new_dir.mkdir(parents=True)
        (new_dir / "profile.json").write_text(json.dumps(profile_data, indent=2), encoding="utf-8")
        try:
            profile = tighc._load_profile(new_dir)
        except Exception as e:
            shutil.rmtree(new_dir)
            QMessageBox.critical(self, "New profile", f"Failed to create profile: {e}")
            return

        self.main_window.controller.profiles[profile.id] = profile
        self.current_profile_id = profile.id
        self.refresh_profile_list()
        self.main_window.enqueue_log(f"Created profile '{profile.name}' (copied bindings from the Minecraft template).")

    def _on_reload_profiles(self):
        """Re-runs the full profile loader and replaces the controller's profile set in place."""
        controller = self.main_window.controller
        try:
            fresh = load_profiles()
        except RuntimeError as e:
            QMessageBox.critical(self, "Reload profiles", str(e))
            return
        controller.profiles.clear()
        controller.profiles.update(fresh)
        self.refresh_profile_list()
        self.main_window.enqueue_log("Profiles reloaded from disk.")

    def _compose_profile(self) -> dict:
        """Build the profile dict to write to profile.json from the current form fields and self.current_bindings."""
        name = self.name_field.text().strip() or self.current_profile_id
        window_titles = [t.strip() for t in self.windows_field.text().split(",") if t.strip()]
        if not window_titles:
            raise ValueError("at least one window title is required")
        exact_match = self.exact_match_check.isChecked()
        priority = [t.strip() for t in self.priority_field.text().split(",") if t.strip()]
        profile = {"name": name, "window_titles": window_titles}
        if exact_match:
            profile["window_title_exact"] = True
        if priority:
            profile["priority"] = priority
        profile["bindings"] = []
        for b in self.current_bindings:
            VibeRange(b["vibe_low"], b["vibe_high"])
            profile["bindings"].append({
                "id": b["id"], "keys": b["keys"], "enabled": b["enabled"],
                "devices": b["devices"], "vibe": [b["vibe_low"], b["vibe_high"]],
            })
        return profile

    def _on_restore_profile(self):
        """Downloads the currently selected profile from the TIGHC Profiles GitHub repo and overwrites the local copy."""
        if not self.current_profile_id:
            QMessageBox.information(self, "Restore from GitHub", "No profile selected.")
            return
        confirm = QMessageBox.question(
            self, "Restore from GitHub",
            f"Download '{self.current_profile_id}' from the TIGHC Profiles GitHub repo and overwrite your local copy?\n\nThis cannot be undone.",
        )
        if confirm != QMessageBox.Yes:
            return
        profile_id = self.current_profile_id

        def do_restore():
            return tighc.restore_profile_from_github(profile_id)

        def on_done(ok):
            if ok:
                self._on_reload_profiles()
                self.main_window.enqueue_log(f"Restored '{profile_id}' from GitHub.")
            else:
                QMessageBox.critical(self, "Restore from GitHub", f"Could not download '{profile_id}' - check your internet connection.")

        workers.run_in_thread(self.main_window.relay, do_restore, on_done)

    def _on_update_profiles_from_github(self):
        """Downloads any profiles from GitHub that aren't yet in the user's profiles dir. Existing profiles aren't overwritten."""
        self.main_window.enqueue_log("Checking GitHub for new profiles...")
        messages: list[str] = []

        def do_update():
            return tighc.download_missing_profiles(log=messages.append)

        def on_done(count):
            for msg in messages:
                self.main_window.enqueue_log(msg)
            if count > 0:
                self._on_reload_profiles()
                self.main_window.enqueue_log(f"Downloaded {count} new profile(s) from GitHub.")
            else:
                self.main_window.enqueue_log("No new profiles found.")

        workers.run_in_thread(self.main_window.relay, do_update, on_done)

    def _open_profiles_folder(self):
        from src.gui.settings_tab import _open_folder
        _open_folder(PROFILES_DIR)

    def _on_save_profile(self):
        """
        Snapshots the current on-disk JSON, writes the new profile.json,
        then immediately tries to load it back through the real engine
        parser - if that fails, the snapshot is restored so a bad edit
        never leaves the profile folder in a broken state.
        """
        if not self.current_profile_id:
            return
        profile_dir = PROFILES_DIR / self.current_profile_id
        profile_path = profile_dir / "profile.json"
        backup = profile_path.read_text(encoding="utf-8")

        try:
            profile_data = self._compose_profile()
        except (ValueError, TypeError) as e:
            QMessageBox.critical(self, "Save profile", f"Invalid value: {e}")
            return

        profile_path.write_text(json.dumps(profile_data, indent=2), encoding="utf-8")
        try:
            profile = tighc._load_profile(profile_dir)
        except Exception as e:
            profile_path.write_text(backup, encoding="utf-8")
            QMessageBox.critical(self, "Save profile", f"Not saved - config is invalid:\n{e}")
            return

        self.main_window.controller.profiles[profile.id] = profile
        self.main_window.enqueue_log(f"Saved profile '{profile.name}'.")
        self._load_profile_into_form(profile.id)

    # ------------------------------------------------------------------ bindings
    def _on_add_binding(self):
        dialog = BindingDialog(self)
        if dialog.exec() != QDialog.Accepted or not dialog.result_binding:
            return
        result = dialog.result_binding
        if any(b["id"] == result["id"] for b in self.current_bindings):
            QMessageBox.critical(self, "Add binding", f"id '{result['id']}' already exists in this profile.")
            return
        self.current_bindings.append(result)
        self._refresh_bindings_tree()

    def _on_edit_binding(self):
        idx = self.bindings_tree.indexOfTopLevelItem(self.bindings_tree.currentItem())
        if idx < 0:
            QMessageBox.information(self, "Edit binding", "Select a binding first.")
            return
        dialog = BindingDialog(self, existing=self.current_bindings[idx])
        if dialog.exec() == QDialog.Accepted and dialog.result_binding:
            self.current_bindings[idx] = dialog.result_binding
            self._refresh_bindings_tree()

    def _on_remove_binding(self):
        idx = self.bindings_tree.indexOfTopLevelItem(self.bindings_tree.currentItem())
        if idx < 0:
            QMessageBox.information(self, "Remove binding", "Select a binding first.")
            return
        del self.current_bindings[idx]
        self._refresh_bindings_tree()
