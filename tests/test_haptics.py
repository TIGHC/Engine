"""Tests for src/haptics.py - configs/haptics.json load/merge/apply."""

import json

import pytest

from src import haptics
from src.haptics import DEFAULT_HAPTICS_CONFIG, _deep_merge


def test_deep_merge_fills_in_missing_keys_from_base():
    merged = _deep_merge({"a": 1, "b": {"c": 2, "d": 3}}, {"b": {"c": 99}})
    assert merged == {"a": 1, "b": {"c": 99, "d": 3}}


def test_deep_merge_does_not_mutate_base():
    base = {"a": {"b": 1}}
    _deep_merge(base, {"a": {"b": 2}})
    assert base == {"a": {"b": 1}}


def test_load_haptics_config_creates_defaults_when_missing(tmp_path, monkeypatch):
    config_path = tmp_path / "haptics.json"
    monkeypatch.setattr(haptics, "HAPTICS_CONFIG_PATH", config_path)

    config = haptics.load_haptics_config()

    assert config == DEFAULT_HAPTICS_CONFIG
    assert json.loads(config_path.read_text(encoding="utf-8")) == DEFAULT_HAPTICS_CONFIG


def test_load_haptics_config_merges_partial_user_overrides(tmp_path, monkeypatch):
    config_path = tmp_path / "haptics.json"
    config_path.write_text(json.dumps({"intiface_ws": "ws://example:1"}), encoding="utf-8")
    monkeypatch.setattr(haptics, "HAPTICS_CONFIG_PATH", config_path)

    config = haptics.load_haptics_config()

    assert config["intiface_ws"] == "ws://example:1"
    assert config["smoothing"] == DEFAULT_HAPTICS_CONFIG["smoothing"]


def test_load_haptics_config_falls_back_to_defaults_on_invalid_json(tmp_path, monkeypatch):
    config_path = tmp_path / "haptics.json"
    config_path.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(haptics, "HAPTICS_CONFIG_PATH", config_path)

    assert haptics.load_haptics_config() == DEFAULT_HAPTICS_CONFIG


def test_apply_haptics_config_rejects_invalid_master_range(tmp_path, monkeypatch):
    config_path = tmp_path / "haptics.json"
    monkeypatch.setattr(haptics, "HAPTICS_CONFIG_PATH", config_path)
    bad_config = json.loads(json.dumps(DEFAULT_HAPTICS_CONFIG))
    bad_config["master"]["range"] = [1.5, 2.0]

    with pytest.raises(ValueError):
        haptics.apply_haptics_config(bad_config)
    assert not config_path.exists()  # rejected before anything was written


def test_apply_haptics_config_persists_and_updates_module_globals(tmp_path, monkeypatch):
    config_path = tmp_path / "haptics.json"
    monkeypatch.setattr(haptics, "HAPTICS_CONFIG_PATH", config_path)
    # apply_haptics_config() reassigns these via `global` - pre-registering
    # them with monkeypatch (even to their current value) makes it restore
    # whatever they end up as after the call, so this test can't leak state
    # into whichever test module happens to run next.
    monkeypatch.setattr(haptics, "INTIFACE_WS", haptics.INTIFACE_WS)
    monkeypatch.setattr(haptics, "PANIC_KEY", haptics.PANIC_KEY)
    new_config = json.loads(json.dumps(DEFAULT_HAPTICS_CONFIG))
    new_config["intiface_ws"] = "ws://changed:9"
    new_config["panic_key"]["key"] = "F9"

    haptics.apply_haptics_config(new_config)

    assert json.loads(config_path.read_text(encoding="utf-8"))["intiface_ws"] == "ws://changed:9"
    assert haptics.INTIFACE_WS == "ws://changed:9"
    assert haptics.PANIC_KEY == "f9"  # normalized to lowercase
