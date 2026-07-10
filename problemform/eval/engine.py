"""Per-test-case evaluation pipeline.

Phase A workflow per case:
    1. Run ProblemForm once on the raw question.
    2. Generate raw_answer = answer_provider.generate_text(raw_formulation).
    3. Generate refined_answer = answer_provider.generate_text(refined_prompt).
    4. Run a position-randomized comparative judgment on the answer pair.
    5. Persist per-case artifacts and append a TestCaseResult.

Failure containment: any exception during steps 1–4 of a case is captured into
TestCaseResult.errors. The benchmark loop continues to the next case. Aggregate
rates compute over n_completed.

See ``docs/designs/milestone_03_evaluation_framework.md`` Section 6 for the
design rationale.
"""

from __future__ import annotations

import hashlib
import random
import re
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from problemform.core.language_models import LLMProvider
from problemform.core.workflow import run as pf_run
from problemform.eval.judges import judge_answers
from problemform.eval.models import (
    AbsoluteRubricEvaluation,
    AggregateMetrics,
    AggregateRuntime,
    BenchmarkReport,
    EvalTarget,
    PropertyAggregate,
    PropertyCheck,
    PropertyCheckResult,
    Rubric,
    RubricAggregate,
    TestCase,
    TestCaseResult,
)
from problemform.eval.policy import answer_comparison_applies
from problemform.eval.property_runner import run_property_check
from problemform.eval.rubric_runner import run_rubric


ProgressEventKind = Literal[
    "run_start",
    "case_start",
    "step",
    "case_done",
    "case_errored",
    "run_done",
]

ProgressStep = Literal[
    "problemform_refinement",
    "raw_answer",
    "refined_answer",
    "comparative_judge",
    "answer_comparison_skipped",
    "rubric_eval",
    "property_check",
]


class ProgressEvent(BaseModel):
    """Structured progress signal emitted by ``run_benchmark``.

    The engine is UI-agnostic: it emits events and lets callers (CLI, tests,
    other library consumers) decide how to render them. ``run_benchmark`` and
    ``_run_one_case`` accept an optional ``on_progress`` callback; if ``None``
    is passed (the default), no events are produced and behavior is identical
    to a call with no progress instrumentation.
    """

    kind: ProgressEventKind
    case: TestCase | None = None
    case_index: int
    total: int
    step: ProgressStep | None = None
    timing: dict[str, float] | None = None
    errors: list[str] | None = Field(default=None)


OnProgress = Callable[[ProgressEvent], None]


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _make_run_id(when: datetime) -> str:
    h = hashlib.sha256(str(when).encode()).hexdigest()[:6]
    return f"{when.strftime('%Y-%m-%dT%H-%M-%S')}_{h}"


def _detect_same_family(answer_provider_name: str, answer_model: str,
                        judge_provider_name: str, judge_model: str) -> str | None:
    """Return a warning string when answer and judge share a model family.

    Heuristic: same provider name (case-insensitive, stripped of common
    suffixes like "Provider"). Any same-provider judging risks self-preference.
    """
    def _norm(s: str) -> str:
        return s.lower().removesuffix("provider").strip()
    a = _norm(answer_provider_name)
    j = _norm(judge_provider_name)
    if a != j:
        return None
    return (
        f"answer and judge use the same provider ({a}); "
        "self-preference bias is likely. Consider using a different provider "
        "family for the judge."
    )


# --- M3B: rubric + property evaluation helpers ---------------------------
#
# α.4 wires the α.3 runners into the per-case pipeline. The three lenses (M3A
# comparative answer judgment, rubric evaluations, property checks) stay
# parallel: rubric/property failures are captured per-case but never collapse
# into the M3A verdict or into a single combined score. See
# docs/plans/m3b_alpha_4_doc01_plan_by_claude.md.

# Subject text keyed by evaluation target. Each value is (raw_text, refined_text).
Subjects = dict[EvalTarget, tuple[str, str]]


def _slug(text: str, index: int, maxlen: int = 40) -> str:
    """Derive a stable, unique property name from a free-text property string.

    Lowercases, collapses non-alphanumerics to underscores, truncates, and
    appends the source index so two differently-worded strings never collide.
    """
    base = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:maxlen].rstrip("_")
    return f"{base}_{index}" if base else f"expected_property_{index}"


