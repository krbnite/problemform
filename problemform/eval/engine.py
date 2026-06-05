"""Per-test-case evaluation pipeline.

Phase A workflow per case:
    1. Run ProblemForm once on the raw question.
    2. Generate raw_answer = answer_provider.generate_text(raw_question).
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
import time
from datetime import datetime, timezone
from pathlib import Path

from problemform.core.language_models import LLMProvider
from problemform.core.workflow import run as pf_run
from problemform.eval.judges import judge_answers
from problemform.eval.models import (
    AggregateMetrics,
    BenchmarkReport,
    TestCase,
    TestCaseResult,
)


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


def _run_one_case(
    case: TestCase,
    pf_provider: LLMProvider,
    answer_provider: LLMProvider,
    judge_provider: LLMProvider,
    *,
    max_iterations: int,
    case_dir: Path,
    rng: random.Random,
) -> TestCaseResult:
    """Execute the per-case pipeline. Errors are captured, not raised."""
    timing: dict[str, float] = {}
    errors: list[str] = []
    refined_prompt = case.raw_question  # fallback if PF fails
    raw_answer = ""
    refined_answer = ""
    judgment = None
    problem_state_path: str | None = None

    case_dir.mkdir(parents=True, exist_ok=True)

    try:
        t0 = time.time()
        state = pf_run(case.raw_question, pf_provider, max_iterations=max_iterations)
        timing["pf_run"] = time.time() - t0
        refined_prompt = state.final_prompt or case.raw_question
        ps_path = case_dir / "problem_state.json"
        ps_path.write_text(state.model_dump_json(indent=2))
        problem_state_path = str(ps_path.relative_to(case_dir.parent.parent))
    except Exception as exc:
        errors.append(f"problemform.run failed: {type(exc).__name__}: {exc}")

    try:
        t0 = time.time()
        raw_answer = answer_provider.generate_text(case.raw_question)
        timing["raw_answer"] = time.time() - t0
        (case_dir / "raw_answer.txt").write_text(raw_answer)
    except Exception as exc:
        errors.append(f"raw answer generation failed: {type(exc).__name__}: {exc}")

    try:
        t0 = time.time()
        refined_answer = answer_provider.generate_text(refined_prompt)
        timing["refined_answer"] = time.time() - t0
        (case_dir / "refined_answer.txt").write_text(refined_answer)
    except Exception as exc:
        errors.append(f"refined answer generation failed: {type(exc).__name__}: {exc}")

    if not errors:
        try:
            t0 = time.time()
            judgment = judge_answers(
                judge_provider, case.raw_question, raw_answer, refined_answer, rng=rng
            )
            timing["judge"] = time.time() - t0
        except Exception as exc:
            errors.append(f"judge failed: {type(exc).__name__}: {exc}")

    return TestCaseResult(
        test_case=case,
        raw_prompt=case.raw_question,
        refined_prompt=refined_prompt,
        problem_state_path=problem_state_path,
        raw_answer=raw_answer,
        refined_answer=refined_answer,
        comparative_judgment=judgment,
        errors=errors,
        timing=timing,
    )


def _aggregate(results: list[TestCaseResult]) -> AggregateMetrics:
    n_cases = len(results)
    completed = [r for r in results if r.comparative_judgment is not None and not r.errors]
    n_completed = len(completed)
    n_errored = n_cases - n_completed

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
        n_refined_wins=n_refined_wins,
        n_raw_wins=n_raw_wins,
        n_ties=n_ties,
        refined_win_rate=rate(n_refined_wins),
        raw_win_rate=rate(n_raw_wins),
        tie_rate=rate(n_ties),
        material_improvement_rate=rate(material_improvements),
        degradation_rate=rate(degradations),
    )


def run_benchmark(
    cases: list[TestCase],
    pf_provider: LLMProvider,
    answer_provider: LLMProvider,
    judge_provider: LLMProvider,
    *,
    output_dir: Path,
    max_iterations: int = 1,
    config: dict | None = None,
    bias_warnings: list[str] | None = None,
    rng: random.Random | None = None,
) -> BenchmarkReport:
    """Run the full benchmark pipeline over ``cases``.

    Writes per-case artifacts under ``output_dir/cases/<case_name>/`` and
    aggregates a ``BenchmarkReport`` at the end. The report is returned but
    NOT written here; callers (typically the CLI) handle ``report.json`` /
    ``report.md`` persistence.
    """
    rng = rng or random.Random()
    started_at = _now()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cases_dir = output_dir / "cases"

    results: list[TestCaseResult] = []
    for case in cases:
        case_dir = cases_dir / case.name
        result = _run_one_case(
            case, pf_provider, answer_provider, judge_provider,
            max_iterations=max_iterations,
            case_dir=case_dir,
            rng=rng,
        )
        results.append(result)

    finished_at = _now()
    return BenchmarkReport(
        run_id=_make_run_id(started_at),
        started_at=started_at,
        finished_at=finished_at,
        config=config or {},
        bias_warnings=bias_warnings or [],
        test_case_results=results,
        aggregate=_aggregate(results),
    )
