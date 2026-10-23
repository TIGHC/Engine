"""Tests for src/updates.py - GitHub update check.

check_for_update() itself makes a real network call via _github_get(), so
every test here monkeypatches that (network/GUI-free, per this suite's own
convention - see test_profiles.py) rather than hitting GitHub.
"""

from src import updates


def test_parse_version_tuple_valid():
    assert updates._parse_version_tuple("26.10.23") == (26, 10, 23, 0)
    assert updates._parse_version_tuple(" 26.10.23-2 \n") == (26, 10, 23, 2)


def test_parse_version_tuple_rejects_malformed_input():
    for bad in ("26.10", "26.10.23.1", "vYY.MM.DD", "", "26.10.xx", "26.13.01", "26.10.23-0"):
        assert updates._parse_version_tuple(bad) is None


def test_check_for_update_returns_none_when_fetch_fails(monkeypatch):
    monkeypatch.setattr(updates, "_github_get", lambda url, timeout=8: None)
    assert updates.check_for_update() is None


def test_check_for_update_returns_none_on_malformed_remote_version(monkeypatch):
    monkeypatch.setattr(updates, "_github_get", lambda url, timeout=8: b"not-a-version")
    assert updates.check_for_update() is None


def test_check_for_update_returns_none_when_remote_is_not_newer(monkeypatch):
    monkeypatch.setattr(updates, "get_version_tuple", lambda: (26, 10, 23, 0))
    monkeypatch.setattr(updates, "_github_get", lambda url, timeout=8: b"26.10.23")
    assert updates.check_for_update() is None

    monkeypatch.setattr(updates, "_github_get", lambda url, timeout=8: b"26.10.22")
    assert updates.check_for_update() is None


def test_check_for_update_returns_details_when_remote_is_newer(monkeypatch):
    monkeypatch.setattr(updates, "get_version_tuple", lambda: (26, 10, 23, 0))
    monkeypatch.setattr(updates, "_github_get", lambda url, timeout=8: b"26.10.23-1\n")

    result = updates.check_for_update()

    assert result == {
        "version": "26.10.23-1",
        "url": "https://github.com/TIGHC/Engine/releases/tag/v26.10.23-1",
    }


def test_check_for_update_requests_version_md_from_github(monkeypatch):
    seen = {}

    def fake_get(url, timeout=8):
        seen["url"] = url
        return b"0.0.1"  # never newer, keeps the assertion focused on the URL

    monkeypatch.setattr(updates, "_github_get", fake_get)
    updates.check_for_update()

    assert seen["url"] == updates.TIGHC_VERSION_URL
    assert seen["url"] == "https://raw.githubusercontent.com/TIGHC/Engine/main/VERSION.md"
