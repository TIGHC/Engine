"""Light/dark theme for the GUI, matching tighc.stuxie.dev's palette (same
tokens as style.css's :root/[data-theme] blocks, translated from CSS custom
properties to QSS).

Keeps a manual toggle (see main_window.py's theme button) rather than
following the OS color scheme -- matches the old Tk/sv_ttk build's
behavior, where every launch started at DEFAULT_THEME regardless of the
system setting.
"""
from __future__ import annotations

from src import paths

DEFAULT_THEME = "dark"

# QSS's url() needs forward slashes even on Windows -- backslashes get
# parsed as escape characters and silently break the rule.
_CHECK_ICON = str(paths.APP_ROOT / "assets" / "checkbox_check.png").replace("\\", "/")

LIGHT = dict(
    bg="#f7f6fb", bg_alt="#efedf7", panel="#ffffff", border="#ddd9ea",
    text="#201e29", text_dim="#55536a", muted="#86839a",
    accent="#6947e0", accent_hover="#5636c4", accent_contrast="#ffffff",
    code_text="#4a34ad", error="#b3312f",
)

DARK = dict(
    bg="#14141a", bg_alt="#191922", panel="#1e1e29", border="#2b2b38",
    text="#e8e6f0", text_dim="#a5a3b5", muted="#6b6879",
    accent="#7c5cff", accent_hover="#9077ff", accent_contrast="#ffffff",
    code_text="#cfc4ff", error="#d98c8c",
)

_THEMES = {"light": LIGHT, "dark": DARK}

# Always-dark terminal-style log box (Run tab) -- stays dark regardless of
# the active app theme, same as the old Tk build's log_text widget.
LOG_TERMINAL = {"bg": "#0d0d0d", "fg": "#d4d4d4"}

# Tag color table for the Run tab's log viewer: {tag_name: (dark_color, light_color)}.
# The log is always rendered against LOG_TERMINAL's dark background regardless of
# app theme, so only the dark_color half is actually used -- the light_color is
# kept alongside for reference/parity with the original Tk implementation, in case
# a future light-mode terminal is ever wanted.
LOG_TAG_COLORS = {
    "log_span_id":      ("#dcdcaa", "#af7d00"),
    "log_span_verb":    ("#4ec9b0", "#008000"),
    "log_span_key":     ("#9cdcfe", "#0070c1"),
    "log_span_range":   ("#ce9178", "#b46200"),
    "log_header":       ("#569cd6", "#0000cc"),
    "log_profile":      ("#dcdcaa", "#af7d00"),
    "log_binding":      ("#9cdcfe", "#001080"),
    "log_disabled":     ("#5c6370", "#aaaaaa"),
    "log_status":       ("#808080", "#777777"),
    "log_path":         ("#5c6370", "#aaaaaa"),
    "log_channels":     ("#4fc1ff", "#0070c1"),
    "log_warning":      ("#ce9178", "#b46200"),
    "log_activate":     ("#4ec9b0", "#008000"),
    "log_panic":        ("#f44747", "#cc0000"),
    "log_error":        ("#f44747", "#cc0000"),
    "log_device":       ("#4fc1ff", "#0070c1"),
    "log_success":      ("#6a9955", "#008000"),
    "log_default":      ("#d4d4d4", "#1e1e1e"),
}

