"""TIGHC's main window: owns the one HapticsController and AsyncBridge
for the app's lifetime, builds the top bar and tab widget, and delegates
each tab's content to its own module.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src import tighc
from src.engine import HapticsController
from src.gui import theme, workers
from src.gui.about_tab import AboutTab
from src.gui.devices_tab import DevicesTab
from src.gui.profiles_tab import ProfilesTab
from src.gui.run_tab import RunTab
from src.gui.settings_tab import SettingsTab
from src.gui.test_tab import TestTab
from src.tighc import PROJECT_NAME, PROJECT_SHORT_NAME, __version__


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.theme = theme.DEFAULT_THEME
        self.setWindowTitle(f"{PROJECT_SHORT_NAME} ({PROJECT_NAME}) — v{__version__}")
        self.resize(1040, 720)
        self.setMinimumSize(860, 600)

        self.bridge = workers.AsyncBridge()
        self.relay = workers.MainThreadRelay(self)
        self.controller = HapticsController(tighc.INTIFACE_WS, dict(tighc.PROFILES), log_fn=self.enqueue_log)

        self._log_ready = False
        self._log_buffer: list[str] = []

        self._build_ui()
        self._log_ready = True
        for message in self._log_buffer:
            self.run_tab.append_log_line(message)
        self._log_buffer.clear()

        # Population order matters: profiles first (so the Test tab's
        # profile picker has something to select), then channels.
        self.profiles_tab.refresh_profile_list()
        self.devices_tab.refresh_channels_tree()
        self.run_tab._refresh_override_choices()

        self.about_tab._check_for_updates(manual=False)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)

        top_bar = QHBoxLayout()
        self.connection_status_label = QLabel("Not connected")
        self.connection_status_label.setProperty("hint", "true")
        top_bar.addWidget(self.connection_status_label)
        top_bar.addStretch(1)
        self.update_link = QLabel("")
        self.update_link.setTextFormat(Qt.RichText)
        self.update_link.setOpenExternalLinks(True)
        self.update_link.hide()
        top_bar.addWidget(self.update_link)
        self.theme_toggle_btn = QPushButton(self._theme_toggle_label())
        self.theme_toggle_btn.clicked.connect(self._on_toggle_theme)
        top_bar.addWidget(self.theme_toggle_btn)
        outer.addLayout(top_bar)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._on_tab_changed)
        outer.addWidget(self.tabs, stretch=1)

        self.devices_tab = DevicesTab(self)
        self.profiles_tab = ProfilesTab(self)
        self.test_tab = TestTab(self)
        self.settings_tab = SettingsTab(self)
        self.run_tab = RunTab(self)
        self.about_tab = AboutTab(self)

        self.tabs.addTab(self.devices_tab, "Devices")
        self.tabs.addTab(self.profiles_tab, "Profiles")
        self.tabs.addTab(self.test_tab, "Test")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.run_tab, "Run")
        self.tabs.addTab(self.about_tab, "About")

    # ------------------------------------------------------------- theme
    def _theme_toggle_label(self) -> str:
        return "Switch to light mode" if self.theme == "dark" else "Switch to dark mode"

    def _on_toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        app = QApplication.instance()
        app.setStyleSheet(theme.stylesheet(self.theme))
        self.theme_toggle_btn.setText(self._theme_toggle_label())
        self.about_tab.refresh_theme()

    # --------------------------------------------------------------- log
    def enqueue_log(self, message: str):
        """
        The `log_fn` passed to HapticsController (and called directly by
        the GUI itself in a few places). Safe to call from any thread -
        controller log calls can originate from the bridge's asyncio
        thread (background_loop, pynput callbacks scheduled onto it) as
        well as the Qt main thread. Marshals to the main thread via
        MainThreadRelay and appends straight to the Run tab's log - no
        polling loop needed, unlike the old Tk build's queue.Queue.
        """
        self.relay.call(self._append_log, str(message))

    def _append_log(self, message: str):
        if self._log_ready:
            self.run_tab.append_log_line(message)
        else:
            # Run tab doesn't exist yet (still inside _build_ui) - buffer
            # until __init__ flushes it right after _build_ui() returns.
            self._log_buffer.append(message)

    # -------------------------------------------------------- connection
    def set_connection_status(self, text: str, connected: bool = False):
        self.connection_status_label.setText(text)
        color = theme.accent_color(self.theme) if connected else theme.text_dim_color(self.theme)
        self.connection_status_label.setStyleSheet(f"color: {color};")

    def show_update_link(self, version: str, url: str):
        self.update_link.setText(f'<a href="{url}">Update available: v{version}</a>')
        self.update_link.show()

    # ----------------------------------------------------------- tabs
    def _on_tab_changed(self, index: int):
        """Clear all Test tab overrides (pin + holds) whenever the user navigates away from the Test tab."""
        if self.tabs.widget(index) is not self.test_tab:
            self.test_tab.clear_overrides_on_leave()

    # ---------------------------------------------------------- shutdown
    def closeEvent(self, event):
        """Stop the engine/disconnect (waiting up to 5s), then let the window close."""
        fut = self.bridge.submit(self.controller.shutdown())
        try:
            fut.result(timeout=5)
        except Exception:
            pass
        self.bridge.stop()
        event.accept()
