"""Formulation-type evaluation policy registry.

Keyed by ``TestCase.formulation_type``, this maps each formulation type to a
:class:`FormulationPolicy`. M3B-β.1 uses a single field — whether the M3A
answer-comparison lens applies — but the policy is an *object* so later β phases
can extend it (default rubrics, property suites, …) without changing the registry's
shape or callers.

**Answerability criterion:** a formulation type is *answerable* when the refinement
naturally induces a downstream response or artifact **whose quality we care about**
(e.g. a question → an answer, a specification → an implementation). Types whose
deliverable is the refined formulation itself (arguments, beliefs, decisions,
dilemmas, goals, plans) are *formulation-only* and skip the answer lens. See
``docs/plans/m3b_beta_1_plan_by_claude.md`` and the amendment in
``docs/designs/m3b_beta_corpus_diversification.md``.
"""

from __future__ import annotations

from dataclasses import dataclass

from problemform.eval.models import CANONICAL_FORMULATION_TYPES


@dataclass(frozen=True)
class FormulationPolicy:
    """Immutable per-formulation-type evaluation policy.

    β.1 field: ``answer_comparison`` — whether the M3A answer-comparison lens runs
    for cases of this type. Later phases add fields (with defaults) so existing
    registry entries keep working.
    """

    answer_comparison: bool = True


_ANSWERABLE = FormulationPolicy(answer_comparison=True)
_FORMULATION_ONLY = FormulationPolicy(answer_comparison=False)

# Answer lens ON for types whose refinement induces a downstream artifact we grade;
# OFF for types whose deliverable is the refined formulation itself. Every
# CANONICAL_FORMULATION_TYPES member has an explicit entry (asserted by a test).
FORMULATION_POLICIES: dict[str, FormulationPolicy] = {
    "question": _ANSWERABLE,
    "explanation": _ANSWERABLE,
    "instruction": _ANSWERABLE,
    "prompt": _ANSWERABLE,
    "specification": _ANSWERABLE,
    "argument": _FORMULATION_ONLY,
    "belief": _FORMULATION_ONLY,
    "decision": _FORMULATION_ONLY,
    "dilemma": _FORMULATION_ONLY,
    "goal": _FORMULATION_ONLY,
    "plan": _FORMULATION_ONLY,
}

# Unknown / "unspecified" types keep legacy behavior (answer lens ON) so pre-typed
# corpora are unaffected.
DEFAULT_POLICY = FormulationPolicy()


def policy_for(formulation_type: str) -> FormulationPolicy:
    """Return the policy for ``formulation_type``, falling back to ``DEFAULT_POLICY``."""
    return FORMULATION_POLICIES.get(formulation_type, DEFAULT_POLICY)


def answer_comparison_applies(
    formulation_type: str, *, override: bool | None = None
) -> bool:
    """Whether the M3A answer-comparison lens applies for a formulation type.

    A CLI-level ``override`` (``--answer-comparison`` / ``--no-answer-comparison``)
    wins when set; otherwise the per-type policy decides.
    """
    if override is not None:
        return override
    return policy_for(formulation_type).answer_comparison


# Fail loudly at import time if the registry drifts from the canonical vocabulary,
# so a newly-added formulation type cannot silently rely on DEFAULT_POLICY.
assert set(FORMULATION_POLICIES) == set(CANONICAL_FORMULATION_TYPES), (
    "FORMULATION_POLICIES must classify every CANONICAL_FORMULATION_TYPES member"
)
