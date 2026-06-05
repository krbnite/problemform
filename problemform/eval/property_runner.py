"""Property-check runner.

Evaluates ``PropertyCheck``s against a subject (a formulation or an artifact),
producing ``PropertyCheckResult``s. One judge call per property. ``passed`` is
computed by the runner from ``holds`` and the property's ``expected`` polarity.

Engine integration (calling these from ``run_benchmark`` and activating
``TestCase.expected_properties`` as runnable assertions) and per-property
aggregation across cases both land in M3B-α.4.
"""

from __future__ import annotations

from pydantic import BaseModel

from problemform.core.language_models import LLMProvider
from problemform.eval.models import (
    EvalSubject,
    EvalTarget,
    PropertyCheck,
    PropertyCheckResult,
)
from problemform.eval.prompts.property_judge import PROMPT as PROPERTY_JUDGE_PROMPT


class _PropertyVerdict(BaseModel):
    """Throw-away envelope for one property's judge call."""

    holds: bool
    rationale: str


_SUBJECT_KIND_DISPLAY: dict[EvalTarget, tuple[str, str]] = {
    "formulation": ("Formulation", "formulation"),
    "artifact":    ("Artifact",    "artifact"),
}


def run_property_check(
    property_check: PropertyCheck,
    subject_text: str,
    subject_label: EvalSubject,
    judge_provider: LLMProvider,
) -> PropertyCheckResult:
    """Evaluate one ``PropertyCheck`` against ``subject_text``.

    The judge reports only ``holds`` (whether the property is satisfied);
    the runner combines that with ``property_check.expected`` to compute
    ``passed = (holds == expected)``. This separates "did the judge observe
    the property?" (judge's concern) from "is the observation what we wanted
    to see?" (caller's concern via the polarity).
    """
    subject_kind, subject_kind_lc = _SUBJECT_KIND_DISPLAY[property_check.target]
    prompt = (
        PROPERTY_JUDGE_PROMPT
        .replace("{subject_kind_lowercase}", subject_kind_lc)
        .replace("{subject_kind}", subject_kind)
        .replace("{property_name}", property_check.name)
        .replace("{property_description}", property_check.description)
        .replace("{subject_text}", subject_text)
    )
    verdict = judge_provider.generate_structured(
        prompt=prompt,
        output_model=_PropertyVerdict,
        temperature=0.0,
    )
    return PropertyCheckResult(
        property_name=property_check.name,
        target=property_check.target,
        subject=subject_label,
        holds=verdict.holds,
        expected=property_check.expected,
        passed=(verdict.holds == property_check.expected),
        rationale=verdict.rationale,
    )


def run_property_checks(
    properties: list[PropertyCheck],
    subject_text: str,
    subject_label: EvalSubject,
    judge_provider: LLMProvider,
) -> list[PropertyCheckResult]:
    """Batch convenience: evaluate ``properties`` against the same subject.

    Preserves input order so callers can pair results back to property
    definitions positionally if they choose.
    """
    return [
        run_property_check(p, subject_text, subject_label, judge_provider)
        for p in properties
    ]
