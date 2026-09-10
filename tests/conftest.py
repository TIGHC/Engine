"""pytest configuration: isolate every test run from the developer's real
per-user TIGHC data directory (%APPDATA%\\TIGHC or ~/.local/share/TIGHC).

src/paths.py reads APPDATA/XDG_DATA_HOME at *import* time, and importing
src.profiles or src.haptics (transitively pulled in by nearly everything,
including src.tighc) has import-time side effects of its own: creating
config directories, writing haptics.json's defaults, and - if the profiles
dir looks empty - reaching out to the TIGHC-Profiles GitHub repo. None of
that should ever touch the real user's install or the network just because
`pytest` ran, so this file redirects APPDATA/XDG_DATA_HOME to a throwaway
temp directory, and pre-seeds one dummy profile so the "first launch"
GitHub-download path never triggers - all before pytest imports a single
test module or the `src` package, since conftest.py is always collected
(and therefore imported) first.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

_TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="tighc-pytest-"))
os.environ["APPDATA"] = str(_TEST_DATA_DIR)
os.environ["XDG_DATA_HOME"] = str(_TEST_DATA_DIR)
# macOS ignores XDG_DATA_HOME (it uses ~/Library/Application Support instead
# - see src/paths.py), so also redirect HOME: Path.home() reads it on every
# POSIX platform, which keeps this isolated even when run on a real Mac.
os.environ["HOME"] = str(_TEST_DATA_DIR)

_user_data_dir = (
    _TEST_DATA_DIR / "Library" / "Application Support" / "TIGHC"
    if sys.platform == "darwin"
    else _TEST_DATA_DIR / "TIGHC"
)
_seed_profile_dir = _user_data_dir / "profiles" / "minecraft"
_seed_profile_dir.mkdir(parents=True, exist_ok=True)
(_seed_profile_dir / "profile.json").write_text(
    json.dumps(
        {
            "name": "Minecraft",
            "window_titles": ["minecraft"],
            "bindings": [
                {"id": "attack", "keys": ["mouse_left"], "enabled": True, "devices": ["all"], "vibe": [0.5, 0.8]},
            ],
        }
    ),
    encoding="utf-8",
)
