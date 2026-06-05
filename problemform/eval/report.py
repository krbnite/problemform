"""Benchmark report rendering: JSON + Markdown.

The Markdown report is deliberately structured so the headline cannot be read
without simultaneously seeing the raw-win rate and degradation rate. See
``docs/designs/milestone_03_evaluation_framework.md`` Section 8.
"""

from __future__ import annotations

from pathlib import Path

from problemform.eval.models import BenchmarkReport, TestCaseResult


def write_run(report: BenchmarkReport, run_dir: Path) -> None:
    """Persist ``report.json`` and ``report.md`` under ``run_dir``."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.json").write_text(report.model_dump_json(indent=2))
    (run_dir / "report.md").write_text(render_markdown(report))


def _fmt_pct(rate: float | None) -> str:
    return f"{rate * 100:.0f}%" if rate is not None else "n/a"


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


def render_markdown(report: BenchmarkReport) -> str:
    """Render the full benchmark report as Markdown."""
    return "\n\n".join([
        _headline(report),
        _config_block(report),
        _per_case_table(report),
        _diagnostic_section(report),
        _errors_section(report),
    ]) + "\n"
