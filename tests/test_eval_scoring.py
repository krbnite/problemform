import pytest

from problemform.eval.scoring import (
    SCORING_RANGES,
    normalize_raw_score,
    weighted_average,
)


def test_normalize_binary_endpoints():
    assert normalize_raw_score(0, "binary") == 0.0
    assert normalize_raw_score(1, "binary") == 1.0


def test_normalize_graded_3_each_step():
    assert normalize_raw_score(0, "graded_3") == 0.0
    assert normalize_raw_score(1, "graded_3") == 0.5
    assert normalize_raw_score(2, "graded_3") == 1.0


def test_normalize_graded_5_each_step():
    assert normalize_raw_score(0, "graded_5") == 0.0
    assert normalize_raw_score(1, "graded_5") == 0.25
    assert normalize_raw_score(2, "graded_5") == 0.5
    assert normalize_raw_score(3, "graded_5") == 0.75
    assert normalize_raw_score(4, "graded_5") == 1.0


def test_normalize_clamps_out_of_range_high_and_low():
    # Judges sometimes return out-of-scale; runner should clamp not crash.
    assert normalize_raw_score(7, "graded_5") == 1.0       # clamp high
    assert normalize_raw_score(-3, "graded_5") == 0.0       # clamp low
    assert normalize_raw_score(99, "binary") == 1.0
    assert normalize_raw_score(-1, "binary") == 0.0


def test_scoring_ranges_cover_all_scales():
    # Defends against a new scale being added to the model without an entry here.
    assert set(SCORING_RANGES.keys()) == {"binary", "graded_3", "graded_5"}


def test_weighted_average_uniform_weights():
    assert weighted_average([0.2, 0.4, 0.6], [1.0, 1.0, 1.0]) == pytest.approx(0.4)


def test_weighted_average_non_uniform_weights():
    # (0.2 * 1 + 0.4 * 2 + 0.6 * 1) / 4 = 0.4
    assert weighted_average([0.2, 0.4, 0.6], [1.0, 2.0, 1.0]) == pytest.approx(0.4)


def test_weighted_average_zero_total_weight_returns_zero():
    """Zero total weight returns 0.0 rather than raising ZeroDivisionError."""
    assert weighted_average([0.5, 0.7], [0.0, 0.0]) == 0.0
    assert weighted_average([], []) == 0.0