def _activate_expected_properties(case: TestCase) -> list[PropertyCheck]:
    """Activate ``TestCase.expected_properties`` as runnable property checks.

    M3B-α.4 decision (option B): the current corpus ``expected_properties`` are
    predominantly formulation-shaped ("elicits the child's age", "surfaces
    latent constraints"), so each activates as ``target=formulation,
    expected=True`` — evaluated against the formulation, not the answer.
    Artifact-target coverage is retained by shared suites (e.g.
    ``artifact_baseline_v1``). See docs/plans/m3b_alpha_4_doc01_plan_by_claude.md
    item 4 and the design-doc amendment tracked in docs/backlog.md.
    """
    return [
        PropertyCheck(
            name=_slug(s, i),
            description=s,
            target="formulation",
            expected=True,
        )
        for i, s in enumerate(case.expected_properties)
    ]


def _run_rubric_both_subjects(
    rubric: Rubric, subjects: Subjects, judge_provider: LLMProvider
) -> list[AbsoluteRubricEvaluation]:
    """Score ``rubric`` against its target's raw and refined subjects.

    Skips a subject whose text is empty (e.g. an artifact-target rubric when
    answer generation failed) rather than judging an empty string.
    """
    raw_text, refined_text = subjects[rubric.target]
    out: list[AbsoluteRubricEvaluation] = []
    for label, text in (("raw", raw_text), ("refined", refined_text)):
        if text:
            out.append(run_rubric(rubric, text, label, judge_provider))
    return out


def _run_property_both_subjects(
    prop: PropertyCheck, subjects: Subjects, judge_provider: LLMProvider
) -> list[PropertyCheckResult]:
    """Evaluate ``prop`` against its target's raw and refined subjects."""
    raw_text, refined_text = subjects[prop.target]
    out: list[PropertyCheckResult] = []
    for label, text in (("raw", raw_text), ("refined", refined_text)):
        if text:
            out.append(run_property_check(prop, text, label, judge_provider))
    return out


