"""Benchmark report rendering: JSON + Markdown.

The Markdown report is deliberately structured so the headline cannot be read
without simultaneously seeing the raw-win rate and degradation rate. See
``docs/designs/milestone_03_evaluation_framework.md`` Section 8.
"""

from __future__ import annotations

from pathlib import Path

from problemform.eval.models import BenchmarkReport, ComparativeJudgment, TestCaseResult


# Disagreement-diagnostic thresholds (M3B-α.4). Named so calibration can adjust
# them later. EPS_TIE: a formulation-rubric delta at or below this counts as
# "flat/negative". LARGE_DELTA: at or above this counts as a "large" formulation
# gain. See docs/designs/milestone_03b_rubrics_and_properties.md.
EPS_TIE = 0.05
LARGE_DELTA = 0.15


def write_run(report: BenchmarkReport, run_dir: Path) -> None:
    """Persist ``report.json`` and ``report.md`` under ``run_dir``."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.json").write_text(report.model_dump_json(indent=2))
    (run_dir / "report.md").write_text(render_markdown(report))


def _fmt_pct(rate: float | None) -> str:
    return f"{rate * 100:.0f}%" if rate is not None else "n/a"


def _fmt_score(v: float | None) -> str:
    return f"{v:.2f}" if v is not None else "n/a"


def _fmt_delta(v: float | None) -> str:
    return f"{v:+.2f}" if v is not None else "n/a"


def format_seconds(s: float) -> str:
    """Render a wall-clock duration as ``Xm YYs`` (≥60s) or ``Y.Ys`` (<60s).

    Shared by the CLI's per-case timing table, the CLI's run-level headline,
    and the ``## Runtime`` section in :func:`render_markdown`.
    """
    if s >= 60:
        m, sec = divmod(int(round(s)), 60)
        return f"{m}m {sec:02d}s"
    return f"{s:.1f}s"


def _headline(report: BenchmarkReport) -> str:
    agg = report.aggregate
    lines = [
        "# Benchmark Report",
        "",
        f"**Run ID:** `{report.run_id}`",
        f"**Started:** {report.started_at.isoformat()}",
        f"**Finished:** {report.finished_at.isoformat()}",
        "",
        "## Headline",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Refined wins | **{_fmt_pct(agg.refined_win_rate)}** ({agg.n_refined_wins}/{agg.n_completed}) |",
        f"| Raw wins | **{_fmt_pct(agg.raw_win_rate)}** ({agg.n_raw_wins}/{agg.n_completed}) |",
        f"| Ties | **{_fmt_pct(agg.tie_rate)}** ({agg.n_ties}/{agg.n_completed}) |",
        f"| Material improvement rate | **{_fmt_pct(agg.material_improvement_rate)}** |",
        f"| Degradation rate | **{_fmt_pct(agg.degradation_rate)}** |",
        "",
        f"**Sample:** n={agg.n_cases} (completed: {agg.n_completed}, errored: {agg.n_errored}).",
        "**Caveats:** K=1; sample size likely below any statistical significance threshold.",
    ]
    return "\n".join(lines)


def _config_block(report: BenchmarkReport) -> str:
    cfg = report.config or {}
    lines = ["## Configuration", "", "| Role | Provider | Model |", "|---|---|---|"]
    for role, label in [("pf", "ProblemForm"), ("answer", "Answer"), ("judge", "Judge")]:
        p = cfg.get(f"{role}_provider", "?")
        m = cfg.get(f"{role}_model", "?")
        lines.append(f"| {label} | {p} | {m} |")
    lines += [
        "",
        f"**max_iterations:** {cfg.get('max_iterations', 'n/a')}",
        f"**Position randomized:** {'yes' if cfg.get('position_randomized', True) else 'no'}",
        f"**Judgments per pair (K):** {cfg.get('judgments_per_pair', 1)}",
    ]
    if report.bias_warnings:
        lines.append("")
        lines.append("**Bias warnings:**")
        for w in report.bias_warnings:
            lines.append(f"- {w}")
    return "\n".join(lines)


def _runtime_section(report: BenchmarkReport) -> str:
    """Render per-role wall-clock totals for the benchmark run."""
    rt = report.aggregate_runtime
    return "\n".join([
        "## Runtime",
        "",
        "| Role | Total |",
        "|---|---|",
        f"| ProblemForm refinement | {format_seconds(rt.pf_seconds)} |",
        f"| Answer generation | {format_seconds(rt.answer_seconds)} |",
        f"| Comparative judge | {format_seconds(rt.judge_seconds)} |",
        f"| Rubric evaluation | {format_seconds(rt.rubric_seconds)} |",
        f"| Property checks | {format_seconds(rt.property_seconds)} |",
        f"| **Total** | **{format_seconds(rt.total_seconds)}** |",
    ])


def _per_case_table(report: BenchmarkReport) -> str:
    lines = [
        "## Per-case results",
        "",
        "| Case | Category | Winner | Materiality |",
        "|---|---|---|---|",
    ]
    for r in report.test_case_results:
        if r.comparative_judgment is not None:
            w = r.comparative_judgment.winner_actual
            m = r.comparative_judgment.materiality
        else:
            w, m = "—", "errored"
        lines.append(f"| {r.test_case.name} | {r.test_case.category} | {w} | {m} |")
    return "\n".join(lines)


def _diagnostic_section(report: BenchmarkReport) -> str:
    """Cases where refined was worse than raw (or substantively degraded).

    This section is deliberately prominent. A benchmark that hides its
    regressions is an advocacy artifact, not a measurement instrument.
    """
    diagnostic_cases: list[TestCaseResult] = [
        r for r in report.test_case_results
        if r.comparative_judgment is not None
        and (
            r.comparative_judgment.winner_actual == "raw"
            or r.comparative_judgment.materiality == "degradation"
        )
    ]
    lines = ["## Cases where refined was worse than raw", ""]
    if not diagnostic_cases:
        lines.append("_None in this run._")
        return "\n".join(lines)
    for r in diagnostic_cases:
        j = r.comparative_judgment
        assert j is not None
        lines += [
            f"### `{r.test_case.name}` ({r.test_case.category})",
            "",
            f"- **Winner:** {j.winner_actual}  |  **Materiality:** {j.materiality}",
            f"- **Judge rationale:** {j.rationale}",
            "",
        ]
        if j.key_differences:
            lines.append("**Key differences:**")
            for d in j.key_differences:
                lines.append(f"- {d}")
            lines.append("")
    return "\n".join(lines)


def _errors_section(report: BenchmarkReport) -> str:
    errored = [r for r in report.test_case_results if r.errors]
    lines = ["## Errors", ""]
    if not errored:
        lines.append("_None._")
        return "\n".join(lines)
    for r in errored:
        lines.append(f"### `{r.test_case.name}`")
        lines.append("")
        for e in r.errors:
            lines.append(f"- {e}")
        lines.append("")
    return "\n".join(lines)


def _rubric_evaluations_section(report: BenchmarkReport) -> str:
    """Per-rubric raw/refined absolute-score means and their delta.

    One of the three parallel lenses. Reported on its own axis; never merged with
    the M3A comparative verdict or the property lens into a single score.
    """
    lines = ["## Rubric evaluations", ""]
    if not report.aggregate_rubrics:
        lines.append("_No rubrics applied in this run._")
        return "\n".join(lines)
    lines += [
        "| Rubric | Target | Raw mean | Refined mean | Δ (refined − raw) | n |",
        "|---|---|---|---|---|---|",
    ]
    for name, agg in report.aggregate_rubrics.items():
        lines.append(
            f"| {name} | {agg.target} | {_fmt_score(agg.raw_mean_aggregate)} "
            f"| {_fmt_score(agg.refined_mean_aggregate)} | {_fmt_delta(agg.mean_delta)} "
            f"| {agg.n_cases} |"
        )
    return "\n".join(lines)


def _property_checks_section(report: BenchmarkReport) -> str:
    """Per-property raw/refined pass rates.

    Binary regression signal, one row per property. No weighted "overall property
    score" — each property is independently meaningful.
    """
    lines = ["## Property checks", ""]
    if not report.aggregate_properties:
        lines.append("_No property checks applied in this run._")
        return "\n".join(lines)
    lines += [
        "| Property | Target | Raw pass | Refined pass | n |",
        "|---|---|---|---|---|",
    ]
    for name, agg in report.aggregate_properties.items():
        lines.append(
            f"| {name} | {agg.target} | {_fmt_pct(agg.raw_pass_rate)} "
            f"| {_fmt_pct(agg.refined_pass_rate)} | {agg.n_applied} |"
        )
    return "\n".join(lines)


def _formulation_deltas(r: TestCaseResult) -> dict[str, float]:
    """Per formulation-target rubric: this case's ``refined − raw`` aggregate delta.

    Only rubrics with both a raw and a refined evaluation contribute.
    """
    by_rubric: dict[str, dict[str, float]] = {}
    for ev in r.rubric_evaluations:
        if ev.target != "formulation":
            continue
        by_rubric.setdefault(ev.rubric_name, {})[ev.subject] = ev.aggregate_score
    return {
        name: subs["refined"] - subs["raw"]
        for name, subs in by_rubric.items()
        if "raw" in subs and "refined" in subs
    }


def _classify_disagreement(j: ComparativeJudgment, delta: float) -> str | None:
    """Classify M3A-vs-formulation disagreement into one of three patterns.

    The formulation-rubric delta is compared against the M3A answer verdict.
    Artifact-target rubrics are excluded by the caller — they measure the same
    axis as M3A, so disagreement there is not the high-value signal here.
    """
    material_refined = j.winner_actual == "refined" and j.materiality == "material"
    if material_refined and delta <= EPS_TIE:
        return "P2 · answer material-win, formulation flat/negative"
    if material_refined and EPS_TIE < delta < LARGE_DELTA:
        return "P1 · answer material-win, small formulation gain"
    if j.winner_actual == "tie" and delta >= LARGE_DELTA:
        return "P3 · answer tie, large formulation gain"
    return None


def _disagreement_diagnostic_section(report: BenchmarkReport) -> str:
    """Cases where the M3A answer verdict and the formulation-rubric delta diverge.

    The high-diagnostic-value section per the design doc: the two lenses are
    reported side by side so a human can see the mismatch. They are never merged
    into a single number.
    """
    lines = [
        "## Disagreement diagnostic",
        "",
        "_Cases where the M3A answer verdict and the formulation-rubric delta "
        "point in different directions. Worth human review; the two lenses are "
        "shown side by side, never merged._",
        "",
    ]
    flagged: list[tuple[TestCaseResult, str, float, str]] = []
    for r in report.test_case_results:
        j = r.comparative_judgment
        if j is None:
            continue
        for rubric_name, delta in _formulation_deltas(r).items():
            pattern = _classify_disagreement(j, delta)
            if pattern is not None:
                flagged.append((r, rubric_name, delta, pattern))

    if not flagged:
        lines.append("_No disagreements flagged in this run._")
        return "\n".join(lines)

    lines += [
        "| Case | Rubric | M3A verdict | Formulation Δ | Pattern |",
        "|---|---|---|---|---|",
    ]
    for r, rubric_name, delta, pattern in flagged:
        j = r.comparative_judgment
        assert j is not None
        verdict = f"{j.winner_actual} / {j.materiality}"
        lines.append(
            f"| {r.test_case.name} | {rubric_name} | {verdict} "
            f"| {delta:+.2f} | {pattern} |"
        )
    return "\n".join(lines)


def render_markdown(report: BenchmarkReport) -> str:
    """Render the full benchmark report as Markdown."""
    return "\n\n".join([
        _headline(report),
        _config_block(report),
        _runtime_section(report),
        _rubric_evaluations_section(report),
        _property_checks_section(report),
        _disagreement_diagnostic_section(report),
        _per_case_table(report),
        _diagnostic_section(report),
        _errors_section(report),
    ]) + "\n"
