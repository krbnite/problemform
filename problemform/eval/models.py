"""Evaluation-framework data model.

Phase A (M3A) types — ``TestCase``, ``ComparativeJudgment``, ``TestCaseResult``,
``AggregateMetrics``, ``BenchmarkReport`` — capture the answer-comparison
contract. See ``docs/designs/milestone_03_evaluation_framework.md`` for that
design.

Phase B (M3B-α) types — ``Rubric`` / ``RubricCriterion`` / ``CriterionScore`` /
``AbsoluteRubricEvaluation`` / ``RubricAggregate`` and ``PropertyCheck`` /
``PropertyCheckResult`` / ``PropertyAggregate`` — add target-aware rubric and
property-check evaluation. ``target`` is a first-class axis (``formulation`` or
``artifact``) on rubrics and property checks; only absolute mode is supported
in α (comparative mode deferred to M3B-β). See
``docs/designs/milestone_03b_rubrics_and_properties.md``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Materiality = Literal["material", "minor", "stylistic_only", "degradation"]


CANONICAL_FORMULATION_TYPES: frozenset[str] = frozenset({
    "question", "argument", "belief", "decision", "dilemma", "explanation",
    "goal", "instruction", "plan", "prompt", "specification",
})
"""The project's canonical formulation-type vocabulary.

Advisory, **not** enforced: ``TestCase.formulation_type`` is a free ``str`` so the
corpus can grow without a code change, and unknown values fall back to a generic
policy in later phases (M3B-β.1). This set simply names the formulation types the
framework recognizes today.
"""


class TestCase(BaseModel):
    """A single benchmark input.

    ``formulation_type`` classifies *what kind* of input this is (question,
    argument, decision, …; see ``CANONICAL_FORMULATION_TYPES``) and is the axis the
    corpus is organized around. It is distinct from ``category``, which is a free
    organizational/topic label. As of M3B-β.0 the field is populated but not yet
    consumed by the engine or report.
    """

    __test__ = False  # tell pytest this is not a test class

    name: str
    category: str
    raw_formulation: str  # the user's raw problem formulation, of any type (question, decision, dilemma, belief, argument, goal, …)
    formulation_type: str = "unspecified"  # canonical formulation type; see CANONICAL_FORMULATION_TYPES. Advisory metadata, not enforced.
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


# --- M3B-α: rubric + property-check types --------------------------------


EvalTarget = Literal["formulation", "artifact"]
RubricMode = Literal["absolute", "comparative"]
CriterionScoring = Literal["binary", "graded_3", "graded_5"]
EvalSubject = Literal["raw", "refined"]


class RubricCriterion(BaseModel):
    """A single criterion within a ``Rubric``.

    ``scoring`` selects the raw-score scale used by the judge; the runner
    normalizes to ``0.0..1.0`` for aggregation. ``weight`` enters the rubric's
    aggregate as a weighted average.
    """

    name: str
    description: str
    weight: float = 1.0
    scoring: CriterionScoring = "graded_5"
    rationale_required: bool = True


class Rubric(BaseModel):
    """A named, ordered collection of weighted criteria with a target/mode.

    Phase α only ships absolute-mode rubrics; comparative mode is reserved for
    M3B-β. The ``target`` axis (``formulation`` vs ``artifact``) is the bridge
    mechanism — a single rubric framework can evaluate either the prompt /
    problem statement produced by ProblemForm or the downstream answer.
    """

    name: str
    description: str
    target: EvalTarget
    mode: RubricMode
    criteria: list[RubricCriterion]
    notes: str | None = None
    schema_version: int = 1


class CriterionScore(BaseModel):
    """A judge's verdict on one ``RubricCriterion`` for one subject."""

    criterion_name: str
    score: float          # normalized 0.0..1.0
    raw_score: int        # what the judge returned on the criterion's scale
    rationale: str


class AbsoluteRubricEvaluation(BaseModel):
    """Result of applying an absolute-mode rubric to a single subject."""

    rubric_name: str
    target: EvalTarget
    subject: EvalSubject
    criterion_scores: list[CriterionScore]
    aggregate_score: float


class PropertyCheck(BaseModel):
    """A binary assertion about a subject, evaluated by an LLM judge.

    Property checks are regression-shaped: they codify "this should always be
    true" rather than measuring graded quality. ``target`` selects whether the
    property is asserted about a formulation or about a downstream artifact.
    """

    name: str
    description: str
    target: EvalTarget
    expected: bool = True


class PropertyCheckResult(BaseModel):
    """Outcome of evaluating one ``PropertyCheck`` against one subject."""

    property_name: str
    target: EvalTarget
    subject: EvalSubject
    holds: bool
    expected: bool
    passed: bool          # holds == expected
    rationale: str


