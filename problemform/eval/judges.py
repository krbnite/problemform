"""Comparative judgment helpers.

Randomizes presentation order per the bias-mitigation policy in
``docs/designs/milestone_03_evaluation_framework.md`` Section 7. The judge sees
opaque labels "A" and "B"; the engine records which label was actually
"refined" and de-anonymizes ``winner_actual``.
"""

from __future__ import annotations

import random
from typing import Literal

from pydantic import BaseModel, Field

from problemform.core.language_models import LLMProvider
from problemform.eval.models import ComparativeJudgment, Materiality
from problemform.eval.prompts.comparative_judge import PROMPT as COMPARATIVE_JUDGE_PROMPT


class ComparativeJudgmentResult(BaseModel):
    """Envelope matching the JSON schema in the comparative-judge prompt."""

    winner: Literal["a", "b", "tie"]
    materiality: Materiality
    rationale: str
    key_differences: list[str] = Field(default_factory=list)


def _resolve_winner_actual(
    judge_winner: Literal["a", "b", "tie"],
    presented_first_actual: Literal["raw", "refined"],
) -> Literal["raw", "refined", "tie"]:
    """De-anonymize the judge's a/b verdict given which side was presented first."""
    if judge_winner == "tie":
        return "tie"
    if presented_first_actual == "raw":
        return "raw" if judge_winner == "a" else "refined"
    # presented_first_actual == "refined"
    return "refined" if judge_winner == "a" else "raw"


def judge_answers(
    judge_provider: LLMProvider,
    question: str,
    raw_answer: str,
    refined_answer: str,
    *,
    rng: random.Random | None = None,
) -> ComparativeJudgment:
    """Run a single position-randomized comparative judgment.

    Returns a fully-populated ``ComparativeJudgment`` with ``winner_actual``
    de-anonymized from the judge's ``a/b`` verdict and ``presented_first_actual``
    set to whichever side appeared in the "Answer A" slot.
    """
    rng = rng or random.Random()
    present_refined_first = rng.random() < 0.5

    if present_refined_first:
        answer_a, answer_b = refined_answer, raw_answer
        presented_first_actual: Literal["raw", "refined"] = "refined"
    else:
        answer_a, answer_b = raw_answer, refined_answer
        presented_first_actual = "raw"

    prompt = (
        COMPARATIVE_JUDGE_PROMPT
        .replace("{question}", question)
        .replace("{answer_a}", answer_a)
        .replace("{answer_b}", answer_b)
    )
    result = judge_provider.generate_structured(
        prompt=prompt,
        output_model=ComparativeJudgmentResult,
        temperature=0.0,
    )
    return ComparativeJudgment(
        target="answer",
        presented_first_actual=presented_first_actual,
        winner=result.winner,
        winner_actual=_resolve_winner_actual(result.winner, presented_first_actual),
        materiality=result.materiality,
        rationale=result.rationale,
        key_differences=result.key_differences,
    )
