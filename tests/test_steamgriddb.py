"""Tests for src/steamgriddb.py's pure helper - pick_best()."""

from src.steamgriddb import pick_best


def test_pick_best_returns_none_for_empty_list():
    assert pick_best([]) is None


def test_pick_best_prefers_official_style():
    assets = [{"id": 1, "style": "alternate"}, {"id": 2, "style": "official"}, {"id": 3, "style": "alternate"}]
    assert pick_best(assets)["id"] == 2


def test_pick_best_falls_back_to_first_when_no_official_style():
    assets = [{"id": 1, "style": "alternate"}, {"id": 2, "style": "blurred"}]
    assert pick_best(assets)["id"] == 1
