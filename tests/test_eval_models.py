from datetime import datetime

import pytest

from problemform.eval.models import (
    CANONICAL_FORMULATION_TYPES,
    AggregateMetrics,
    BenchmarkReport,
    ComparativeJudgment,
    Materiality,
    TestCase,
    TestCaseResult,
)


def _judgment(**overrides):
    base = dict(
        presented_first_actual="raw",
        winner="b",
        winner_actual="refined",
        materiality="material",
        rationale="r",
        key_differences=["d1", "d2"],
    )
    base.update(overrides)
    return ComparativeJudgment(**base)


def _result(name="case1", judgment=None, errors=None):
    return TestCaseResult(
        test_case=TestCase(name=name, category="philosophy", raw_formulation="q"),
        raw_prompt="q",
        refined_prompt="q-refined",
        problem_state_path=f"cases/{name}/problem_state.json",
        raw_answer="raw answer text",
        refined_answer="refined answer text",
        comparative_judgment=judgment,
        errors=errors or [],
    )


def test_test_case_round_trips_through_json():
    tc = TestCase(
        name="cosmology_nothingness",
        category="philosophy",
        raw_formulation="why is there something rather than nothing",
        tags=["cosmology", "metaphysics"],
        expected_properties=["disambiguates 'nothing'"],
        notes="control rationale",
    )
    again = TestCase.model_validate_json(tc.model_dump_json())
    assert again == tc


# --- M3B-β.0: formulation_type ----------------------------------------------


def test_formulation_type_defaults_to_unspecified():
    tc = TestCase(name="x", category="topic", raw_formulation="…")
    assert tc.formulation_type == "unspecified"


def test_formulation_type_round_trips():
    tc = TestCase(name="x", category="topic", raw_formulation="…",
                  formulation_type="argument")
    assert TestCase.model_validate_json(tc.model_dump_json()).formulation_type == "argument"


def test_legacy_testcase_dict_without_formulation_type_parses():
    """A pre-β.0 payload (no formulation_type key) deserializes to the default."""
    tc = TestCase.model_validate(
        {"name": "x", "category": "topic", "raw_formulation": "…"}
    )
    assert tc.formulation_type == "unspecified"


def test_canonical_formulation_types_contents():
    assert CANONICAL_FORMULATION_TYPES == frozenset({
        "question", "argument", "belief", "decision", "dilemma", "explanation",
        "goal", "instruction", "plan", "prompt", "specification",
    })


@pytest.mark.parametrize("m", ["material", "minor", "stylistic_only", "degradation"])
def test_materiality_literal_accepts_all_four(m):
    j = _judgment(materiality=m)
    assert j.materiality == m


def test_comparative_judgment_round_trips():
    j = _judgment()
    assert ComparativeJudgment.model_validate_json(j.model_dump_json()) == j


def test_test_case_result_carries_inline_answer_text():
    r = _result(judgment=_judgment())
    payload = r.model_dump_json()
    assert "raw answer text" in payload
    assert "refined answer text" in payload
    again = TestCaseResult.model_validate_json(payload)
    assert again.raw_answer == "raw answer text"
    assert again.refined_answer == "refined answer text"


def test_test_case_result_supports_errored_case():
    r = _result(judgment=None, errors=["LLM provider error: stub"])
    assert r.comparative_judgment is None
    assert r.errors == ["LLM provider error: stub"]


def test_aggregate_metrics_carries_three_way_scoreboard():
    a = AggregateMetrics(
        n_cases=5,
        n_completed=4,
        n_errored=1,
        n_refined_wins=2,
        n_raw_wins=1,
        n_ties=1,
        refined_win_rate=0.5,
        raw_win_rate=0.25,
        tie_rate=0.25,
        material_improvement_rate=0.25,
        degradation_rate=0.0,
    )
    # The presence of all five rate fields is the structural insurance against
    # turning the report into an advocacy artifact.
    for field in (
        "n_refined_wins", "n_raw_wins", "n_ties",
        "refined_win_rate", "raw_win_rate", "tie_rate",
        "material_improvement_rate", "degradation_rate",
    ):
        assert hasattr(a, field)


