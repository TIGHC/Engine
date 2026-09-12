"""Settings tab: one form field/checkbox per haptics.json key, plus
user-data-folder shortcuts.
"""
from __future__ import annotations

import subprocess
import sys

from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src import tighc
from src.ranges import VibeRange
from src.tighc import CONFIGS_DIR, PROFILES_DIR, TIGHC_PROFILES_URL, USER_DATA_DIR, load_haptics_config


def _link_label(text: str, url: str) -> QLabel:
    label = QLabel(f'<a href="{url}">{text}</a>')
    label.setOpenExternalLinks(True)
    return label


def _open_folder(path):
    """Open a folder in the system file explorer, creating it first if needed."""
    path.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        import os
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


class SettingsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        self._body = None
        self._build_form()
        scroll.setWidget(self._body)
        self._scroll = scroll

    def _build_form(self):
        body = QWidget()
        layout = QGridLayout(body)
        row = 0
        self.cfg_fields: dict[str, QLineEdit] = {}

        cfg = load_haptics_config()

        def add(label: str, key: str, default) -> None:
            nonlocal row
            layout.addWidget(QLabel(label), row, 0)
            field = QLineEdit(str(default))
            field.setFixedWidth(140)
            layout.addWidget(field, row, 1)
            self.cfg_fields[key] = field
            row += 1

        add("Intiface WS URL:", "intiface_ws", cfg["intiface_ws"])

        self.master_enabled_check = QCheckBox("Master random override enabled")
        self.master_enabled_check.setChecked(cfg["master"]["enabled"])
        layout.addWidget(self.master_enabled_check, row, 0, 1, 2)
        row += 1
        add("Master range % low:", "master_low", cfg["master"]["range"][0] * 100)
        add("Master range % high:", "master_high", cfg["master"]["range"][1] * 100)

        self.smoothing_enabled_check = QCheckBox("Level smoothing enabled")
        self.smoothing_enabled_check.setChecked(cfg["smoothing"]["enabled"])
        layout.addWidget(self.smoothing_enabled_check, row, 0, 1, 2)
        row += 1
        add("Smoothing factor (0-1):", "smoothing_factor", cfg["smoothing"]["factor"])

        self.panic_enabled_check = QCheckBox("Panic key enabled")
        self.panic_enabled_check.setChecked(cfg["panic_key"]["enabled"])
        layout.addWidget(self.panic_enabled_check, row, 0, 1, 2)
        row += 1
        add("Panic key:", "panic_key", cfg["panic_key"]["key"])
        add("Panic hold duration (sec):", "panic_hold", cfg["panic_key"]["hold_duration"])

        layout.addWidget(QLabel("Panic key action:"), row, 0)
        mode_row = QHBoxLayout()
        self.panic_mode_hold = QRadioButton("Suppress for duration")
        self.panic_mode_stop = QRadioButton("Stop engine completely")
        if cfg["panic_key"].get("panic_mode", "hold") == "stop":
            self.panic_mode_stop.setChecked(True)
        else:
            self.panic_mode_hold.setChecked(True)
        mode_row.addWidget(self.panic_mode_hold)
        mode_row.addWidget(self.panic_mode_stop)
        mode_row.addStretch(1)
        mode_widget = QWidget()
        mode_widget.setLayout(mode_row)
        layout.addWidget(mode_widget, row, 1)
        row += 1

        self.reconnect_enabled_check = QCheckBox("Auto-reconnect enabled")
        self.reconnect_enabled_check.setChecked(cfg["auto_reconnect"]["enabled"])
        layout.addWidget(self.reconnect_enabled_check, row, 0, 1, 2)
        row += 1
        add("Reconnect cooldown (sec):", "reconnect_cooldown", cfg["auto_reconnect"]["cooldown"])
        add("Reconnect failure threshold:", "reconnect_threshold", cfg["auto_reconnect"]["failure_threshold"])
        add("Background tick (sec):", "background_tick", cfg["timing"]["background_tick"])

        save_settings_btn = QPushButton("Save settings")
        save_settings_btn.setProperty("accent", "true")
        save_settings_btn.clicked.connect(self._on_save_settings)
        layout.addWidget(save_settings_btn, row, 0)
        row += 1
        hint = QLabel(
            "Takes effect immediately - no restart needed. Exception: a WebSocket URL change needs "
            '"Connect + Scan" (or Stop then Start) to actually reconnect to it.'
        )
        hint.setProperty("hint", "true")
        hint.setWordWrap(True)
        layout.addWidget(hint, row, 0, 1, 2)
        row += 1

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        layout.addWidget(sep2, row, 0, 1, 2)
        row += 1
        header2 = QLabel("User data folders")
        header2.setStyleSheet("font-weight: bold;")
        layout.addWidget(header2, row, 0, 1, 2)
        row += 1

        folders_row = QHBoxLayout()
        for label, path in (
            ("Open user data folder", USER_DATA_DIR),
            ("Open configs folder", CONFIGS_DIR),
            ("Open profiles folder", PROFILES_DIR),
        ):
            btn = QPushButton(label)
            btn.clicked.connect(lambda _checked=False, p=path: _open_folder(p))
            folders_row.addWidget(btn)
        folders_row.addWidget(_link_label("Browse profiles on GitHub", TIGHC_PROFILES_URL))
        folders_row.addStretch(1)
        folders_widget = QWidget()
        folders_widget.setLayout(folders_row)
        layout.addWidget(folders_widget, row, 0, 1, 2)
        row += 1
        data_hint = QLabel("User data (your profiles and settings) is stored separately from the app so it survives updates.")
        data_hint.setProperty("hint", "true")
        data_hint.setWordWrap(True)
        layout.addWidget(data_hint, row, 0, 1, 2)
        row += 1

        reset_btn = QPushButton("Reset settings to defaults")
        reset_btn.clicked.connect(self._on_reset_settings)
        layout.addWidget(reset_btn, row, 0)

        old_body = self._body
        self._body = body
        if hasattr(self, "_scroll"):
            self._scroll.setWidget(body)
        if old_body is not None:
            old_body.deleteLater()

    def _on_reset_settings(self):
        """Reset haptics.json to defaults by deleting it and rebuilding the form."""
        confirm = QMessageBox.question(
            self, "Reset settings to defaults",
            "Delete your haptics.json and reset all settings to their defaults?\n\nThis cannot be undone.",
        )
        if confirm != QMessageBox.Yes:
            return
        path = tighc.HAPTICS_CONFIG_PATH
        if path.exists():
            path.unlink()
        reset_cfg = dict(tighc.DEFAULT_HAPTICS_CONFIG)
        reset_cfg["confirmed_age"] = tighc.CONFIRMED_AGE
        tighc.apply_haptics_config(reset_cfg)
        self.main_window.enqueue_log("Settings reset to defaults.")
        self._build_form()

    def _on_save_settings(self):
        """
        Assemble a full haptics.json-shaped dict from every form field and
        hand it to tighc.apply_haptics_config(), which persists it and
        updates the engine's live settings in place - no restart needed.
        Validates the master-range values form a valid VibeRange first.
        """
        try:
            cfg = {
                "intiface_ws": self.cfg_fields["intiface_ws"].text().strip(),
                "master": {
                    "enabled": self.master_enabled_check.isChecked(),
                    "range": [
                        float(self.cfg_fields["master_low"].text()) / 100.0,
                        float(self.cfg_fields["master_high"].text()) / 100.0,
                    ],
                },
                "smoothing": {
                    "enabled": self.smoothing_enabled_check.isChecked(),
                    "factor": float(self.cfg_fields["smoothing_factor"].text()),
                },
                "panic_key": {
                    "enabled": self.panic_enabled_check.isChecked(),
                    "key": self.cfg_fields["panic_key"].text().strip(),
                    "hold_duration": float(self.cfg_fields["panic_hold"].text()),
                    "panic_mode": "stop" if self.panic_mode_stop.isChecked() else "hold",
                },
                "auto_reconnect": {
                    "enabled": self.reconnect_enabled_check.isChecked(),
                    "cooldown": float(self.cfg_fields["reconnect_cooldown"].text()),
                    "failure_threshold": int(self.cfg_fields["reconnect_threshold"].text()),
                },
                "timing": {"background_tick": float(self.cfg_fields["background_tick"].text())},
                "confirmed_age": tighc.CONFIRMED_AGE,
            }
            VibeRange(*cfg["master"]["range"])
        except ValueError as e:
            QMessageBox.critical(self, "Settings", f"Invalid value: {e}")
            return

        controller = self.main_window.controller
        ws_url_changed = cfg["intiface_ws"] != controller.ws_url
        tighc.apply_haptics_config(cfg)
        # apply_haptics_config() can't itself force an already-open
        # connection to move to a new URL - update the live controller's
        # ws_url too, so at least the *next* connect picks up the change.
        controller.ws_url = cfg["intiface_ws"]
        self.main_window.devices_tab.ws_url_field.setText(cfg["intiface_ws"])

        self.main_window.enqueue_log("Settings saved and applied immediately.")
        if ws_url_changed:
            self.main_window.enqueue_log('Intiface WebSocket URL changed - click "Connect + Scan" (or Stop then Start) to use it.')