def _run_one_case(
    case: TestCase,
    pf_provider: LLMProvider,
    answer_provider: LLMProvider | None,
    judge_provider: LLMProvider,
    *,
    max_iterations: int,
    case_dir: Path,
    rng: random.Random,
    rubrics: list[Rubric] | None = None,
    property_suites: list[PropertyCheck] | None = None,
    answer_comparison_override: bool | None = None,
    case_index: int = 0,
    total: int = 1,
    on_progress: OnProgress | None = None,
) -> TestCaseResult:
    """Execute the per-case pipeline. Errors are captured, not raised."""
    timing: dict[str, float] = {}
    errors: list[str] = []
    refined_prompt = case.raw_formulation  # fallback if PF fails
    raw_answer = ""
    refined_answer = ""
    judgment = None
    problem_state_path: str | None = None
    # M3B-β.1: does the M3A answer-comparison lens apply to this case?
    answer_applicable = answer_comparison_applies(
        case.formulation_type, override=answer_comparison_override
    )

    case_dir.mkdir(parents=True, exist_ok=True)

    def _emit(kind: ProgressEventKind, *, step: ProgressStep | None = None) -> None:
        if on_progress is None:
            return
        on_progress(ProgressEvent(
            kind=kind, case=case, case_index=case_index, total=total,
            step=step,
            timing=dict(timing) if kind in ("case_done", "case_errored") else None,
            errors=list(errors) if kind == "case_errored" else None,
        ))

    _emit("step", step="problemform_refinement")
    try:
        t0 = time.time()
        state = pf_run(case.raw_formulation, pf_provider, max_iterations=max_iterations)
        timing["pf_run"] = time.time() - t0
        refined_prompt = state.final_prompt or case.raw_formulation
        ps_path = case_dir / "problem_state.json"
        ps_path.write_text(state.model_dump_json(indent=2))
        problem_state_path = str(ps_path.relative_to(case_dir.parent.parent))
    except Exception as exc:
        errors.append(f"problemform.run failed: {type(exc).__name__}: {exc}")

    # M3A answer-comparison lens — skipped entirely for formulation-only types
    # (or when forced off via the CLI override). A skipped case generates no
    # answers, makes no judge call, and touches no answer provider.
    if answer_applicable:
        _emit("step", step="raw_answer")
        try:
            t0 = time.time()
            raw_answer = answer_provider.generate_text(case.raw_formulation)
            timing["raw_answer"] = time.time() - t0
            (case_dir / "raw_answer.txt").write_text(raw_answer)
        except Exception as exc:
            errors.append(f"raw answer generation failed: {type(exc).__name__}: {exc}")

        _emit("step", step="refined_answer")
        try:
            t0 = time.time()
            refined_answer = answer_provider.generate_text(refined_prompt)
            timing["refined_answer"] = time.time() - t0
            (case_dir / "refined_answer.txt").write_text(refined_answer)
        except Exception as exc:
            errors.append(f"refined answer generation failed: {type(exc).__name__}: {exc}")

        if not errors:
            _emit("step", step="comparative_judge")
            try:
                t0 = time.time()
                judgment = judge_answers(
                    judge_provider, case.raw_formulation, raw_answer, refined_answer, rng=rng
                )
                timing["judge"] = time.time() - t0
            except Exception as exc:
                errors.append(f"judge failed: {type(exc).__name__}: {exc}")
    else:
        # Distinct progress breadcrumb so a policy skip is not mistaken for a clean
        # M3A completion (or an error).
        _emit("step", step="answer_comparison_skipped")

    # --- M3B rubric + property lenses ---
    # Run independently of the M3A judge gate: formulation-target evaluation
    # only needs the prompts (available even if answer generation failed);
    # artifact-target evaluation is skipped per-subject when its answer is
    # empty. A rubric/property failure is recorded but does not invalidate the
    # M3A verdict (see _aggregate).
    rubric_evaluations: list[AbsoluteRubricEvaluation] = []
    property_check_results: list[PropertyCheckResult] = []
    subjects: Subjects = {
        "formulation": (case.raw_formulation, refined_prompt),
        "artifact": (raw_answer, refined_answer),
    }
    active_properties = list(property_suites or []) + _activate_expected_properties(case)

    if rubrics:
        _emit("step", step="rubric_eval")
        t0 = time.time()
        for rubric in rubrics:
            try:
                rubric_evaluations.extend(
                    _run_rubric_both_subjects(rubric, subjects, judge_provider)
                )
            except Exception as exc:
                errors.append(
                    f"rubric {rubric.name!r} failed: {type(exc).__name__}: {exc}"
                )
        timing["rubric"] = time.time() - t0

    if active_properties:
        _emit("step", step="property_check")
        t0 = time.time()
        for prop in active_properties:
            try:
                property_check_results.extend(
                    _run_property_both_subjects(prop, subjects, judge_provider)
                )
            except Exception as exc:
                errors.append(
                    f"property {prop.name!r} failed: {type(exc).__name__}: {exc}"
                )
        timing["property"] = time.time() - t0

    _emit("case_errored" if errors else "case_done")

    return TestCaseResult(
        test_case=case,
        raw_prompt=case.raw_formulation,
        refined_prompt=refined_prompt,
        problem_state_path=problem_state_path,
        raw_answer=raw_answer,
        refined_answer=refined_answer,
        comparative_judgment=judgment,
        answer_comparison_applicable=answer_applicable,
        errors=errors,
        timing=timing,
        rubric_evaluations=rubric_evaluations,
        property_check_results=property_check_results,
    )


def _aggregate_runtime(results: list[TestCaseResult]) -> AggregateRuntime:
    """Sum per-case ``timing`` into role-level totals.

    Errored cases contribute whatever partial timing they captured. Missing keys
    fall through to ``0.0`` via ``dict.get``.
    """
    pf = sum(r.timing.get("pf_run", 0.0) for r in results)
    answer = sum(
        r.timing.get("raw_answer", 0.0) + r.timing.get("refined_answer", 0.0)
        for r in results
    )
    judge = sum(r.timing.get("judge", 0.0) for r in results)
    rubric = sum(r.timing.get("rubric", 0.0) for r in results)
    prop = sum(r.timing.get("property", 0.0) for r in results)
    return AggregateRuntime(
        total_seconds=pf + answer + judge + rubric + prop,
        pf_seconds=pf,
        answer_seconds=answer,
        judge_seconds=judge,
        rubric_seconds=rubric,
        property_seconds=prop,
    )