_QSS_TEMPLATE = """
QWidget {{
    background-color: {bg};
    color: {text};
    selection-background-color: {accent};
    selection-color: {accent_contrast};
    font-size: 9pt;
}}
QMainWindow, QDialog {{
    background-color: {bg};
}}
QTabWidget::pane {{
    border: 1px solid {border};
    background: {bg};
    top: -1px;
}}
QTabBar::tab {{
    background: {bg_alt};
    color: {text_dim};
    padding: 6px 16px;
    border: 1px solid {border};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}
QTabBar::tab:selected {{
    background: {bg};
    color: {text};
    border: 1px solid {accent};
    border-bottom: none;
}}
QTabBar::tab:hover:!selected {{
    color: {text};
}}
QPushButton {{
    background: {panel};
    color: {text};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    /* Redeclare the full "border" shorthand, not just border-color -- a
       pseudo-state rule overriding only one sub-property of a shorthand
       set in the base rule doesn't reliably apply in Qt's QSS engine. */
    border: 1px solid {accent};
}}
QPushButton:pressed {{
    background: {bg_alt};
    border: 1px solid {accent};
}}
QPushButton:disabled {{
    color: {muted};
    border: 1px solid {border};
    background: {bg_alt};
}}
QPushButton[accent="true"] {{
    background: {accent};
    color: {accent_contrast};
    border: 1px solid {accent};
    font-weight: bold;
}}
QPushButton[accent="true"]:hover {{
    background: {accent_hover};
    border: 1px solid {accent_hover};
}}
QPushButton[accent="true"]:disabled {{
    background: {bg_alt};
    color: {muted};
    border: 1px solid {border};
}}
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
    background: {panel};
    color: {text};
    border: 1px solid {border};
    border-radius: 4px;
    padding: 3px 5px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {accent};
}}
QComboBox {{
    background: {panel};
    color: {text};
    border: 1px solid {border};
    border-radius: 4px;
    padding: 3px 5px;
}}
QComboBox:focus {{
    border: 1px solid {accent};
}}
QCheckBox {{
    color: {text};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 17px;
    height: 17px;
    border: 1px solid {border};
    border-radius: 3px;
    background: {panel};
}}
QCheckBox::indicator:checked {{
    background: {accent};
    border: 1px solid {accent};
    image: url({check_icon});
}}
QCheckBox::indicator:hover {{
    border: 1px solid {accent};
}}
QGroupBox {{
    border: 1px solid {border};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: bold;
}}
QGroupBox::title {{
    color: {text};
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}}
QScrollArea {{
    border: none;
    background: {bg};
}}
QScrollArea > QWidget > QWidget {{
    background: {bg};
}}
QScrollBar:vertical {{
    background: {bg_alt};
    width: 13px;
    border-radius: 6px;
}}
QScrollBar:horizontal {{
    background: {bg_alt};
    height: 13px;
    border-radius: 6px;
}}
QScrollBar::handle {{
    background: {border};
    border-radius: 5px;
    min-height: 24px;
    min-width: 24px;
}}
QScrollBar::handle:hover {{
    background: {muted};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
    width: 0;
}}
QScrollBar::add-page, QScrollBar::sub-page {{
    background: none;
}}
QTreeWidget, QTableWidget {{
    background: {panel};
    color: {text};
    border: 1px solid {border};
    border-radius: 4px;
    alternate-background-color: {bg_alt};
}}
QHeaderView::section {{
    background: {bg_alt};
    color: {text_dim};
    border: none;
    border-bottom: 1px solid {border};
    padding: 4px 6px;
    font-weight: bold;
}}
QTreeWidget::item:selected, QTableWidget::item:selected {{
    background: {accent};
    color: {accent_contrast};
}}
QSlider::groove:horizontal {{
    border: 1px solid {border};
    height: 6px;
    background: {bg_alt};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {accent};
    border: 1px solid {accent};
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{
    background: {accent_hover};
    border: 1px solid {accent_hover};
}}
QSlider::sub-page:horizontal {{
    background: {accent};
    border-radius: 3px;
}}
QLabel[hint="true"] {{
    color: {text_dim};
}}
QLabel[error="true"] {{
    color: {error};
}}
QLabel[link="true"] {{
    color: {accent};
}}
QMessageBox QLabel {{
    color: {text};
}}
"""


def tokens(theme_name: str) -> dict[str, str]:
    return _THEMES.get(theme_name, DARK)


def stylesheet(theme_name: str) -> str:
    return _QSS_TEMPLATE.format(check_icon=_CHECK_ICON, **tokens(theme_name))


def accent_color(theme_name: str) -> str:
    return tokens(theme_name)["accent"]


def text_dim_color(theme_name: str) -> str:
    return tokens(theme_name)["text_dim"]


def code_text_color(theme_name: str) -> str:
    return tokens(theme_name)["code_text"]
