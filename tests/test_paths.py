"""Tests for src/paths.py - filesystem layout.

conftest.py redirects APPDATA/XDG_DATA_HOME to a throwaway temp directory
before src.paths is ever imported, so these assertions run against that
temp directory rather than the developer's real per-user TIGHC install.
"""

from pathlib import Path

from src.paths import APP_ROOT, CONFIGS_DIR, PROFILES_DIR, USER_DATA_DIR


def test_user_data_dir_is_named_tighc():
    assert USER_DATA_DIR.name == "TIGHC"


def test_configs_and_profiles_dirs_are_created_under_user_data_dir():
    assert CONFIGS_DIR.parent == USER_DATA_DIR
    assert PROFILES_DIR.parent == USER_DATA_DIR
    assert CONFIGS_DIR.is_dir()
    assert PROFILES_DIR.is_dir()


def test_app_root_is_not_frozen_during_tests():
    # Running under pytest (not a PyInstaller build), APP_ROOT should be the
    # source tree's repo root, not a bundle temp dir.
    assert isinstance(APP_ROOT, Path)
    assert (APP_ROOT / "VERSION.md").exists()
