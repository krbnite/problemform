from datetime import datetime

import pytest

from problemform.eval.models import (
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
        test_case=TestCase(name=name, category="philosophy", raw_question="q"),
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
        raw_question="why is there something rather than nothing",
        tags=["cosmology", "metaphysics"],
        expected_properties=["disambiguates 'nothing'"],
        notes="control rationale",
    )
    again = TestCase.model_validate_json(tc.model_dump_json())
    assert again == tc


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
