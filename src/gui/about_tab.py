"""About tab: logo banner, project blurb, age notice, version/update
check, links, and the changelog viewer.
"""
from __future__ import annotations

import re
import webbrowser
from html import escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src import paths
from src.gui import theme, workers
from src.tighc import (
    AUTHOR_NAME,
    AUTHOR_URL,
    PROJECT_NAME,
    PROJECT_SHORT_NAME,
    PROJECTS_URL,
    REPO_URL,
    WEBSITE_URL,
    __version__,
    check_for_update,
)

CHANGELOG_PATH = paths.APP_ROOT / "CHANGELOG.md"


def _render_changelog_html(md_text: str, theme_name: str) -> str:
    """Convert CHANGELOG.md's markdown (##/###/- /**bold**/`code`) to HTML, colored to match the active theme."""
    accent = theme.accent_color(theme_name)
    text_dim = theme.text_dim_color(theme_name)
    code_text = theme.code_text_color(theme_name)

    def inline(text: str) -> str:
        text = escape(text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"`([^`]+)`", f'<code style="color:{code_text};">\\1</code>', text)
        return text

    parts: list[str] = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            parts.append("</ul>")
            in_list = False

    for line in md_text.splitlines():
        if line.startswith("## "):
            close_list()
            parts.append(f'<h2 style="color:{accent};">{escape(line[3:].strip())}</h2>')
        elif line.startswith("### "):
            close_list()
            parts.append(f'<h3 style="color:{text_dim};">{escape(line[4:].strip())}</h3>')
        elif line.startswith("- ") or line.startswith("  - "):
            if not in_list:
                parts.append("<ul>")
                in_list = True
            parts.append(f"<li>{inline(line.lstrip('- ').lstrip())}</li>")
        elif line.startswith("# "):
            continue  # skip top-level title - shown as a label above
        elif line.strip():
            close_list()
            parts.append(f'<p style="color:{text_dim};">{inline(line.strip())}</p>')
        else:
            close_list()
    close_list()
    return "".join(parts)


def _link_label(html: str) -> QLabel:
    label = QLabel(html)
    label.setTextFormat(Qt.RichText)
    label.setOpenExternalLinks(True)
    return label


class AboutTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        logo_path = paths.APP_ROOT / "assets" / "logo.png"
        if logo_path.is_file():
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                logo_label = QLabel()
                logo_label.setPixmap(pixmap.scaledToHeight(64, Qt.SmoothTransformation))
                outer.addWidget(logo_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll, stretch=1)

        body = QWidget()
        scroll.setWidget(body)
        layout = QVBoxLayout(body)

        version_row = QHBoxLayout()
        version_label = QLabel(f"{PROJECT_SHORT_NAME} - version {__version__}")
        version_label.setStyleSheet("font-weight: bold;")
        version_row.addWidget(version_label)
        check_btn = QPushButton("Check for updates")
        check_btn.clicked.connect(lambda: self._check_for_updates(manual=True))
        version_row.addWidget(check_btn)
        self.update_status_label = QLabel("")
        self.update_status_label.setProperty("hint", "true")
        version_row.addWidget(self.update_status_label)
        version_row.addStretch(1)
        layout.addLayout(version_row)

        blurb = QLabel(
            "Drives a Buttplug/Intiface haptic device from keyboard/mouse input in any game, "
            "via configurable per-game profiles, per-binding intensity ranges, and per-motor device targeting."
        )
        blurb.setWordWrap(True)
        layout.addWidget(blurb)

        age_notice = QLabel("Intended for use only by adults aged 18 or older.")
        age_notice.setStyleSheet("font-weight: bold;")
        layout.addWidget(age_notice)

        terms_url = WEBSITE_URL + "/legal/terms"
        layout.addWidget(_link_label(
            f'By using this software, you agree to the <a href="{terms_url}">Terms and Ethics of Use</a>.'
        ))

        versioning = QLabel("Versioning: Semantic Versioning (semver.org) - MAJOR.MINOR.PATCH.")
        versioning.setProperty("hint", "true")
        layout.addWidget(versioning)

        layout.addWidget(_link_label(f'Website: <a href="{WEBSITE_URL}">{WEBSITE_URL}</a>'))
        profiles_url = WEBSITE_URL + "/profiles"
        layout.addWidget(_link_label(f'Profiles: <a href="{profiles_url}">{profiles_url}</a>'))
        layout.addWidget(_link_label(f'Repository: <a href="{REPO_URL}">{REPO_URL}</a>'))

        author_row = QHBoxLayout()
        author_row.addWidget(QLabel("Written & Maintained by"))
        avatar_path = paths.APP_ROOT / "assets" / "author.png"
        if avatar_path.is_file():
            pixmap = QPixmap(str(avatar_path))
            if not pixmap.isNull():
                avatar_label = QLabel()
                avatar_label.setPixmap(pixmap.scaledToHeight(20, Qt.SmoothTransformation))
                author_row.addWidget(avatar_label)
        author_row.addWidget(_link_label(f'<a href="{AUTHOR_URL}">{AUTHOR_NAME}</a>'))
        author_row.addStretch(1)
        layout.addLayout(author_row)

        project_link = _link_label(f'<a href="{PROJECTS_URL}" style="color:inherit;">A StuxieDev Project</a>')
        project_link.setProperty("hint", "true")
        layout.addWidget(project_link)

        changelog_header = QHBoxLayout()
        changelog_title = QLabel("Changelog")
        changelog_title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        changelog_header.addWidget(changelog_title)
        changelog_header.addStretch(1)
        changelogs_url = WEBSITE_URL + "/changelogs"
        changelog_header.addWidget(_link_label(f'<a href="{changelogs_url}">View on website</a>'))
        reload_btn = QPushButton("Reload")
        reload_btn.clicked.connect(self.load_changelog)
        changelog_header.addWidget(reload_btn)
        layout.addLayout(changelog_header)

        self.changelog_view = QTextEdit()
        self.changelog_view.setReadOnly(True)
        self.changelog_view.setMinimumHeight(320)
        layout.addWidget(self.changelog_view)

        self.load_changelog()

    def load_changelog(self):
        """(Re)load CHANGELOG.md into the changelog viewer. Wired to the "Reload" button too."""
        try:
            text = CHANGELOG_PATH.read_text(encoding="utf-8")
        except OSError as e:
            self.changelog_view.setPlainText(f"(Could not read {CHANGELOG_PATH.name}: {e})")
            return
        html = _render_changelog_html(text, self.main_window.theme)
        self.changelog_view.setHtml(html)

    def refresh_theme(self):
        """Called by MainWindow after a theme toggle - the changelog's inline colors are baked into its HTML."""
        self.load_changelog()

    def _check_for_updates(self, manual: bool = False):
        """
        Check GitHub for a newer TIGHC release in the background. Called
        once at startup (manual=False): silent unless an update is
        actually found. Also wired to this tab's "Check for updates"
        button (manual=True), which always reports a result.
        """
        if manual:
            self.update_status_label.setText("Checking...")
        workers.run_in_thread(self.main_window.relay, check_for_update, lambda result: self._on_update_checked(result, manual))

    def _on_update_checked(self, result, manual: bool):
        if result:
            self.main_window.show_update_link(result["version"], result["url"])
            if manual:
                self.update_status_label.setText("")
        elif manual:
            self.update_status_label.setText(f"You're on the latest version (v{__version__}).")
