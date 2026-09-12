"""Run tab: Start/Stop the haptics engine, a live per-channel status
readout, and the log pane every log call (from the controller, and the
GUI itself) feeds.
"""
from __future__ import annotations

import re
from html import escape

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.gui import theme, workers

_MONOSPACE = "Consolas, 'Courier New', monospace"

# Matches runtime activation lines: [binding_id]: activated (key) [40-65%]
_LOG_ACTIVATE_RE = re.compile(r"^(\[[^\]]+\])(: activated )(\([^)]+\))( \[[^\]]+\])$")


def _classify_log_line(text: str) -> str:
    """Map one log line to a tag name from theme.LOG_TAG_COLORS. Matches
    the patterns produced by engine.print_banner() and the runtime log
    calls in HapticsController and the GUI itself."""
    m = text.strip()
    if m.startswith("[") and "(window match:" in m:
        return "log_profile"
    if m.startswith("  - ") and "-> " in m and "disabled" not in m:
        return "log_binding"
    if m.startswith("  - ") and "disabled" in m:
        return "log_disabled"
    if m.startswith("- ") and "-> " in m:
        return "log_status"
    if m.startswith(("Global config:", "Profiles dir:", "Devices file:")):
        return "log_path"
    if m.startswith("Channels ("):
        return "log_channels"
    if "active -" in m and "TIGHC" in m:
        return "log_header"
    lm = m.lower()
    if "stay idle" in lm or ("no " in lm and ("channel" in lm or "profile" in lm)):
        return "log_warning"
    if "panic" in lm:
        return "log_panic"
    if any(w in lm for w in ("error", "failed", "fail", "could not", "exception")):
        return "log_error"
    if any(w in lm for w in ("connected", "scanning", "disconnected", "reconnect", "device")):
        return "log_device"
    if any(w in lm for w in ("saved", "downloaded", "restored", "created", "reset")):
        return "log_success"
    if _LOG_ACTIVATE_RE.match(m):
        return "log_activate"
    return "log_default"


def render_log_line_html(message: str) -> str:
    """Render one log line as color-coded HTML for the log widget.
    Activation events get inline span coloring; everything else gets a
    single whole-line tag from _classify_log_line()."""

    def span(tag: str, text: str) -> str:
        color = theme.LOG_TAG_COLORS[tag][0]
        bold = "font-weight:bold;" if tag in ("log_header", "log_profile", "log_panic") else ""
        return f'<span style="color:{color};{bold}">{escape(text)}</span>'

    m = message.strip()
    am = _LOG_ACTIVATE_RE.match(m)
    if am:
        return (
            span("log_span_id", am.group(1))
            + span("log_span_verb", am.group(2))
            + span("log_span_key", am.group(3))
            + span("log_span_range", am.group(4))
        )
    return span(_classify_log_line(m), message)


class RunTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._engine_running = False

        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.setProperty("accent", "true")
        self.start_btn.clicked.connect(self._on_start)
        btn_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)
        btn_row.addWidget(self.stop_btn)

        self.status_label = QLabel("Stopped")
        self.status_label.setStyleSheet("font-weight: bold;")
        btn_row.addWidget(self.status_label)

        btn_row.addSpacing(20)
        btn_row.addWidget(QLabel("Override profile:"))
        self.override_combo = QComboBox()
        self.override_combo.currentIndexChanged.connect(self._on_override_changed)
        btn_row.addWidget(self.override_combo)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        levels_group = QGroupBox("Live status")
        levels_layout = QVBoxLayout(levels_group)
        self.levels_label = QLabel("(not connected)")
        self.levels_label.setStyleSheet(f"font-family: {_MONOSPACE};")
        self.levels_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        levels_layout.addWidget(self.levels_label)
        layout.addWidget(levels_group)

        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(
            f"background: {theme.LOG_TERMINAL['bg']}; color: {theme.LOG_TERMINAL['fg']}; "
            f"font-family: {_MONOSPACE};"
        )
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group, stretch=1)

        self._refresh_override_choices()

        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._poll_status)
        self._status_timer.start(400)

    # --------------------------------------------------------------- log
    def append_log_line(self, message: str):
        """Classify/color-code one log line and append it to the log widget, scrolling to the bottom."""
        self.log_text.append(render_log_line_html(message))
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    # ----------------------------------------------------------- override
    def _refresh_override_choices(self):
        controller = self.main_window.controller
        self.override_combo.blockSignals(True)
        self.override_combo.clear()
        self.override_combo.addItem("Auto (follow focus)")
        for profile in sorted(controller.profiles.values(), key=lambda p: p.name.lower()):
            self.override_combo.addItem(profile.name)
        self.override_combo.blockSignals(False)

    def _on_override_changed(self, _index: int):
        controller = self.main_window.controller
        selected = self.override_combo.currentText()
        if not selected or selected == "Auto (follow focus)":
            controller.run_profile_override = None
            self.main_window.enqueue_log("Profile override cleared - following focused window.")
        else:
            profile = next((p for p in controller.profiles.values() if p.name == selected), None)
            if profile:
                controller.run_profile_override = profile
                self.main_window.enqueue_log(f"Profile override set to '{profile.name}'.")

    # --------------------------------------------------------------- start/stop
    def _on_start(self):
        """
        Connects first if this is the very first Start (no client yet) -
        so clicking Start alone is enough without needing to visit the
        Devices tab first - then calls controller.start_engine(), which is
        what actually spins up background_loop() and the pynput listeners.
        """
        controller = self.main_window.controller
        self.start_btn.setEnabled(False)
        if not controller.client:
            self.main_window.set_connection_status(f"Connecting to {controller.ws_url} ...")

        async def _start():
            if not controller.client:
                if not await controller.connect():
                    return False
            controller.start_engine()
            return True

        workers.submit(self.main_window.bridge, self.main_window.relay, _start(), self._after_start)

    def _after_start(self, fut):
        controller = self.main_window.controller
        try:
            ok = fut.result()
        except Exception as e:
            ok = False
            self.main_window.enqueue_log(f"Start failed: {e}")
        self.main_window.devices_tab.refresh_channels_tree()
        is_connected = bool(controller.client)
        self.main_window.devices_tab.set_connected(is_connected)
        if ok:
            self._engine_running = True
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Running")
        else:
            self.start_btn.setEnabled(True)

    def _on_stop(self):
        self.stop_btn.setEnabled(False)
        workers.submit(self.main_window.bridge, self.main_window.relay, self.main_window.controller.stop_engine(), self._after_stop)

    def _after_stop(self, fut):
        try:
            fut.result()
        except Exception as e:
            self.main_window.enqueue_log(f"Stop error: {e}")
        self._engine_running = False
        self.start_btn.setEnabled(True)
        self.status_label.setText("Stopped")

    def force_stopped_state(self):
        """Called by other tabs (e.g. Devices' Disconnect) when the engine stops as a side effect."""
        self._engine_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Stopped")

    # --------------------------------------------------------------- polling
    def _poll_status(self):
        """
        Runs every 400ms: refreshes the "Live status" label with the
        current active profile and every channel's last-sent level, and
        the top bar's connection indicator. Also detects if the engine
        stopped itself (e.g. panic key in "stop" mode) without the user
        clicking Stop.
        """
        controller = self.main_window.controller
        if self._engine_running and not controller.running:
            self.force_stopped_state()

        is_connected = bool(controller.client)
        if controller.channels:
            active = controller.active_profile.name if controller.active_profile else "(none - idle)"
            lines = [f"Active profile: {active}"]
            for nickname, channel in sorted(controller.channels.items()):
                lines.append(f"  {nickname}: {channel.last_level * 100:.0f}%")
            self.levels_label.setText("\n".join(lines))
            self.main_window.set_connection_status(f"Connected - {len(controller.channels)} channel(s)", connected=True)
        else:
            self.levels_label.setText("(not connected)")
            self.main_window.set_connection_status(
                "Connected - no devices found" if is_connected else "Not connected", connected=is_connected
            )
