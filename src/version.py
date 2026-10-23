"""TIGHC's version - single source of truth, read by the engine's startup
banner and gui.py's About tab.

The version number lives in VERSION.md alongside src.paths.APP_ROOT (the
repo root when running from source, or a PyInstaller executable's bundled
resources - see src/paths.py) so it can be read by both Python (here) and
external tools (the website, CI, etc.) without importing the package.
Versioning follows Date Versioning (datevers.ing): the UTC release date as
YY.MM.DD, plus -1, -2... for later releases the same day. Bump VERSION.md
and add a matching entry to CHANGELOG.md together.
"""

import re

from src.paths import APP_ROOT

_DATE_VERSION_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{2})(?:-([1-9]\d*))?$")

__version__ = (APP_ROOT / "VERSION.md").read_text(encoding="utf-8").strip()


def parse_version(text: str) -> "tuple | None":
    """Parse "YY.MM.DD" or "YY.MM.DD-N" into (YY, MM, DD, N), or None if malformed."""
    match = _DATE_VERSION_RE.match(text.strip()) if isinstance(text, str) else None
    if not match:
        return None
    parts = tuple(int(g) if g else 0 for g in match.groups())
    if not (1 <= parts[1] <= 12 and 1 <= parts[2] <= 31):
        return None
    return parts


def get_version() -> str:
    """Return the current version string, e.g. "26.10.23" or "26.10.23-1"."""
    return __version__


def get_version_tuple() -> tuple:
    """
    Parse __version__ into a (year, month, day, n) int tuple, for callers
    that need to compare versions programmatically rather than just
    display the string (e.g. "is this build new enough to have feature X").
    n is the same-day release number from a "-N" suffix, 0 when absent.
    """
    parsed = parse_version(__version__)
    if parsed is None:
        raise ValueError(f"VERSION.md holds {__version__!r}, which isn't YY.MM.DD or YY.MM.DD-N")
    return parsed


if __name__ == "__main__":
    print(f"{__file__} is TIGHC's version module - it's a library, not meant to be run directly.")
    print("Run `python gui.py` (from the repo root) for the interactive GUI.")
