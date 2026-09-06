"""Tests for src/devices.py - nickname slugification and channel-nickname resolution."""

from src.devices import _slugify, resolve_channel_nicknames


def test_slugify_replaces_non_alphanumeric_and_collapses_runs():
    assert _slugify("Lovense Edge v2!") == "lovense_edge_v2"


def test_slugify_strips_leading_and_trailing_separators():
    assert _slugify("__Weird--Name__") == "weird_name"


def test_slugify_never_returns_empty():
    assert _slugify("!!!") == "device"


def test_resolve_channel_nicknames_reuses_saved_nickname():
    registry = [{"device_name": "Edge", "feature_index": 0, "output_type": "vibrate", "description": None, "nickname": "left"}]
    entries = [("Edge", 0, "vibrate", None)]

    result = resolve_channel_nicknames(registry, entries)

    assert result == {("Edge", 0, "vibrate"): "left"}
    assert len(registry) == 1  # nothing new appended


def test_resolve_channel_nicknames_generates_motor_suffix_for_multi_feature_device():
    registry = []
    entries = [
        ("Edge", 0, "vibrate", None),
        ("Edge", 1, "vibrate", None),
    ]

    result = resolve_channel_nicknames(registry, entries)

    assert result[("Edge", 0, "vibrate")] == "edge_motor1"
    assert result[("Edge", 1, "vibrate")] == "edge_motor2"
    assert len(registry) == 2


def test_resolve_channel_nicknames_appends_output_type_for_multi_output_device():
    registry = []
    entries = [
        ("Toy", 0, "vibrate", None),
        ("Toy", 0, "oscillate", None),
    ]

    result = resolve_channel_nicknames(registry, entries)

    assert result[("Toy", 0, "vibrate")] == "toy_vibrate"
    assert result[("Toy", 0, "oscillate")] == "toy_oscillate"


def test_resolve_channel_nicknames_dedupes_collisions_with_numeric_suffix():
    registry = [{"device_name": "toy", "feature_index": 9, "output_type": "vibrate", "description": None, "nickname": "toy"}]
    entries = [("Toy", 0, "vibrate", None)]  # slugifies to the same "toy" nickname already taken

    result = resolve_channel_nicknames(registry, entries)

    assert result[("Toy", 0, "vibrate")] == "toy_2"


def test_resolve_channel_nicknames_uses_description_when_present():
    registry = []
    entries = [("Edge", 0, "vibrate", "Left Motor")]

    result = resolve_channel_nicknames(registry, entries)

    assert result[("Edge", 0, "vibrate")] == "edge_left_motor"
