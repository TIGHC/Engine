# PyInstaller spec for cli.py -> a single "TIGHC-CLI" (or "TIGHC-CLI.exe")
# console executable.
#
# Build locally with (from the repo root - paths below are relative to it):
#   pyinstaller tighc-cli.spec
#
# See tighc-gui.spec for why VERSION.md/CHANGELOG.md/assets are bundled as
# datas and why the pynput backend is listed explicitly per-platform.
# cli.py itself only reads VERSION.md (via src/version.py) and doesn't
# touch CHANGELOG.md/assets/, but they're included anyway so both
# executables have an identical, predictable bundle layout.

import sys

block_cipher = None

if sys.platform == "win32":
    _pynput_hidden = ["pynput.keyboard._win32", "pynput.mouse._win32"]
elif sys.platform == "darwin":
    _pynput_hidden = ["pynput.keyboard._darwin", "pynput.mouse._darwin"]
else:
    _pynput_hidden = ["pynput.keyboard._xorg", "pynput.mouse._xorg"]

a = Analysis(
    ["cli.py"],
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
    name="TIGHC-CLI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon="assets/icon.ico" if sys.platform == "win32" else None,
)
