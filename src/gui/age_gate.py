"""Blocking 18+ acknowledgment shown before the main window - self-
attestation, not real ID verification. Mirrors the sibling TS4RLS/TWRAR
projects' disclaimer dialog: centered logo, bold title, body, terms link,
then buttons.
"""
from __future__ import annotations

import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from src import paths
from src.tighc import WEBSITE_URL


class AgeGateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Before you continue")
        self.setModal(True)
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        logo_path = paths.APP_ROOT / "assets" / "logo.png"
        if logo_path.is_file():
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                logo_label = QLabel()
                logo_label.setPixmap(pixmap.scaledToHeight(64, Qt.SmoothTransformation))
                logo_label.setAlignment(Qt.AlignHCenter)
                layout.addWidget(logo_label)

        title = QLabel("Before you continue")
        title.setStyleSheet("font-size: 12pt; font-weight: bold;")
        title.setAlignment(Qt.AlignHCenter)
        layout.addWidget(title)

        body = QLabel(
            "This software connects to and controls adult haptic/sex toy devices\n"
            "based on your keyboard and mouse input while gaming.\n\n"
            "It is intended for use only by adults aged 18 or older."
        )
        body.setAlignment(Qt.AlignHCenter)
        layout.addWidget(body)

        terms_url = WEBSITE_URL + "/legal/terms"
        terms = QLabel(
            f'By continuing, you agree to the '
            f'<a href="{terms_url}" style="color:inherit;">Terms and Ethics of Use</a>.'
        )
        terms.setAlignment(Qt.AlignHCenter)
        terms.setTextFormat(Qt.RichText)
        terms.setOpenExternalLinks(False)
        terms.linkActivated.connect(lambda _url: webbrowser.open(terms_url))
        layout.addWidget(terms)

        buttons = QDialogButtonBox()
        continue_btn = buttons.addButton("I am 18 or older - Continue", QDialogButtonBox.AcceptRole)
        continue_btn.setProperty("accent", "true")
        buttons.addButton("Exit", QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
