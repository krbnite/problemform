from __future__ import annotations

from typing import TypeVar

import pytest
from pydantic import BaseModel

from problemform.models import (
    AlternativeFraming,
    AlternativeFramingResult,
    Assumption,
    AssumptionExcavationResult,
    ConvergenceResult,
    ExpertPanelResult,
    ExpertPerspective,
    InformationGap,
    InformationGapResult,
    MetaQuestion,
    MetaQuestionResult,
    ObjectiveAnalysisResult,
    PromptRefinementResult,
    Revision,
)

T = TypeVar("T", bound=BaseModel)


class StubLLMProvider:
    """Deterministic LLMProvider for tests.

    First convergence call returns NEAR_CONVERGENCE; subsequent calls return
    CONVERGED so the workflow loop exits after exactly two iterations.
    """

    def __init__(self) -> None:
        self.convergence_calls = 0
        self.refinement_calls = 0

    def generate_text(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        return ""

    def generate_structured(
        self,
        prompt: str,
        output_model: type[T],
        *,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> T:
        if output_model is ObjectiveAnalysisResult:
            return output_model(
                stated_objective="stated",
                inferred_objective="inferred",
                objective_alignment="aligned",
                rationale="r",
            )
        if output_model is AssumptionExcavationResult:
            return output_model(
                assumptions=[
                    Assumption(
                        assumption="a",
                        assumption_type="implicit",
                        importance="high",
                        impact_if_wrong="i",
                        rationale="r",
                    )
                ]
            )
        if output_model is InformationGapResult:
            return output_model(
                information_gaps=[
                    InformationGap(
                        gap="g",
                        importance="high",
                        impact_if_known="i",
                        acquisition_method="user_question",
                        rationale="r",
                    )
                ]
            )
        if output_model is ExpertPanelResult:
            return output_model(
                expert_panel_perspectives=[
                    ExpertPerspective(
                        perspective_type="domain expert",
                        perspective_name="X",
                        rationale="r",
                        question="q",
                    )
                ]
            )
        if output_model is AlternativeFramingResult:
            return output_model(
                alternative_framings=[
                    AlternativeFraming(
                        framing="f",
                        rationale="r",
                        difference_from_original="d",
                        potential_value="v",
                    )
                ]
            )
        if output_model is MetaQuestionResult:
            return output_model(
                meta_questions=[
                    MetaQuestion(question="q", rationale="r", potential_impact="i")
                ]
            )
        if output_model is PromptRefinementResult:
            self.refinement_calls += 1
            return output_model(
                prompt=f"refined prompt v{self.refinement_calls}",
                revision=Revision(
                    phase="PROMPT_REFINEMENT",
                    description="d",
                    rationale="r",
                ),
            )
        if output_model is ConvergenceResult:
            self.convergence_calls += 1
            status = "CONVERGED" if self.convergence_calls >= 2 else "NEAR_CONVERGENCE"
            return output_model(
                convergence_status=status,
                rationale="r",
                remaining_opportunities=[],
            )
        raise AssertionError(f"Unexpected output_model: {output_model!r}")


@pytest.fixture
def stub_llm() -> StubLLMProvider:
    return StubLLMProvider()