def test_benchmark_report_round_trips():
    now = datetime(2026, 6, 4, 16, 12, 0)
    report = BenchmarkReport(
        run_id="2026-06-04T16-12-00_a1b2c3",
        started_at=now,
        finished_at=now,
        config={"pf_provider": "openai", "answer_provider": "openai", "judge_provider": "anthropic"},
        bias_warnings=[],
        test_case_results=[_result(judgment=_judgment())],
        aggregate=AggregateMetrics(
            n_cases=1, n_completed=1, n_errored=0,
            n_refined_wins=1, n_raw_wins=0, n_ties=0,
            refined_win_rate=1.0, raw_win_rate=0.0, tie_rate=0.0,
            material_improvement_rate=1.0, degradation_rate=0.0,
        ),
    )
    again = BenchmarkReport.model_validate_json(report.model_dump_json())
    assert again == report


def test_benchmark_report_round_trips_aggregate_runtime():
    """``aggregate_runtime`` round-trips through JSON and defaults to all zeros."""
    from problemform.eval.models import AggregateRuntime

    now = datetime(2026, 6, 5, 9, 0, 0)
    report = BenchmarkReport(
        run_id="2026-06-05T09-00-00_deadbe",
        started_at=now,
        finished_at=now,
        config={},
        aggregate=AggregateMetrics(
            n_cases=2, n_completed=2, n_errored=0,
            n_refined_wins=1, n_raw_wins=1, n_ties=0,
            refined_win_rate=0.5, raw_win_rate=0.5, tie_rate=0.0,
            material_improvement_rate=0.5, degradation_rate=0.0,
        ),
        aggregate_runtime=AggregateRuntime(
            total_seconds=42.5, pf_seconds=30.0, answer_seconds=8.5, judge_seconds=4.0,
        ),
    )
    again = BenchmarkReport.model_validate_json(report.model_dump_json())
    assert again.aggregate_runtime == report.aggregate_runtime

    # Older payloads without aggregate_runtime should deserialize cleanly.
    payload = report.model_dump()
    del payload["aggregate_runtime"]
    legacy = BenchmarkReport.model_validate(payload)
    assert legacy.aggregate_runtime == AggregateRuntime()  # all zeros


# --- M3B-α: rubric + property data model -----------------------------------


def test_rubric_round_trips_through_json():
    from problemform.eval.models import Rubric, RubricCriterion

    r = Rubric(
        name="formulation_quality_v1",
        description="seed formulation rubric",
        target="formulation",
        mode="absolute",
        criteria=[
            RubricCriterion(
                name="central_claim",
                description="names a central claim",
            ),
            RubricCriterion(
                name="assumption_surfacing",
                description="surfaces load-bearing assumptions",
                weight=2.0,
                scoring="graded_3",
                rationale_required=False,
            ),
        ],
        notes="seed",
    )
    again = Rubric.model_validate_json(r.model_dump_json())
    assert again == r


def test_absolute_rubric_evaluation_round_trips():
    from problemform.eval.models import (
        AbsoluteRubricEvaluation,
        CriterionScore,
    )

    e = AbsoluteRubricEvaluation(
        rubric_name="formulation_quality_v1",
        target="formulation",
        subject="refined",
        criterion_scores=[
            CriterionScore(
                criterion_name="central_claim",
                score=0.8,
                raw_score=4,
                rationale="names a clear claim",
            ),
        ],
        aggregate_score=0.8,
    )
    again = AbsoluteRubricEvaluation.model_validate_json(e.model_dump_json())
    assert again == e


def test_rubric_aggregate_round_trips_with_optional_delta():
    from problemform.eval.models import RubricAggregate

    agg = RubricAggregate(
        rubric_name="formulation_quality_v1",
        target="formulation",
        n_cases=5,
        raw_mean_aggregate=0.6,
        refined_mean_aggregate=0.78,
        mean_delta=0.18,
    )
    again = RubricAggregate.model_validate_json(agg.model_dump_json())
    assert again == agg

    # Errored / no-data case: rates and delta can be None.
    empty = RubricAggregate(
        rubric_name="formulation_quality_v1",
        target="formulation",
        n_cases=0,
        raw_mean_aggregate=None,
        refined_mean_aggregate=None,
        mean_delta=None,
    )
    assert RubricAggregate.model_validate_json(empty.model_dump_json()) == empty


def test_property_check_and_result_round_trip():
    from problemform.eval.models import PropertyCheck, PropertyCheckResult

    p = PropertyCheck(
        name="addresses_audience",
        description="answer addresses the intended audience",
        target="artifact",
    )
    again = PropertyCheck.model_validate_json(p.model_dump_json())
    assert again == p

    r = PropertyCheckResult(
        property_name="addresses_audience",
        target="artifact",
        subject="refined",
        holds=True,
        expected=True,
        passed=True,
        rationale="explicitly names the audience",
    )
    assert PropertyCheckResult.model_validate_json(r.model_dump_json()) == r