class TestCaseResult(BaseModel):
    """Per-test-case artifact bundle.

    Phase A: ``comparative_judgment`` is singular (K=1). Phase C will promote to a
    list via schema bump. Answer text is stored inline so report.json is
    self-contained; per-case ``.txt`` files are written separately for human
    inspection.

    Phase B (M3B-α) adds ``rubric_evaluations`` and ``property_check_results``
    as siblings to ``comparative_judgment``. Both default to empty lists so
    pre-M3B-α ``report.json`` files continue to deserialize cleanly.
    """

    __test__ = False  # tell pytest this is not a test class

    test_case: TestCase
    raw_prompt: str
    refined_prompt: str
    problem_state_path: str | None = None
    raw_answer: str
    refined_answer: str
    comparative_judgment: ComparativeJudgment | None = None
    # M3B-β.1: whether the M3A answer-comparison lens applied to this case (False when
    # skipped by formulation-type policy / CLI override). Defaulted True so pre-β.1
    # report.json deserializes unchanged. A False value means the answer lens was
    # intentionally not run — NOT that the case is error-free (see errors[]).
    answer_comparison_applicable: bool = True
    errors: list[str] = Field(default_factory=list)
    timing: dict[str, float] = Field(default_factory=dict)
    rubric_evaluations: list[AbsoluteRubricEvaluation] = Field(default_factory=list)
    property_check_results: list[PropertyCheckResult] = Field(default_factory=list)


class AggregateMetrics(BaseModel):
    """Three-way scoreboard plus material-improvement and degradation rates.

    Rates are computed over ``n_completed``, not ``n_cases``, so errored cases
    do not silently depress the win rate.

    M3B-β.1: the answer-lens buckets are mutually exclusive —
    ``n_cases == n_completed + n_errored + n_answer_skipped``. ``n_answer_skipped``
    counts cases whose formulation type (or the CLI override) made the M3A
    answer-comparison lens not applicable; it is decided by answer-lens status only
    and is independent of ``errors[]`` (a skipped case may still carry PF/rubric/
    property errors). Defaults to 0 so pre-β.1 report.json parses unchanged.
    """

    n_cases: int
    n_completed: int
    n_errored: int
    n_answer_skipped: int = 0
    n_refined_wins: int
    n_raw_wins: int
    n_ties: int
    refined_win_rate: float | None
    raw_win_rate: float | None
    tie_rate: float | None
    material_improvement_rate: float | None
    degradation_rate: float | None


class AggregateRuntime(BaseModel):
    """Per-role wall-clock totals across all benchmark cases.

    Built by summing each contributing key from per-case ``TestCaseResult.timing``:
    PF ← ``pf_run``; Answer ← ``raw_answer`` + ``refined_answer``;
    Judge ← ``judge``; Rubric ← ``rubric``; Property ← ``property``. ``judge`` is
    the M3A comparative lens only; the rubric and property lenses (M3B) are
    tracked separately so ``total_seconds`` reconciles without merging the lenses.
    Errored cases contribute whatever partial timing they captured — time spent
    is a measurement signal even when the case ultimately errored.

    ``rubric_seconds`` / ``property_seconds`` default to ``0.0`` so pre-M3B-α.4
    ``report.json`` files (which lack them) continue to deserialize cleanly.
    """

    total_seconds: float = 0.0
    pf_seconds: float = 0.0
    answer_seconds: float = 0.0
    judge_seconds: float = 0.0
    rubric_seconds: float = 0.0
    property_seconds: float = 0.0


class RubricAggregate(BaseModel):
    """Per-rubric mean absolute-score and raw-vs-refined delta across cases.

    Defined narrowly for M3B-α: enough to populate the headline raw/refined
    means and the delta the report renders. Per-criterion mean deltas and
    other slicing can be added in M3B-β as the report grows.
    """

    rubric_name: str
    target: EvalTarget
    n_cases: int
    raw_mean_aggregate: float | None
    refined_mean_aggregate: float | None
    mean_delta: float | None              # refined_mean - raw_mean


class PropertyAggregate(BaseModel):
    """Per-property pass-rate aggregation.

    For M3B-α, each property carries a single ``target``; pass rates are
    surfaced separately for raw vs refined subjects so a property can show
    refinement-induced regressions or improvements at a glance.
    """

    property_name: str
    target: EvalTarget
    n_applied: int                        # number of cases the property was evaluated against
    raw_pass_rate: float | None
    refined_pass_rate: float | None


class BenchmarkReport(BaseModel):
    run_id: str
    started_at: datetime
    finished_at: datetime
    config: dict
    bias_warnings: list[str] = Field(default_factory=list)
    test_case_results: list[TestCaseResult] = Field(default_factory=list)
    aggregate: AggregateMetrics
    aggregate_runtime: AggregateRuntime = Field(default_factory=AggregateRuntime)
    aggregate_rubrics: dict[str, RubricAggregate] = Field(default_factory=dict)
    aggregate_properties: dict[str, PropertyAggregate] = Field(default_factory=dict)
    schema_version: int = 1
