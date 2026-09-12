"""Test tab: live per-channel and per-binding testing without needing
the actual game running. STUB - full port in progress.
"""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class TestTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Test tab - port in progress."))

    def refresh_test_channels(self):
        pass

    def refresh_test_artwork(self, force_refresh: bool = False):
        pass

    def clear_overrides_on_leave(self):
        pass
