"""Tests for src/metadata.py - project identity constants."""

from src import metadata


def test_project_identity_constants_are_nonempty_strings():
    for name in ("PROJECT_NAME", "PROJECT_SHORT_NAME", "REPO_URL", "WEBSITE_URL", "AUTHOR_NAME", "AUTHOR_URL"):
        value = getattr(metadata, name)
        assert isinstance(value, str) and value, f"{name} should be a non-empty string"


def test_urls_use_https():
    assert metadata.REPO_URL.startswith("https://")
    assert metadata.WEBSITE_URL.startswith("https://")
    assert metadata.AUTHOR_URL.startswith("https://")
