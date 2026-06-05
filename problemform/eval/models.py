"""Phase A data model for the ProblemForm evaluation framework.

See `docs/designs/milestone_03_evaluation_framework.md` for the design rationale.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Materiality = Literal["material", "minor", "stylistic_only", "degradation"]


class TestCase(BaseModel):
    __test__ = False  # tell pytest this is not a test class

    name: str
    category: str
    raw_question: str
    tags: list[str] = Field(default_factory=list)
    expected_properties: list[str] = Field(default_factory=list)
    expected_failure_modes: list[str] = Field(default_factory=list)
    notes: str | None = None
    schema_version: int = 1


class ComparativeJudgment(BaseModel):
    """A single pairwise verdict on raw_answer vs refined_answer.

    Phase A: target is locked to "answer"; prompt-vs-prompt targets land in Phase B.
    Answer text is intentionally NOT duplicated on this object; it lives on the
    enclosing TestCaseResult.
    """

    target: Literal["answer"] = "answer"
    presented_first_actual: Literal["raw", "refined"]
    winner: Literal["a", "b", "tie"]
    winner_actual: Literal["raw", "refined", "tie"]
    materiality: Materiality
    rationale: str
    key_differences: list[str] = Field(default_factory=list)


class TestCaseResult(BaseModel):
    """Per-test-case artifact bundle.

    Phase A: ``comparative_judgment`` is singular (K=1). Phase C will promote to a
    list via schema bump. Answer text is stored inline so report.json is
    self-contained; per-case ``.txt`` files are written separately for human
    inspection.
    """

    __test__ = False  # tell pytest this is not a test class

    test_case: TestCase
    raw_prompt: str
    refined_prompt: str
    problem_state_path: str | None = None
    raw_answer: str
    refined_answer: str
    comparative_judgment: ComparativeJudgment | None = None
    errors: list[str] = Field(default_factory=list)
    timing: dict[str, float] = Field(default_factory=dict)


class AggregateMetrics(BaseModel):
    """Three-way scoreboard plus material-improvement and degradation rates.

    Rates are computed over ``n_completed``, not ``n_cases``, so errored cases
    do not silently depress the win rate.
    """

    n_cases: int
    n_completed: int
    n_errored: int
    n_refined_wins: int
    n_raw_wins: int
    n_ties: int
    refined_win_rate: float | None
    raw_win_rate: float | None
    tie_rate: float | None
    material_improvement_rate: float | None
    degradation_rate: float | None


class BenchmarkReport(BaseModel):
    run_id: str
    started_at: datetime
    finished_at: datetime
    config: dict
    bias_warnings: list[str] = Field(default_factory=list)
    test_case_results: list[TestCaseResult] = Field(default_factory=list)
    aggregate: AggregateMetrics
    schema_version: int = 1