def test_property_aggregate_round_trips_with_optional_rates():
    from problemform.eval.models import PropertyAggregate

    agg = PropertyAggregate(
        property_name="addresses_audience",
        target="artifact",
        n_applied=5,
        raw_pass_rate=0.4,
        refined_pass_rate=0.8,
    )
    assert PropertyAggregate.model_validate_json(agg.model_dump_json()) == agg

    empty = PropertyAggregate(
        property_name="addresses_audience",
        target="artifact",
        n_applied=0,
        raw_pass_rate=None,
        refined_pass_rate=None,
    )
    assert PropertyAggregate.model_validate_json(empty.model_dump_json()) == empty


def test_test_case_result_defaults_new_m3b_fields_to_empty():
    """A TestCaseResult constructed without M3B fields should default both new
    sibling lists to empty, so pre-M3B-α callers and stored JSON continue to work."""
    r = _result(judgment=_judgment())
    assert r.rubric_evaluations == []
    assert r.property_check_results == []

    # Round-trip with the new fields populated.
    from problemform.eval.models import (
        AbsoluteRubricEvaluation,
        CriterionScore,
        PropertyCheckResult,
    )

    eval_ = AbsoluteRubricEvaluation(
        rubric_name="formulation_quality_v1",
        target="formulation",
        subject="refined",
        criterion_scores=[
            CriterionScore(
                criterion_name="central_claim",
                score=0.8, raw_score=4, rationale="r",
            )
        ],
        aggregate_score=0.8,
    )
    pres = PropertyCheckResult(
        property_name="x", target="artifact", subject="raw",
        holds=False, expected=True, passed=False, rationale="r",
    )
    populated = r.model_copy(update={
        "rubric_evaluations": [eval_],
        "property_check_results": [pres],
    })
    again = TestCaseResult.model_validate_json(populated.model_dump_json())
    assert again == populated


def test_benchmark_report_backward_compat_without_m3b_fields():
    """A BenchmarkReport JSON payload without the new aggregate_rubrics and
    aggregate_properties fields should still deserialize cleanly to defaults."""
    from problemform.eval.models import AggregateRuntime

    now = datetime(2026, 6, 5, 10, 0, 0)
    report = BenchmarkReport(
        run_id="2026-06-05T10-00-00_cafe00",
        started_at=now,
        finished_at=now,
        config={},
        aggregate=AggregateMetrics(
            n_cases=1, n_completed=1, n_errored=0,
            n_refined_wins=1, n_raw_wins=0, n_ties=0,
            refined_win_rate=1.0, raw_win_rate=0.0, tie_rate=0.0,
            material_improvement_rate=1.0, degradation_rate=0.0,
        ),
    )
    # Sanity: defaults are empty dicts.
    assert report.aggregate_rubrics == {}
    assert report.aggregate_properties == {}

    # Drop the new fields from the payload to simulate pre-M3B-α data.
    payload = report.model_dump()
    del payload["aggregate_rubrics"]
    del payload["aggregate_properties"]
    legacy = BenchmarkReport.model_validate(payload)
    assert legacy.aggregate_rubrics == {}
    assert legacy.aggregate_properties == {}


def test_benchmark_report_round_trips_with_m3b_aggregates():
    from problemform.eval.models import (
        PropertyAggregate,
        RubricAggregate,
    )

    now = datetime(2026, 6, 5, 11, 0, 0)
    report = BenchmarkReport(
        run_id="2026-06-05T11-00-00_beadaa",
        started_at=now,
        finished_at=now,
        config={},
        aggregate=AggregateMetrics(
            n_cases=2, n_completed=2, n_errored=0,
            n_refined_wins=2, n_raw_wins=0, n_ties=0,
            refined_win_rate=1.0, raw_win_rate=0.0, tie_rate=0.0,
            material_improvement_rate=1.0, degradation_rate=0.0,
        ),
        aggregate_rubrics={
            "formulation_quality_v1": RubricAggregate(
                rubric_name="formulation_quality_v1",
                target="formulation",
                n_cases=2,
                raw_mean_aggregate=0.6,
                refined_mean_aggregate=0.8,
                mean_delta=0.2,
            )
        },
        aggregate_properties={
            "addresses_audience": PropertyAggregate(
                property_name="addresses_audience",
                target="artifact",
                n_applied=2,
                raw_pass_rate=0.5,
                refined_pass_rate=1.0,
            )
        },
    )
    again = BenchmarkReport.model_validate_json(report.model_dump_json())
    assert again == report
