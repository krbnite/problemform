from datetime import datetime
from pathlib import Path

from problemform.eval.models import (
    AggregateMetrics, BenchmarkReport, ComparativeJudgment, TestCase, TestCaseResult,
)
from problemform.eval.report import render_markdown, write_run


def _judgment(winner_actual="refined", materiality="material"):
    return ComparativeJudgment(
        target="answer",
        presented_first_actual="raw",
        winner="b",
        winner_actual=winner_actual,
        materiality=materiality,
        rationale="rationale text",
        key_differences=["diff1", "diff2"],
    )


def _result(name, category, judgment=None, errors=None,
            raw_answer="RAW_TEXT_INLINE", refined_answer="REFINED_TEXT_INLINE"):
    return TestCaseResult(
        test_case=TestCase(name=name, category=category, raw_question="q"),
        raw_prompt="q",
        refined_prompt="q-refined",
        raw_answer=raw_answer,
        refined_answer=refined_answer,
        comparative_judgment=judgment,
        errors=errors or [],
    )


def _report(results, aggregate, bias_warnings=None):
    now = datetime(2026, 6, 4, 16, 12, 0)
    return BenchmarkReport(
        run_id="2026-06-04T16-12-00_a1b2c3",
        started_at=now, finished_at=now,
        config={
            "pf_provider": "openai", "pf_model": "gpt-5.4",
            "answer_provider": "openai", "answer_model": "gpt-5.4",
            "judge_provider": "anthropic", "judge_model": "claude-sonnet-4-6",
            "max_iterations": 1, "position_randomized": True,
        },
        bias_warnings=bias_warnings or [],
        test_case_results=results,
        aggregate=aggregate,
    )


def test_headline_surfaces_all_five_rates():
    """The headline must show refined, raw, ties, material, and degradation rates side-by-side."""
    agg = AggregateMetrics(
        n_cases=5, n_completed=5, n_errored=0,
        n_refined_wins=3, n_raw_wins=1, n_ties=1,
        refined_win_rate=0.6, raw_win_rate=0.2, tie_rate=0.2,
        material_improvement_rate=0.4, degradation_rate=0.0,
    )
    report = _report([], agg)
    md = render_markdown(report)
    assert "Refined wins" in md
    assert "Raw wins" in md
    assert "Ties" in md
    assert "Material improvement rate" in md
    assert "Degradation rate" in md
    assert "60%" in md and "20%" in md and "40%" in md


def test_markdown_has_all_required_sections():
    agg = AggregateMetrics(
        n_cases=1, n_completed=1, n_errored=0,
        n_refined_wins=1, n_raw_wins=0, n_ties=0,
        refined_win_rate=1.0, raw_win_rate=0.0, tie_rate=0.0,
        material_improvement_rate=1.0, degradation_rate=0.0,
    )
    md = render_markdown(_report([_result("c1", "philosophy", judgment=_judgment())], agg))
    for section in ["# Benchmark Report", "## Headline", "## Configuration",
                    "## Per-case results", "## Cases where refined was worse than raw",
                    "## Errors"]:
        assert section in md


def test_diagnostic_section_populated_when_raw_wins():
    j = _judgment(winner_actual="raw", materiality="minor")
    agg = AggregateMetrics(
        n_cases=1, n_completed=1, n_errored=0,
        n_refined_wins=0, n_raw_wins=1, n_ties=0,
        refined_win_rate=0.0, raw_win_rate=1.0, tie_rate=0.0,
        material_improvement_rate=0.0, degradation_rate=0.0,
    )
    md = render_markdown(_report([_result("c1", "control", judgment=j)], agg))
    assert "Cases where refined was worse than raw" in md
    assert "`c1`" in md
    assert "rationale text" in md
    assert "diff1" in md
    assert "_None in this run._" not in md


def test_diagnostic_section_says_none_when_clean():
    j = _judgment(winner_actual="refined", materiality="material")
    agg = AggregateMetrics(
        n_cases=1, n_completed=1, n_errored=0,
        n_refined_wins=1, n_raw_wins=0, n_ties=0,
        refined_win_rate=1.0, raw_win_rate=0.0, tie_rate=0.0,
        material_improvement_rate=1.0, degradation_rate=0.0,
    )
    md = render_markdown(_report([_result("c1", "philosophy", judgment=j)], agg))
    assert "_None in this run._" in md


def test_errors_section_lists_errored_cases():
    bad = _result("badcase", "control", judgment=None, errors=["judge failed: stub"])
    agg = AggregateMetrics(
        n_cases=1, n_completed=0, n_errored=1,
        n_refined_wins=0, n_raw_wins=0, n_ties=0,
        refined_win_rate=None, raw_win_rate=None, tie_rate=None,
        material_improvement_rate=None, degradation_rate=None,
    )
    md = render_markdown(_report([bad], agg))
    assert "`badcase`" in md
    assert "judge failed: stub" in md


def test_bias_warnings_surfaced_in_config_block():
    agg = AggregateMetrics(
        n_cases=0, n_completed=0, n_errored=0,
        n_refined_wins=0, n_raw_wins=0, n_ties=0,
        refined_win_rate=None, raw_win_rate=None, tie_rate=None,
        material_improvement_rate=None, degradation_rate=None,
    )
    md = render_markdown(_report([], agg, bias_warnings=["self-preference bias is likely"]))
    assert "Bias warnings" in md
    assert "self-preference" in md


def test_report_json_round_trips_with_inline_answer_text(tmp_path: Path):
    """report.json must be self-contained: inline answer text round-trips."""
    j = _judgment()
    agg = AggregateMetrics(
        n_cases=1, n_completed=1, n_errored=0,
        n_refined_wins=1, n_raw_wins=0, n_ties=0,
        refined_win_rate=1.0, raw_win_rate=0.0, tie_rate=0.0,
        material_improvement_rate=1.0, degradation_rate=0.0,
    )
    report = _report([_result("c1", "philosophy", judgment=j)], agg)
    write_run(report, tmp_path)
    assert (tmp_path / "report.json").exists()
    assert (tmp_path / "report.md").exists()
    again = BenchmarkReport.model_validate_json((tmp_path / "report.json").read_text())
    assert again == report
    # Inline answer text is present in the report's case results.
    assert again.test_case_results[0].raw_answer == "RAW_TEXT_INLINE"
    assert again.test_case_results[0].refined_answer == "REFINED_TEXT_INLINE"
