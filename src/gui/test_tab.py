"""Test tab: two independent ways to check things work without needing
the actual game running - drive a channel directly (bypassing
profiles/keybinds entirely), or simulate a profile's keybinds being
pressed (exercising the same code path real input does, via
HapticsController.test_pulse() and a "pinned" active profile).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.ranges import VibeRange


class TestTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._test_channel_widgets: dict[str, dict] = {}  # nickname -> {"slider", "hold_check", "pct_label"}

        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Profile to test:"))
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        top.addWidget(self.profile_combo)
        self.pin_check = QCheckBox("Pin as active profile (ignores the real focused window)")
        self.pin_check.toggled.connect(self._on_toggle_pin)
        top.addWidget(self.pin_check)
        top.addStretch(1)
        stop_btn = QPushButton("Stop all testing")
        stop_btn.clicked.connect(self._on_stop_all_test)
        top.addWidget(stop_btn)
        layout.addLayout(top)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, stretch=1)

        channels_group = QGroupBox("Manual channel control")
        channels_layout = QVBoxLayout(channels_group)
        channels_hint = QLabel("Drives a channel directly, no profile needed.")
        channels_hint.setProperty("hint", "true")
        channels_layout.addWidget(channels_hint)
        self._channels_scroll = QScrollArea()
        self._channels_scroll.setWidgetResizable(True)
        channels_layout.addWidget(self._channels_scroll)
        splitter.addWidget(channels_group)

        bindings_group = QGroupBox("Simulate keybinds")
        bindings_layout = QVBoxLayout(bindings_group)
        bindings_hint = QLabel('"Hold" needs the engine Started (Run tab) and this profile pinned above to take effect.')
        bindings_hint.setProperty("hint", "true")
        bindings_hint.setWordWrap(True)
        bindings_layout.addWidget(bindings_hint)
        self._bindings_scroll = QScrollArea()
        self._bindings_scroll.setWidgetResizable(True)
        bindings_layout.addWidget(self._bindings_scroll)
        splitter.addWidget(bindings_group)

        self.refresh_test_channels()
        self.refresh_test_bindings()

    # ------------------------------------------------------------ profile picker
    def set_profile_choices(self, display_names: list[str]):
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(display_names)
        self.profile_combo.blockSignals(False)

    def ensure_valid_selection(self, ids: list[str], fallback_display_name: str):
        profiles_tab = self.main_window.profiles_tab
        if profiles_tab._profile_id_for_display(self.profile_combo.currentText()) not in ids:
            self.profile_combo.setCurrentText(fallback_display_name)

    def _on_profile_changed(self, _index: int):
        self.refresh_test_bindings()

    # --------------------------------------------------------------- channels
    def refresh_test_channels(self):
        """
        Rebuild the manual-control panel with one row per connected
        channel (slider + %, Hold checkbox, Pulse button), tearing down and
        recreating every widget rather than diffing.
        """
        controller = self.main_window.controller
        self._test_channel_widgets = {}

        body = QWidget()
        body_layout = QVBoxLayout(body)
        if not controller.channels:
            body_layout.addWidget(QLabel("(no channels - connect on the Devices tab)"))
        else:
            for nickname, _channel in sorted(controller.channels.items()):
                row = QHBoxLayout()
                name_label = QLabel(nickname)
                name_label.setFixedWidth(140)
                row.addWidget(name_label)

                slider = QSlider(Qt.Horizontal)
                slider.setRange(0, 100)
                slider.setFixedWidth(130)
                row.addWidget(slider)
                pct_label = QLabel("0%")
                pct_label.setFixedWidth(40)
                row.addWidget(pct_label)
                hold_check = QCheckBox("Hold")
                row.addWidget(hold_check)
                pulse_btn = QPushButton("Pulse")
                row.addWidget(pulse_btn)
                row.addStretch(1)

                # Dragging the slider while "Hold" is on updates the live
                # level immediately, so you can feel out an intensity in
                # real time.
                slider.valueChanged.connect(
                    lambda value, n=nickname, hc=hold_check, pl=pct_label: self._on_test_level_changed(n, value, hc, pl)
                )
                hold_check.toggled.connect(
                    lambda checked, n=nickname, s=slider: self._on_toggle_channel_hold(n, s, checked)
                )
                pulse_btn.clicked.connect(lambda _checked=False, n=nickname, s=slider: self._on_test_channel_pulse(n, s))

                row_widget = QWidget()
                row_widget.setLayout(row)
                body_layout.addWidget(row_widget)

                self._test_channel_widgets[nickname] = {"slider": slider, "hold_check": hold_check, "pct_label": pct_label}
        body_layout.addStretch(1)
        self._channels_scroll.setWidget(body)

    def _on_test_level_changed(self, nickname: str, value: int, hold_check: QCheckBox, pct_label: QLabel):
        """Slider handler: update the "N%" label live, and push the new level if this channel is currently held."""
        pct_label.setText(f"{value}%")
        if hold_check.isChecked():
            self.main_window.bridge.submit(self.main_window.controller.set_test_level(nickname, value / 100.0))

    def _on_toggle_channel_hold(self, nickname: str, slider: QSlider, checked: bool):
        """Per-channel "Hold" checkbox handler: engage or release a manual level override at the slider's current position."""
        if checked:
            self.main_window.bridge.submit(self.main_window.controller.set_test_level(nickname, slider.value() / 100.0))
        else:
            self.main_window.bridge.submit(self.main_window.controller.clear_test_level(nickname))

    def _on_test_channel_pulse(self, nickname: str, slider: QSlider):
        """Per-channel "Pulse" button handler: fire a fixed-duration test pulse at the slider's current level, just this one channel."""
        level = slider.value() / 100.0
        vibe = VibeRange(level, level)
        self.main_window.bridge.submit(self.main_window.controller.test_pulse(vibe, 0.6, frozenset({nickname})))

    # --------------------------------------------------------------- bindings
    def refresh_test_bindings(self):
        """Rebuild the "simulate keybinds" panel for whichever profile is selected: a "Trigger (0.5s)" button per enabled binding."""
        profiles_tab = self.main_window.profiles_tab
        profile_id = profiles_tab._profile_id_for_display(self.profile_combo.currentText())
        profile = self.main_window.controller.profiles.get(profile_id)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        if not profile:
            body_layout.addWidget(QLabel("(no profile selected)"))
        else:
            for binding in profile.bindings:
                if not binding["enabled"]:
                    continue
                row = QHBoxLayout()
                id_label = QLabel(binding["id"])
                id_label.setFixedWidth(160)
                row.addWidget(id_label)
                trigger_btn = QPushButton("Trigger (0.5s)")
                trigger_btn.clicked.connect(lambda _checked=False, b=binding: self._on_trigger_binding(b))
                row.addWidget(trigger_btn)
                row.addStretch(1)
                row_widget = QWidget()
                row_widget.setLayout(row)
                body_layout.addWidget(row_widget)
        body_layout.addStretch(1)
        self._bindings_scroll.setWidget(body)

    def _on_trigger_binding(self, binding: dict):
        """Fire exactly the pulse a real press of this binding would, using its own vibe/duration range and devices target."""
        self.main_window.bridge.submit(self.main_window.controller.test_pulse(binding["vibe"], 0.5, binding["devices"]))

    # ------------------------------------------------------------------ pin
    def _on_toggle_pin(self, checked: bool):
        """Set or clear controller.test_profile_override to force (or stop forcing) the selected profile active."""
        controller = self.main_window.controller
        profiles_tab = self.main_window.profiles_tab
        profile = controller.profiles.get(profiles_tab._profile_id_for_display(self.profile_combo.currentText()))
        if checked:
            if not profile:
                QMessageBox.information(self, "Test mode", "Select a profile to pin first.")
                self.pin_check.blockSignals(True)
                self.pin_check.setChecked(False)
                self.pin_check.blockSignals(False)
                return
            controller.test_profile_override = profile
            self.main_window.enqueue_log(f"Pinned '{profile.name}' as the active profile for testing.")
        else:
            controller.test_profile_override = None
            self.main_window.enqueue_log("Unpinned test profile - the active profile now follows the focused window again.")

    def _on_stop_all_test(self):
        """Releases every manual channel hold in one go, for bailing out quickly (does not touch the profile pin)."""
        for nickname, widgets in self._test_channel_widgets.items():
            if widgets["hold_check"].isChecked():
                widgets["hold_check"].setChecked(False)
                self.main_window.bridge.submit(self.main_window.controller.clear_test_level(nickname))
        self.main_window.enqueue_log("Test mode: released all manual holds.")

    def clear_overrides_on_leave(self):
        """Clear all Test tab overrides (pin + holds) whenever the user navigates away from the Test tab."""
        changed = False
        if self.pin_check.isChecked():
            self.pin_check.setChecked(False)  # triggers _on_toggle_pin, which clears test_profile_override
            changed = True
        for nickname, widgets in self._test_channel_widgets.items():
            if widgets["hold_check"].isChecked():
                widgets["hold_check"].setChecked(False)
                self.main_window.bridge.submit(self.main_window.controller.clear_test_level(nickname))
                changed = True
        if changed:
            self.main_window.enqueue_log("Left Test tab - test overrides cleared.")
