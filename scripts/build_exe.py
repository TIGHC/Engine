"""Builds a standalone TIGHC executable with PyInstaller, for whatever
platform this is run on.

Run with: python scripts/build_exe.py
Requires PyInstaller: pip install pyinstaller (build.sh/build.bat do this
for you - see requirements.txt for the app's own runtime dependencies).

PyInstaller can't cross-compile - run this on each platform (Windows,
Linux, macOS) you want a native build for; that's also what the CI "build"
job does, once per OS runner (see .github/workflows/ci.yml).

Drives PyInstaller via its argument API rather than a hand-maintained
.spec file, same as the sibling TWRAR/TS4RLS projects - --specpath below
still makes PyInstaller write one, just into the gitignored build/ dir as
a byproduct, not a file this repo tracks.
"""
from __future__ import annotations

import sys
from pathlib import Path

import PyInstaller.__main__

IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION = (REPO_ROOT / "VERSION.md").read_text(encoding="utf-8").strip()
DIST_DIR = REPO_ROOT / "dist"
BUILD_DIR = REPO_ROOT / "build"

_DATA_SEP = ";" if IS_WINDOWS else ":"


def _add_data(src: Path, dest: str) -> str:
    return f"--add-data={src}{_DATA_SEP}{dest}"


def _icon_args() -> list[str]:
    # PyInstaller doesn't support icon embedding for plain Linux/ELF
    # binaries, so a Linux build just goes without one.
    if IS_WINDOWS:
        icon = REPO_ROOT / "assets" / "icon.ico"
    elif IS_MACOS:
        icon = REPO_ROOT / "assets" / "icon.icns"
    else:
        return []
    return [f"--icon={icon}"] if icon.is_file() else []


def _pynput_hidden_import_args() -> list[str]:
    # pynput picks its keyboard/mouse backend per-platform at import time,
    # which PyInstaller's static analysis doesn't always follow correctly -
    # so the actual backend module for the platform this runs on is listed
    # explicitly rather than left to autodetection.
    if IS_WINDOWS:
        backend = "win32"
    elif sys.platform == "darwin":
        backend = "darwin"
    else:
        backend = "xorg"
    return [
        f"--hidden-import=pynput.keyboard._{backend}",
        f"--hidden-import=pynput.mouse._{backend}",
    ]


COMMON_ARGS = [
    "--onefile",
    "--noconfirm",
    f"--distpath={DIST_DIR}",
    f"--workpath={BUILD_DIR}",
    f"--specpath={BUILD_DIR}",
    f"--paths={REPO_ROOT}",
]


def build_gui() -> None:
    # The About tab and age-gate read assets/logo.png (and icon.png/.ico/
    # .icns), CHANGELOG.md, and VERSION.md at runtime via src.paths.APP_ROOT (which
    # resolves to sys._MEIPASS in a frozen build) - bundle them as data so
    # those lookups succeed instead of silently no-op'ing (missing icon/
    # logo/blank changelog) in the packaged exe.
    PyInstaller.__main__.run([
        str(REPO_ROOT / "gui.py"),
        "--name=TIGHC",
        "--windowed",
        *_icon_args(),
        *_pynput_hidden_import_args(),
        _add_data(REPO_ROOT / "assets", "assets"),
        _add_data(REPO_ROOT / "VERSION.md", "."),
        _add_data(REPO_ROOT / "CHANGELOG.md", "."),
        *COMMON_ARGS,
    ])


def main() -> None:
    print(f"Building TIGHC v{VERSION} standalone executable for {sys.platform}...")
    build_gui()
    ext = ".exe" if IS_WINDOWS else ""
    print(f"\nDone. Output: {DIST_DIR / ('TIGHC' + ext)}")


if __name__ == "__main__":
    main()
