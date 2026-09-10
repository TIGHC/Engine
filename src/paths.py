"""Filesystem layout for TIGHC's per-install runtime state.

Split out on its own so every other module (haptics, devices,
profiles, steamgriddb) can depend on these paths without pulling in
anything heavier - keeps the dependency graph a simple fan-out from here
rather than everything routing through one large module.

User data (configs, profiles, artwork cache) lives in the platform-standard
per-user app directory so it survives git updates and submodule updates:
  Windows: %APPDATA%\\TIGHC\\
  macOS:   ~/Library/Application Support/TIGHC/
  Linux:   ~/.local/share/TIGHC/

On first launch (empty user profiles dir), profiles.py fetches all profiles
from the TIGHC-Profiles GitHub repo and seeds them into the user profiles dir.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Base directory for read-only, ship-with-the-app resources (VERSION.md,
# CHANGELOG.md, assets/) - as opposed to USER_DATA_DIR below, which is
# read/write per-user state. Running from source, this is the repo root;
# frozen into a PyInstaller executable, `__file__`-relative lookups no
# longer point at real files (everything's packed into the bundle), so this
# falls back to `sys._MEIPASS`, the temp/onedir path PyInstaller extracts
# `--add-data` resources into. Both cases are set up so the same relative
# layout (VERSION.md, CHANGELOG.md, assets/ at the root) resolves correctly.
APP_ROOT = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else REPO_ROOT

# Platform-standard per-user app directory.
if os.name == "nt":
    _base = Path(os.environ.get("APPDATA", Path.home()))
elif sys.platform == "darwin":
    _base = Path.home() / "Library" / "Application Support"
else:
    _base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

USER_DATA_DIR = _base / "TIGHC"

# Per-install runtime config/state (haptics.json, devices.json, ...)
CONFIGS_DIR = USER_DATA_DIR / "configs"
CONFIGS_DIR.mkdir(parents=True, exist_ok=True)

# User's working copy of game profiles - seeded from BUNDLED_PROFILES_DIR on
# first run, then fully owned by the user (GUI reads/writes here).
PROFILES_DIR = USER_DATA_DIR / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

# Downloaded cover-art images.
ARTWORK_CACHE_DIR = USER_DATA_DIR / "artwork_cache"


if __name__ == "__main__":
    print(f"{__file__} is TIGHC's filesystem-layout module - it's a library, not meant to be run directly.")
    print("Run `python gui.py` (from the repo root) for the interactive GUI.")
