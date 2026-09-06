"""Tests for src/profiles.py - profile.json parsing/validation and matching."""

import json

import pytest

from src.profiles import Profile, _load_profile, _parse_devices_field


def _write_profile(tmp_path, data, folder_name="testgame"):
    profile_dir = tmp_path / folder_name
    profile_dir.mkdir()
    (profile_dir / "profile.json").write_text(json.dumps(data), encoding="utf-8")
    return profile_dir


def _minimal_profile(**overrides):
    data = {
        "name": "Test Game",
        "window_titles": ["Test Game"],
        "bindings": [
            {"id": "attack", "keys": ["mouse_left"], "enabled": True, "devices": ["all"], "vibe": [0.5, 0.8]},
        ],
    }
    data.update(overrides)
    return data


# ------------------------------------------------------------------ _parse_devices_field

def test_parse_devices_field_defaults_to_all_when_omitted():
    assert _parse_devices_field({"id": "x"}) is None


def test_parse_devices_field_all_means_none():
    assert _parse_devices_field({"id": "x", "devices": ["ALL"]}) is None


def test_parse_devices_field_lowercases_and_freezes_nicknames():
    assert _parse_devices_field({"id": "x", "devices": ["Left", "right"]}) == frozenset({"left", "right"})


@pytest.mark.parametrize("devices_field", [[], "left", 5, None])
def test_parse_devices_field_rejects_non_list_or_empty(devices_field):
    with pytest.raises(ValueError):
        _parse_devices_field({"id": "x", "devices": devices_field})


# ------------------------------------------------------------------ _load_profile

def test_load_profile_parses_basic_fields(tmp_path):
    profile_dir = _write_profile(tmp_path, _minimal_profile())
    profile = _load_profile(profile_dir)

    assert profile.id == "testgame"
    assert profile.name == "Test Game"
    assert profile.window_titles == ["Test Game"]
    assert profile.window_title_exact is False
    assert "mouse_left" in profile.bindings_by_key
    assert profile.bindings_by_key["mouse_left"].id == "attack"
    assert len(profile.bindings) == 1


def test_load_profile_missing_file_raises(tmp_path):
    profile_dir = tmp_path / "empty"
    profile_dir.mkdir()
    with pytest.raises(ValueError, match="profile.json"):
        _load_profile(profile_dir)


def test_load_profile_requires_window_titles(tmp_path):
    profile_dir = _write_profile(tmp_path, _minimal_profile(window_titles=[]))
    with pytest.raises(ValueError, match="window_titles"):
        _load_profile(profile_dir)


def test_load_profile_rejects_duplicate_binding_ids(tmp_path):
    data = _minimal_profile()
    data["bindings"].append(dict(data["bindings"][0]))
    profile_dir = _write_profile(tmp_path, data)
    with pytest.raises(ValueError, match="duplicate binding id"):
        _load_profile(profile_dir)


def test_load_profile_rejects_binding_with_no_keys(tmp_path):
    data = _minimal_profile()
    data["bindings"][0]["keys"] = []
    profile_dir = _write_profile(tmp_path, data)
    with pytest.raises(ValueError, match="no keys"):
        _load_profile(profile_dir)


def test_load_profile_rejects_binding_missing_vibe(tmp_path):
    data = _minimal_profile()
    del data["bindings"][0]["vibe"]
    profile_dir = _write_profile(tmp_path, data)
    with pytest.raises(ValueError, match="no 'vibe' field"):
        _load_profile(profile_dir)


def test_load_profile_skips_disabled_bindings_in_dispatch_map(tmp_path):
    data = _minimal_profile()
    data["bindings"][0]["enabled"] = False
    profile_dir = _write_profile(tmp_path, data)
    profile = _load_profile(profile_dir)

    assert profile.bindings_by_key == {}
    assert len(profile.bindings) == 1  # still recorded for the banner/GUI


def test_load_profile_falls_back_to_folder_name_when_name_missing(tmp_path):
    data = _minimal_profile()
    del data["name"]
    profile_dir = _write_profile(tmp_path, data, folder_name="nameless")
    profile = _load_profile(profile_dir)
    assert profile.name == "nameless"


# ------------------------------------------------------------------ Profile.matches

def test_profile_matches_substring_by_default():
    profile = Profile(id="p", name="P", window_titles=["Grounded"], bindings_by_key={}, bindings=[], priority=[])
    assert profile.matches("Grounded 2 - Steam")
    assert not profile.matches("Minecraft")


def test_profile_matches_exact_when_flagged():
    profile = Profile(
        id="p", name="P", window_titles=["Grounded"], bindings_by_key={}, bindings=[], priority=[],
        window_title_exact=True,
    )
    assert profile.matches("Grounded")
    assert not profile.matches("Grounded 2")
