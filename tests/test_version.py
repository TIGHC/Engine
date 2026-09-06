"""Tests for src/version.py - the VERSION.md-backed version string."""

import re

from src.version import __version__, get_version, get_version_tuple

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def test_version_is_valid_semver():
    assert _SEMVER_RE.match(__version__), f"{__version__!r} is not MAJOR.MINOR.PATCH"


def test_get_version_matches_version_dunder():
    assert get_version() == __version__


def test_get_version_tuple_matches_the_string():
    major, minor, patch = get_version_tuple()
    assert f"{major}.{minor}.{patch}" == __version__
    assert all(isinstance(part, int) for part in (major, minor, patch))
