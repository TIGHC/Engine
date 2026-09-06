"""Tests for src/ranges.py - the intensity/duration band types."""

import pytest

from src.ranges import DurationRange, FloatRange, PulseSpec, VibeRange


def test_float_range_accepts_low_equal_high():
    r = FloatRange(0.5, 0.5)
    assert r.roll() == 0.5


def test_float_range_rejects_low_above_high():
    with pytest.raises(ValueError):
        FloatRange(0.6, 0.4)


def test_float_range_roll_stays_within_bounds():
    r = FloatRange(2.0, 5.0)
    for _ in range(200):
        value = r.roll()
        assert 2.0 <= value <= 5.0


def test_vibe_range_accepts_full_bounds():
    assert VibeRange(0.0, 1.0).high == 1.0


@pytest.mark.parametrize("low, high", [(-0.1, 0.5), (0.5, 1.1), (-0.1, 1.1)])
def test_vibe_range_rejects_out_of_bounds(low, high):
    with pytest.raises(ValueError):
        VibeRange(low, high)


def test_vibe_range_str_is_a_percent_span():
    assert str(VibeRange(0.4, 0.65)) == "40-65%"


def test_duration_range_str_is_seconds_span():
    assert str(DurationRange(0.3, 0.4)) == "0.30-0.40s"


def test_duration_range_allows_values_above_one():
    # Unlike VibeRange, duration isn't bounded to 0-1 - it's seconds.
    assert DurationRange(0.1, 5.0).high == 5.0


def test_pulse_spec_roll_duration_delegates_to_duration_range():
    spec = PulseSpec(vibe=VibeRange(0.2, 0.2), duration=DurationRange(1.0, 1.0))
    assert spec.roll_duration() == 1.0
