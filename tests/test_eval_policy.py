"""Formulation-type policy registry (M3B-β.1.1)."""

from problemform.eval.models import CANONICAL_FORMULATION_TYPES
from problemform.eval.policy import (
    DEFAULT_POLICY,
    FORMULATION_POLICIES,
    FormulationPolicy,
    answer_comparison_applies,
    policy_for,
)

ANSWERABLE = {"question", "explanation", "instruction", "prompt", "specification"}
FORMULATION_ONLY = {"argument", "belief", "decision", "dilemma", "goal", "plan"}


def test_registry_covers_every_canonical_type():
    """No canonical formulation type may silently rely on the fallback policy."""
    assert set(FORMULATION_POLICIES) == set(CANONICAL_FORMULATION_TYPES)


def test_answerable_set():
    for t in ANSWERABLE:
        assert policy_for(t).answer_comparison is True, t
        assert answer_comparison_applies(t) is True, t


def test_formulation_only_set():
    for t in FORMULATION_ONLY:
        assert policy_for(t).answer_comparison is False, t
        assert answer_comparison_applies(t) is False, t


def test_answerable_and_formulation_only_partition_the_canonical_types():
    assert ANSWERABLE | FORMULATION_ONLY == set(CANONICAL_FORMULATION_TYPES)
    assert ANSWERABLE & FORMULATION_ONLY == set()


def test_unspecified_and_unknown_fall_back_to_answerable():
    assert DEFAULT_POLICY.answer_comparison is True
    assert policy_for("unspecified") is DEFAULT_POLICY
    assert policy_for("some_future_type") is DEFAULT_POLICY
    assert answer_comparison_applies("unspecified") is True
    assert answer_comparison_applies("some_future_type") is True


def test_override_wins_over_policy():
    # Override forces regardless of the per-type default.
    assert answer_comparison_applies("decision", override=True) is True    # formulation-only forced on
    assert answer_comparison_applies("question", override=False) is False  # answerable forced off
    # override=None defers to the policy.
    assert answer_comparison_applies("decision", override=None) is False
    assert answer_comparison_applies("question", override=None) is True


def test_policy_is_immutable():
    import dataclasses
    import pytest

    p = FormulationPolicy()
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.answer_comparison = False  # type: ignore[misc]
