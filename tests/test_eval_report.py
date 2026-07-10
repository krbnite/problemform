from datetime import datetime
from pathlib import Path

from problemform.eval.models import (
    AbsoluteRubricEvaluation, AggregateMetrics, BenchmarkReport, ComparativeJudgment,
    CriterionScore, PropertyAggregate, RubricAggregate, TestCase, TestCaseResult,
)
from problemform.eval.report import render_markdown, write_run


def _one_completed_agg() -> AggregateMetrics:
    return AggregateMetrics(
        n_cases=1, n_completed=1, n_errored=0,
        n_refined_wins=1, n_raw_wins=0, n_ties=0,
        refined_win_rate=1.0, raw_win_rate=0.0, tie_rate=0.0,
        material_improvement_rate=1.0, degradation_rate=0.0,
    )


def _abs_eval(rubric_name, subject, score, target="formulation"):
    return AbsoluteRubricEvaluation(
        rubric_name=rubric_name, target=target, subject=subject,
        criterion_scores=[CriterionScore(criterion_name="c", score=score,
                                         raw_score=int(round(score * 4)), rationale="r")],
        aggregate_score=score,
    )


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
        test_case=TestCase(name=name, category=category, raw_formulation="q"),
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


def test_runtime_section_present_with_per_role_totals():
    """`render_markdown` includes a `## Runtime` section with the per-role
    breakdown and a Total row formatted via `format_seconds`."""
    from problemform.eval.models import AggregateRuntime
    from problemform.eval.report import format_seconds

    agg = AggregateMetrics(
        n_cases=1, n_completed=1, n_errored=0,
        n_refined_wins=1, n_raw_wins=0, n_ties=0,
        refined_win_rate=1.0, raw_win_rate=0.0, tie_rate=0.0,
        material_improvement_rate=1.0, degradation_rate=0.0,
    )
    report = _report([_result("c1", "philosophy", judgment=_judgment())], agg)
    report = report.model_copy(update={
        "aggregate_runtime": AggregateRuntime(
            total_seconds=552.0,   # 9m 12s
            pf_seconds=552.0 - 167.0 - 159.0 - 40.0 - 20.0,
            answer_seconds=167.0,
            judge_seconds=159.0,
            rubric_seconds=40.0,
            property_seconds=20.0,
        ),
    })
    md = render_markdown(report)
    assert "## Runtime" in md
    assert "ProblemForm refinement" in md
    assert "Answer generation" in md
    assert "Comparative judge" in md
    assert "Rubric evaluation" in md
    assert "Property checks" in md
    assert format_seconds(552.0) in md  # total row uses format_seconds
    # Runtime section appears before the per-case results table.
    assert md.index("## Runtime") < md.index("## Per-case results")


def test_format_seconds_formats_under_and_over_one_minute():
    from problemform.eval.report import format_seconds

    assert format_seconds(0.0) == "0.0s"
    assert format_seconds(42.7) == "42.7s"
    assert format_seconds(60.0) == "1m 00s"
    assert format_seconds(552.0) == "9m 12s"


# --- M3B-α.4 report sections -------------------------------------------------


def test_rubric_and_property_sections_render_with_values():
    report = _report([_result("c1", "philosophy", judgment=_judgment())],
                     _one_completed_agg())
    report = report.model_copy(update={
        "aggregate_rubrics": {
            "formulation_quality_v1": RubricAggregate(
                rubric_name="formulation_quality_v1", target="formulation",
                n_cases=1, raw_mean_aggregate=0.50, refined_mean_aggregate=0.80,
                mean_delta=0.30),
        },
        "aggregate_properties": {
            "addresses_stated_request": PropertyAggregate(
                property_name="addresses_stated_request", target="artifact",
                n_applied=1, raw_pass_rate=1.0, refined_pass_rate=1.0),
        },
    })
    md = render_markdown(report)
    assert "## Rubric evaluations" in md
    assert "## Property checks" in md
    assert "## Disagreement diagnostic" in md
    # Rubric row values render (raw/refined means + signed delta).
    assert "formulation_quality_v1" in md
    assert "0.50" in md and "0.80" in md and "+0.30" in md
    # Property pass rate renders as a percentage.
    assert "addresses_stated_request" in md and "100%" in md
    # Lenses stay separate: three distinct section headers, no merged score.
    assert md.index("## Rubric evaluations") < md.index("## Property checks")
    assert md.index("## Property checks") < md.index("## Disagreement diagnostic")
    # New sections sit between Runtime and Per-case results.
    assert md.index("## Rubric evaluations") < md.index("## Per-case results")


