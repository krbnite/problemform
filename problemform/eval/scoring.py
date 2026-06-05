"""Shared scoring utilities for rubric and property evaluation.

Used by ``rubric_runner.py`` (α.3) for per-criterion normalization and rubric
aggregation. Will be reused by the engine-level aggregator (α.4) for
cross-case mean / delta computation and by β comparative-mode rubrics for
per-criterion winner scoring.

Kept separate from the runners on purpose — normalization arithmetic is
neither execution plumbing (the runners) nor pure data (the models). A
shared utility module is the honest home.
"""

from __future__ import annotations

from problemform.eval.models import CriterionScoring


SCORING_RANGES: dict[CriterionScoring, tuple[int, int]] = {
    "binary":   (0, 1),
    "graded_3": (0, 2),
    "graded_5": (0, 4),
}
"""Canonical (inclusive-min, inclusive-max) integer ranges per scoring scale.

Judges occasionally return values outside these ranges; ``normalize_raw_score``
clamps rather than raises so a single off-by-one verdict doesn't crash an
evaluation run.
"""


def normalize_raw_score(raw_score: int, scoring: CriterionScoring) -> float:
    """Clamp ``raw_score`` to the ``scoring`` scale and map to ``[0.0, 1.0]``.

    The ``CriterionScore.raw_score`` field stores the *unclamped* judge output
    for debugging; ``CriterionScore.score`` stores the normalized post-clamp
    value returned here.
    """
    lo, hi = SCORING_RANGES[scoring]
    clamped = max(lo, min(hi, raw_score))
    if hi == lo:
        return 0.0
    return (clamped - lo) / (hi - lo)


def weighted_average(values: list[float], weights: list[float]) -> float:
    """Compute a weighted average; return ``0.0`` when total weight is zero.

    Defensive against zero total weight rather than raising ``ZeroDivisionError``;
    callers that care about the distinction between "all-zero weights" and a
    genuine ``0.0`` average should check ``sum(weights)`` themselves.
    """
    total_weight = sum(weights)
    if total_weight == 0:
        return 0.0
    return sum(v * w for v, w in zip(values, weights)) / total_weight
