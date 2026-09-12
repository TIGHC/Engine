"""Devices tab: connection controls, the per-channel list, and rename."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.gui import workers
from src.tighc import load_device_registry, save_device_registry


class DevicesTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Intiface WebSocket URL:"))
        # Read-only display, not an editable field here - the Settings tab
        # is the one place that actually persists intiface_ws, so letting
        # this one be edited too would just be a second, easy-to-forget
        # place the URL could silently diverge from what's actually saved.
        self.ws_url_field = QLineEdit(main_window.controller.ws_url)
        self.ws_url_field.setReadOnly(True)
        self.ws_url_field.setFixedWidth(220)
        top.addWidget(self.ws_url_field)
        hint = QLabel("(set in Settings)")
        hint.setProperty("hint", "true")
        top.addWidget(hint)

        self.connect_btn = QPushButton("Connect + Scan")
        self.connect_btn.setProperty("accent", "true")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        top.addWidget(self.connect_btn)

        self.rescan_btn = QPushButton("Rescan")
        self.rescan_btn.clicked.connect(self._on_rescan_clicked)
        top.addWidget(self.rescan_btn)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        top.addWidget(self.disconnect_btn)
        top.addStretch(1)
        layout.addLayout(top)

        # One row per channel - i.e. per motor/capability, not per physical
        # toy - so a dual-motor device shows up as two rows here.
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Nickname", "Device", "Motor", "Output"])
        self.tree.setColumnWidth(0, 220)
        self.tree.setColumnWidth(1, 220)
        self.tree.setColumnWidth(2, 180)
        self.tree.setRootIsDecorated(False)
        layout.addWidget(self.tree, stretch=1)

        btns = QHBoxLayout()
        rename_btn = QPushButton("Rename nickname...")
        rename_btn.clicked.connect(self._on_rename_channel)
        btns.addWidget(rename_btn)
        note = QLabel('Bindings target channels by nickname (or "all"). Each motor/capability is its own channel.')
        note.setProperty("hint", "true")
        btns.addWidget(note)
        btns.addStretch(1)
        layout.addLayout(btns)

    def set_connected(self, is_connected: bool):
        self.connect_btn.setEnabled(not is_connected)
        self.disconnect_btn.setEnabled(is_connected)

    # --------------------------------------------------------------- connect
    def _on_connect_clicked(self):
        controller = self.main_window.controller
        self.connect_btn.setEnabled(False)
        self.main_window.set_connection_status(f"Connecting to {controller.ws_url} ...")
        self.main_window.enqueue_log(f"Connecting to {controller.ws_url} ...")
        workers.submit(self.main_window.bridge, self.main_window.relay, controller.connect(), self._after_connect)

    def _after_connect(self, fut):
        """
        Connect + Scan and Disconnect are mutually exclusive based on
        whether a connection now exists, rather than Connect + Scan always
        re-enabling itself on success - clicking it again while already
        connected would silently open a *second* connection (connect()
        always builds a fresh ButtplugClient) without closing the first.
        """
        controller = self.main_window.controller
        try:
            fut.result()
        except Exception as e:
            self.main_window.enqueue_log(f"Connect failed: {e}")
        is_connected = bool(controller.client)
        self.set_connected(is_connected)
        self.refresh_channels_tree()

    def _on_disconnect_clicked(self):
        """Stops the engine (if running) and disconnects, leaving the app running so the user can reconnect afterward."""
        self.connect_btn.setEnabled(False)
        self.rescan_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(False)
        workers.submit(self.main_window.bridge, self.main_window.relay, self.main_window.controller.shutdown(), self._after_disconnect)

    def _after_disconnect(self, fut):
        try:
            fut.result()
        except Exception as e:
            self.main_window.enqueue_log(f"Disconnect error: {e}")
        self.connect_btn.setEnabled(True)
        self.rescan_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        # shutdown() stops the engine along the way - reflect that on the
        # Run tab too, same states _after_stop() sets.
        self.main_window.run_tab.force_stopped_state()
        self.refresh_channels_tree()
        self.main_window.enqueue_log("Disconnected from Intiface.")

    def _on_rescan_clicked(self):
        self.rescan_btn.setEnabled(False)
        workers.submit(self.main_window.bridge, self.main_window.relay, self.main_window.controller.scan(), self._after_rescan)

    def _after_rescan(self, fut):
        self.rescan_btn.setEnabled(True)
        try:
            fut.result()
        except Exception as e:
            self.main_window.enqueue_log(f"Scan failed: {e}")
        self.refresh_channels_tree()

    # --------------------------------------------------------------- channels
    def refresh_channels_tree(self):
        """Rebuild the channel list from controller.channels - call after anything that changes it."""
        self.tree.clear()
        for nickname, channel in sorted(self.main_window.controller.channels.items()):
            item = QTreeWidgetItem([nickname, channel.device_name, channel.description or "-", channel.output_type.value])
            self.tree.addTopLevelItem(item)
        # The Test tab's per-channel controls mirror this list 1:1, so any
        # time the channel set changes (connect/rescan/rename) they do too.
        self.main_window.test_tab.refresh_test_channels()

    def _on_rename_channel(self):
        """
        Prompts for a new nickname for the selected channel, updates its
        entry in devices.json (matched by device_name+feature_index+
        output_type, not by the old nickname, so this works even if
        devices.json's copy is already out of sync), renames the live
        DeviceChannel in memory, and warns - without blocking - if any
        saved profile binding still references the old nickname.
        """
        selected = self.tree.selectedItems()
        if not selected:
            QMessageBox.information(self, "Rename", "Select a channel first.")
            return
        old_nickname = selected[0].text(0)
        new_nickname, ok = QInputDialog.getText(self, "Rename channel", f"New nickname for '{old_nickname}':", text=old_nickname)
        if not ok or not new_nickname:
            return
        new_nickname = new_nickname.strip().lower()
        controller = self.main_window.controller
        if not new_nickname or new_nickname == old_nickname:
            return
        if new_nickname in controller.channels:
            QMessageBox.critical(self, "Rename", f"'{new_nickname}' is already in use.")
            return

        channel = controller.channels[old_nickname]
        registry = load_device_registry()
        matched = False
        for entry in registry:
            if (
                entry["device_name"] == channel.device_name
                and entry["feature_index"] == channel.feature.index
                and entry["output_type"] == channel.output_type.value
            ):
                entry["nickname"] = new_nickname
                matched = True
                break
        if not matched:
            registry.append({
                "device_name": channel.device_name,
                "feature_index": channel.feature.index,
                "output_type": channel.output_type.value,
                "description": channel.description,
                "nickname": new_nickname,
            })
        save_device_registry(registry)

        stale_references = self._find_nickname_references(old_nickname)
        del controller.channels[old_nickname]
        channel.nickname = new_nickname
        controller.channels[new_nickname] = channel
        self.refresh_channels_tree()
        self.main_window.enqueue_log(f"Renamed channel '{old_nickname}' -> '{new_nickname}'.")

        if stale_references:
            listed = "\n".join(stale_references)
            QMessageBox.warning(
                self, "Rename",
                f"Renamed to '{new_nickname}'.\n\nThese saved bindings still reference the old nickname "
                f"'{old_nickname}' and won't target this channel until you update them:\n\n{listed}",
            )

    def _find_nickname_references(self, nickname: str) -> list[str]:
        """Return ["Profile Name: binding_id", ...] for every currently-loaded binding whose devices list includes `nickname`."""
        references = []
        for profile in self.main_window.controller.profiles.values():
            for binding in profile.bindings:
                devices = binding["devices"]
                if devices is not None and nickname in devices:
                    references.append(f"{profile.name}: {binding['id']}")
        return references