def _aggregate(results: list[TestCaseResult]) -> AggregateMetrics:
    n_cases = len(results)
    # M3B-β.1: three mutually-exclusive answer-lens buckets, decided by answer-lens
    # status ONLY (rubric/property errors never move a case between them):
    #   n_completed      = applicable & comparative judgment present
    #   n_errored        = applicable & judgment did not complete
    #   n_answer_skipped = not applicable (formulation-only / CLI override)
    # so n_cases == n_completed + n_errored + n_answer_skipped. This preserves the
    # α.4 contract: an applicable, completed case with a rubric/property failure stays
    # n_completed (its error remains visible in errors[] / the Errors section). When
    # every case is applicable (legacy), this reduces to the prior α.4 behavior.
    applicable = [r for r in results if r.answer_comparison_applicable]
    completed = [r for r in applicable if r.comparative_judgment is not None]
    n_completed = len(completed)
    n_answer_skipped = sum(1 for r in results if not r.answer_comparison_applicable)
    n_errored = len(applicable) - n_completed

    n_refined_wins = sum(1 for r in completed if r.comparative_judgment.winner_actual == "refined")
    n_raw_wins = sum(1 for r in completed if r.comparative_judgment.winner_actual == "raw")
    n_ties = sum(1 for r in completed if r.comparative_judgment.winner_actual == "tie")

    def rate(count: int) -> float | None:
        return (count / n_completed) if n_completed else None

    material_improvements = sum(
        1 for r in completed
        if r.comparative_judgment.winner_actual == "refined"
        and r.comparative_judgment.materiality == "material"
    )
    degradations = sum(
        1 for r in completed
        if r.comparative_judgment.materiality == "degradation"
    )

    return AggregateMetrics(
        n_cases=n_cases,
        n_completed=n_completed,
        n_errored=n_errored,
        n_answer_skipped=n_answer_skipped,
        n_refined_wins=n_refined_wins,
        n_raw_wins=n_raw_wins,
        n_ties=n_ties,
        refined_win_rate=rate(n_refined_wins),
        raw_win_rate=rate(n_raw_wins),
        tie_rate=rate(n_ties),
        material_improvement_rate=rate(material_improvements),
        degradation_rate=rate(degradations),
    )


def _mean(xs: list[float]) -> float | None:
    """Arithmetic mean, or ``None`` for an empty sequence."""
    return (sum(xs) / len(xs)) if xs else None


def _aggregate_rubrics(results: list[TestCaseResult]) -> dict[str, RubricAggregate]:
    """Per-rubric raw/refined mean aggregate scores and their delta across cases.

    Groups every case's ``AbsoluteRubricEvaluation``s by ``rubric_name`` and
    splits by subject. ``mean_delta`` is ``refined_mean - raw_mean`` when both
    are present. Aggregation stays per-rubric — never collapsed across rubrics
    or with the M3A / property lenses.
    """
    by_name: dict[str, dict] = {}
    for r in results:
        for ev in r.rubric_evaluations:
            slot = by_name.setdefault(
                ev.rubric_name, {"raw": [], "refined": [], "target": ev.target}
            )
            slot[ev.subject].append(ev.aggregate_score)

    out: dict[str, RubricAggregate] = {}
    for name, slot in by_name.items():
        raw_mean = _mean(slot["raw"])
        refined_mean = _mean(slot["refined"])
        delta = (
            refined_mean - raw_mean
            if raw_mean is not None and refined_mean is not None
            else None
        )
        out[name] = RubricAggregate(
            rubric_name=name,
            target=slot["target"],
            n_cases=max(len(slot["raw"]), len(slot["refined"])),
            raw_mean_aggregate=raw_mean,
            refined_mean_aggregate=refined_mean,
            mean_delta=delta,
        )
    return out


