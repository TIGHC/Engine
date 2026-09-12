"""The Intiface Game Haptics Controller (TIGHC) - interactive GUI.

Single entry point, built on PySide6/Qt. Connect to Intiface, scan for
devices, assign friendly nicknames to individual motors/capabilities,
build game profiles (keybinds + ranges + which device each keybind
drives), tweak global settings, and start/stop the haptics engine - all
from one window. Everything you do here is written to the same JSON
files src/tighc.py reads (configs/haptics.json, configs/devices.json,
profiles/<id>/profile.json), so hand-editing those files and using this
GUI are fully interchangeable.

Run with: python gui.py

Copyright (C) StuxieDev. Licensed under the GNU General Public License
v3.0 (or later) - see LICENSE.md for the full text and
https://github.com/TIGHC/Engine for source.
"""
import sys

from src import paths
from src.tighc import load_haptics_config, save_age_confirmation

ICON_PATH = paths.APP_ROOT / "assets" / "icon.png"
ICON_ICO_PATH = paths.APP_ROOT / "assets" / "icon.ico"


def main():
    if sys.platform == "win32":
        # Without an explicit AppUserModelID, Windows groups this window's
        # taskbar button under the launching python.exe's own icon instead
        # of the one set below via setWindowIcon() - this is what actually
        # controls the taskbar/Alt-Tab icon, setWindowIcon() alone does not.
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("StuxieDev.TIGHC")
        except OSError:
            pass

    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication, QDialog

    from src.gui import theme
    from src.gui.age_gate import AgeGateDialog
    from src.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    # Applied here, before the age gate (which may run and finish before
    # MainWindow is ever constructed) - MainWindow re-applies its own
    # (possibly toggled) theme later, but the age gate needs this done
    # upfront or it renders with no styling (default OS/Fusion look: no
    # themed borders, no hover states) instead of matching the app.
    app.setStyleSheet(theme.stylesheet(theme.DEFAULT_THEME))
    icon_path = ICON_ICO_PATH if (sys.platform == "win32" and ICON_ICO_PATH.is_file()) else ICON_PATH
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))

    if not load_haptics_config().get("confirmed_age", False):
        if AgeGateDialog().exec() != QDialog.DialogCode.Accepted:
            return
        save_age_confirmation()

    window = MainWindow()
    if icon_path.is_file():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
