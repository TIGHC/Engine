"""Checks GitHub for a newer TIGHC release than the one currently running.

Reads raw.githubusercontent.com's copy of VERSION.md rather than the GitHub
Releases API - no auth, no API rate limits, and the same approach
src/profiles.py already uses to read repo content without hitting
api.github.com.
"""

import urllib.request
from typing import Optional

from src.metadata import REPO_URL
from src.version import get_version_tuple

TIGHC_VERSION_URL = "https://raw.githubusercontent.com/TIGHC/Engine/main/VERSION.md"


def _github_get(url: str, timeout: int = 8) -> Optional[bytes]:
    """GET a URL with a User-Agent header. Returns raw bytes or None on any error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TIGHC"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def _parse_version_tuple(text: str) -> Optional[tuple]:
    """Parse a "X.Y.Z" string into an (int, int, int) tuple, or None if malformed."""
    try:
        major, minor, patch = text.strip().split(".")
        return (int(major), int(minor), int(patch))
    except (ValueError, AttributeError):
        return None


def check_for_update(timeout: int = 8) -> Optional[dict]:
    """
    Check GitHub for a newer TIGHC release than the one currently running.

    Blocking (plain urllib, no extra dependency) - callers (gui.py) are
    responsible for running this off the Tk main thread, e.g. via a daemon
    thread + root.after(0, ...) to marshal the result back, same as every
    other network call in this app.

    Returns None if the check fails (offline, rate-limited, malformed
    response) or the current version is already the latest. On an
    available update, returns {"version": "X.Y.Z", "url": "<release URL>"}.
    """
    data = _github_get(TIGHC_VERSION_URL, timeout=timeout)
    if data is None:
        return None
    remote_str = data.decode("utf-8", errors="replace").strip()
    remote = _parse_version_tuple(remote_str)
    if remote is None or remote <= get_version_tuple():
        return None
    return {
        "version": remote_str,
        "url": f"{REPO_URL}/releases/tag/v{remote_str}",
    }


if __name__ == "__main__":
    print(f"{__file__} is TIGHC's update-check module - it's a library, not meant to be run directly.")
    print("Run `python gui.py` (from the repo root) for the interactive GUI.")