def _aggregate_properties(results: list[TestCaseResult]) -> dict[str, PropertyAggregate]:
    """Per-property raw/refined pass rates across cases.

    Groups every case's ``PropertyCheckResult``s by ``property_name`` and splits
    by subject. Shared-suite properties (same name across cases) aggregate across
    cases; per-case activated ``expected_properties`` carry case-unique names and
    therefore aggregate over their single case. No weighted "overall property
    score" — each property is independently meaningful.
    """
    by_name: dict[str, dict] = {}
    for r in results:
        for pr in r.property_check_results:
            slot = by_name.setdefault(
                pr.property_name, {"raw": [], "refined": [], "target": pr.target}
            )
            slot[pr.subject].append(1.0 if pr.passed else 0.0)

    out: dict[str, PropertyAggregate] = {}
    for name, slot in by_name.items():
        out[name] = PropertyAggregate(
            property_name=name,
            target=slot["target"],
            n_applied=max(len(slot["raw"]), len(slot["refined"])),
            raw_pass_rate=_mean(slot["raw"]),
            refined_pass_rate=_mean(slot["refined"]),
        )
    return out


def run_benchmark(
    cases: list[TestCase],
    pf_provider: LLMProvider,
    answer_provider: LLMProvider | None,
    judge_provider: LLMProvider,
    *,
    output_dir: Path,
    max_iterations: int = 1,
    rubrics: list[Rubric] | None = None,
    property_suites: list[PropertyCheck] | None = None,
    answer_comparison_override: bool | None = None,
    config: dict | None = None,
    bias_warnings: list[str] | None = None,
    rng: random.Random | None = None,
    on_progress: OnProgress | None = None,
) -> BenchmarkReport:
    """Run the full benchmark pipeline over ``cases``.

    Writes per-case artifacts under ``output_dir/cases/<case_name>/`` and
    aggregates a ``BenchmarkReport`` at the end. The report is returned but
    NOT written here; callers (typically the CLI) handle ``report.json`` /
    ``report.md`` persistence.

    ``answer_provider`` may be ``None`` when no case will use the M3A
    answer-comparison lens (all formulation-only, or ``answer_comparison_override``
    is ``False``). If any case *is* answer-applicable while ``answer_provider`` is
    ``None``, a ``ValueError`` is raised up front — a clear error for direct-API
    callers rather than an ``AttributeError`` deep in execution.

    If ``on_progress`` is provided, structured ``ProgressEvent``s are emitted
    at run start, case start, each sub-step transition, case completion or
    error, and run completion. When ``None``, no events are produced.
    """
    if answer_provider is None and any(
        answer_comparison_applies(c.formulation_type, override=answer_comparison_override)
        for c in cases
    ):
        raise ValueError(
            "answer_provider is required: at least one case is answer-applicable "
            "under the current policy/override. Pass an answer provider, or force the "
            "answer-comparison lens off (answer_comparison_override=False)."
        )

    rng = rng or random.Random()
    started_at = _now()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cases_dir = output_dir / "cases"
    total = len(cases)

    if on_progress is not None:
        on_progress(ProgressEvent(kind="run_start", case_index=0, total=total))

    results: list[TestCaseResult] = []
    for i, case in enumerate(cases):
        if on_progress is not None:
            on_progress(ProgressEvent(
                kind="case_start", case=case, case_index=i, total=total,
            ))
        case_dir = cases_dir / case.name
        result = _run_one_case(
            case, pf_provider, answer_provider, judge_provider,
            max_iterations=max_iterations,
            case_dir=case_dir,
            rng=rng,
            rubrics=rubrics,
            property_suites=property_suites,
            answer_comparison_override=answer_comparison_override,
            case_index=i,
            total=total,
            on_progress=on_progress,
        )
        results.append(result)

    if on_progress is not None:
        on_progress(ProgressEvent(kind="run_done", case_index=total, total=total))

    finished_at = _now()
    return BenchmarkReport(
        run_id=_make_run_id(started_at),
        started_at=started_at,
        finished_at=finished_at,
        config=config or {},
        bias_warnings=bias_warnings or [],
        test_case_results=results,
        aggregate=_aggregate(results),
        aggregate_runtime=_aggregate_runtime(results),
        aggregate_rubrics=_aggregate_rubrics(results),
        aggregate_properties=_aggregate_properties(results),
    )
