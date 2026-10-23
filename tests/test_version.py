"""Tests for src/version.py - the VERSION.md-backed version string."""

import re

from src.version import __version__, get_version, get_version_tuple, parse_version

_DATEVER_RE = re.compile(r"^\d{2}\.(0[1-9]|1[0-2])\.(0[1-9]|[12]\d|3[01])(-[1-9]\d*)?$")


def test_version_is_valid_date_version():
    assert _DATEVER_RE.match(__version__), f"{__version__!r} is not YY.MM.DD or YY.MM.DD-N"


def test_get_version_matches_version_dunder():
    assert get_version() == __version__


def test_get_version_tuple_matches_the_string():
    yy, mm, dd, n = get_version_tuple()
    expected = f"{yy:02d}.{mm:02d}.{dd:02d}" + (f"-{n}" if n else "")
    assert expected == __version__


def test_parse_version_handles_same_day_suffix_and_rejects_semver():
    assert parse_version("26.10.23") == (26, 10, 23, 0)
    assert parse_version("26.10.23-2") == (26, 10, 23, 2)
    assert parse_version("26.10.23") < parse_version("26.10.23-1") < parse_version("26.10.24")
    for bad in ("26.10", "v26.10.23", "26.10.23-0", "26.10.23-", ""):
        assert parse_version(bad) is None


def test_version_md_matches_newest_changelog_heading():
    from src.paths import APP_ROOT
    text = (APP_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    heading = re.search(r"^## v(\S+)", text, re.M)
    assert heading and heading.group(1) == __version__
