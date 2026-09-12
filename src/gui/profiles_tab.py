"""Profiles tab: create/edit/save game profiles, their bindings, and
cover art. STUB - full port in progress.
"""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ProfilesTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Profiles tab - port in progress."))

    def refresh_profile_list(self):
        pass

    def refresh_profile_artwork(self, force_refresh: bool = False):
        pass
