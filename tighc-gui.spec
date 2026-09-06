# PyInstaller spec for gui.py -> a single "TIGHC" (or "TIGHC.exe") executable.
#
# Build locally with (from the repo root - paths below are relative to it):
#   pyinstaller tighc-gui.spec
#
# Bundles VERSION.md, CHANGELOG.md, and assets/ at the root of the frozen
# app, so src.paths.APP_ROOT (which becomes sys._MEIPASS once frozen)
# resolves them the same way it resolves the repo root when running from
# source - see src/paths.py and src/version.py.
#
# pynput picks its keyboard/mouse backend per-platform at import time
# (src/paths.py never touches this - it's a pynput implementation detail),
# which PyInstaller's static analysis doesn't always follow correctly, so
# the actual backend module for the platform this spec is run on is listed
# explicitly below rather than left to autodetection.

import sys

block_cipher = None

if sys.platform == "win32":
    _pynput_hidden = ["pynput.keyboard._win32", "pynput.mouse._win32"]
elif sys.platform == "darwin":
    _pynput_hidden = ["pynput.keyboard._darwin", "pynput.mouse._darwin"]
else:
    _pynput_hidden = ["pynput.keyboard._xorg", "pynput.mouse._xorg"]

a = Analysis(
    ["gui.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("VERSION.md", "."),
        ("CHANGELOG.md", "."),
        ("assets", "assets"),
    ],
    hiddenimports=_pynput_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="TIGHC",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon="assets/icon.ico" if sys.platform == "win32" else None,
)