def test_rubric_property_sections_empty_when_absent():
    md = render_markdown(_report([_result("c1", "philosophy", judgment=_judgment())],
                                 _one_completed_agg()))
    assert "_No rubrics applied in this run._" in md
    assert "_No property checks applied in this run._" in md


def _case_with_formulation_eval(name, judgment, raw_score, refined_score):
    return TestCaseResult(
        test_case=TestCase(name=name, category="cat", raw_formulation="q"),
        raw_prompt="q", refined_prompt="q-refined",
        raw_answer="RAW", refined_answer="REFINED",
        comparative_judgment=judgment,
        rubric_evaluations=[
            _abs_eval("formulation_quality_v1", "raw", raw_score),
            _abs_eval("formulation_quality_v1", "refined", refined_score),
        ],
    )


def test_disagreement_flags_material_answer_win_with_flat_formulation():
    """P2: M3A says refined material-win, but the formulation barely moved."""
    j = _judgment(winner_actual="refined", materiality="material")
    case = _case_with_formulation_eval("c1", j, raw_score=0.80, refined_score=0.82)  # Δ=+0.02
    md = render_markdown(_report([case], _one_completed_agg()))
    assert "_No disagreements flagged in this run._" not in md
    assert "P2" in md
    assert "`c1`" not in md  # rendered in a table cell without backticks
    assert "c1" in md
    assert "+0.02" in md


def test_disagreement_none_when_lenses_agree():
    """Large formulation gain accompanying a material answer win is not a disagreement."""
    j = _judgment(winner_actual="refined", materiality="material")
    case = _case_with_formulation_eval("c1", j, raw_score=0.50, refined_score=0.90)  # Δ=+0.40
    md = render_markdown(_report([case], _one_completed_agg()))
    assert "_No disagreements flagged in this run._" in md


def test_disagreement_flags_tie_with_large_formulation_gain():
    """P3: M3A ties on the answer, but the formulation improved a lot."""
    j = _judgment(winner_actual="tie", materiality="stylistic_only")
    case = _case_with_formulation_eval("c1", j, raw_score=0.40, refined_score=0.80)  # Δ=+0.40
    md = render_markdown(_report([case], _one_completed_agg()))
    assert "P3" in md


# --- M3B-β.1: answer-lens skip rendering ------------------------------------


def _tcr(**overrides):
    base = dict(
        test_case=TestCase(name="a", category="cat", raw_formulation="x"),
        raw_prompt="x", refined_prompt="x", raw_answer="", refined_answer="",
        comparative_judgment=None,
    )
    base.update(overrides)
    return TestCaseResult(**base)


def test_per_case_winner_materiality_matrix():
    from problemform.eval.report import _per_case_winner_materiality
    skipped_clean = _tcr(answer_comparison_applicable=False)
    skipped_err = _tcr(answer_comparison_applicable=False, errors=["rubric x failed"])
    applicable_failed = _tcr(answer_comparison_applicable=True)  # judgment None
    applicable_done = _tcr(answer_comparison_applicable=True,
                           comparative_judgment=_judgment("refined", "material"))
    assert _per_case_winner_materiality(skipped_clean) == ("skipped", "—")
    assert _per_case_winner_materiality(skipped_err) == ("skipped", "errored")
    assert _per_case_winner_materiality(applicable_failed) == ("—", "errored")
    assert _per_case_winner_materiality(applicable_done) == ("refined", "material")


def test_headline_annotates_skips_and_degrades_when_all_skipped():
    agg = AggregateMetrics(
        n_cases=2, n_completed=0, n_errored=0, n_answer_skipped=2,
        n_refined_wins=0, n_raw_wins=0, n_ties=0,
        refined_win_rate=None, raw_win_rate=None, tie_rate=None,
        material_improvement_rate=None, degradation_rate=None,
    )
    md = render_markdown(_report([], agg))
    assert "Answer comparison skipped:** 2" in md
    assert "answer-skipped: 2" in md              # sample line
    assert "n/a" in md                             # M3A rates degrade
    assert "Rubric evaluations" in md              # degrade note points to the rubric lens
