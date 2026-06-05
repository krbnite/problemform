"""Absolute-mode rubric runner.

Scores one ``Rubric`` against one subject (a formulation or an artifact),
producing an ``AbsoluteRubricEvaluation``. One judge call per criterion;
results are aggregated via the shared ``weighted_average`` helper.

Comparative-mode rubrics are deferred to M3B-β and rejected here with a
clear error. Engine integration (calling this from ``run_benchmark``),
cross-case aggregation, and report rendering all land in M3B-α.4.
"""

from __future__ import annotations

from pydantic import BaseModel

from problemform.core.language_models import LLMProvider
from problemform.eval.models import (
    AbsoluteRubricEvaluation,
    CriterionScore,
    CriterionScoring,
    EvalSubject,
    EvalTarget,
    Rubric,
    RubricCriterion,
)
from problemform.eval.prompts.rubric_judge import PROMPT as RUBRIC_JUDGE_PROMPT
from problemform.eval.scoring import normalize_raw_score, weighted_average


class _RubricCriterionVerdict(BaseModel):
    """Throw-away envelope for one criterion's judge call."""

    raw_score: int
    rationale: str


_SUBJECT_KIND_DISPLAY: dict[EvalTarget, tuple[str, str]] = {
    "formulation": ("Formulation", "formulation"),
    "artifact":    ("Artifact",    "artifact"),
}


_SCALE_SPECS: dict[CriterionScoring, str] = {
    "binary": (
        "Binary (0 or 1). Score 0 when the criterion is not met. Score 1 when "
        "the criterion is met."
    ),
    "graded_3": (
        "0–2 graded scale. Score 0 when the criterion is not met at all. "
        "Score 1 when the criterion is partially met. Score 2 when the "
        "criterion is fully met."
    ),
    "graded_5": (
        "0–4 graded scale. Score 0 when the criterion is not met at all. "
        "Score 1, 2, or 3 for increasing partial fulfillment. Score 4 when "
        "the criterion is fully met."
    ),
}


def _build_scale_spec(scoring: CriterionScoring) -> str:
    return _SCALE_SPECS[scoring]


def _score_criterion(
    criterion: RubricCriterion,
    subject_text: str,
    target: EvalTarget,
    judge_provider: LLMProvider,
) -> CriterionScore:
    subject_kind, subject_kind_lc = _SUBJECT_KIND_DISPLAY[target]
    prompt = (
        RUBRIC_JUDGE_PROMPT
        .replace("{subject_kind_lowercase}", subject_kind_lc)
        .replace("{subject_kind}", subject_kind)
        .replace("{criterion_name}", criterion.name)
        .replace("{criterion_description}", criterion.description)
        .replace("{scoring_scale_spec}", _build_scale_spec(criterion.scoring))
        .replace("{subject_text}", subject_text)
    )
    verdict = judge_provider.generate_structured(
        prompt=prompt,
        output_model=_RubricCriterionVerdict,
        temperature=0.0,
    )
    return CriterionScore(
        criterion_name=criterion.name,
        score=normalize_raw_score(verdict.raw_score, criterion.scoring),
        raw_score=verdict.raw_score,
        rationale=verdict.rationale,
    )


def run_rubric(
    rubric: Rubric,
    subject_text: str,
    subject_label: EvalSubject,
    judge_provider: LLMProvider,
) -> AbsoluteRubricEvaluation:
    """Score ``rubric`` against ``subject_text`` and return an evaluation.

    Iterates ``rubric.criteria`` in order, calling the judge once per criterion.
    Normalizes each per-criterion raw score to ``[0.0, 1.0]`` via
    ``normalize_raw_score`` and aggregates to a weighted average via
    ``weighted_average``.

    Raises ``ValueError`` for comparative-mode rubrics — those are deferred to
    M3B-β. The mode field is reserved in the schema so a comparative rubric
    can be defined today and rejected here rather than misinterpreted.
    """
    if rubric.mode != "absolute":
        raise ValueError(
            f"run_rubric only supports mode='absolute' in M3B-α; "
            f"rubric {rubric.name!r} has mode={rubric.mode!r}. "
            f"Comparative-mode rubrics land in M3B-β."
        )

    criterion_scores = [
        _score_criterion(c, subject_text, rubric.target, judge_provider)
        for c in rubric.criteria
    ]
    aggregate = weighted_average(
        values=[cs.score for cs in criterion_scores],
        weights=[c.weight for c in rubric.criteria],
    )
    return AbsoluteRubricEvaluation(
        rubric_name=rubric.name,
        target=rubric.target,
        subject=subject_label,
        criterion_scores=criterion_scores,
        aggregate_score=aggregate,
    )
