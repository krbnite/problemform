import random
from pathlib import Path

from problemform.eval.engine import (
    _activate_expected_properties,
    _aggregate,
    _detect_same_family,
    run_benchmark,
)
from problemform.eval.judges import ComparativeJudgmentResult
from problemform.eval.models import (
    PropertyCheck,
    Rubric,
    RubricCriterion,
    TestCase,
)


# --- stub providers ---------------------------------------------------------


class _PFStub:
    """Drop-in for the PF provider. The engine calls workflow.run which loops
    the full pipeline; we stub generate_structured to feed every phase."""

    model = "pf-stub-model"

    def __init__(self):
        self._cnt = {"conv": 0}

    def generate_text(self, *a, **kw):
        return ""

    def generate_structured(self, prompt, output_model, **kw):
        # Lazy imports to avoid circulars at module load.
        from problemform.models import (
            AlternativeFraming, AlternativeFramingResult,
            Assumption, AssumptionExcavationResult,
            ConvergenceResult, ExpertPanelResult, ExpertPerspective,
            InformationGap, InformationGapResult,
            MetaQuestion, MetaQuestionResult,
            ObjectiveAnalysisResult,
            PromptRefinementResult, Revision,
        )
        if output_model is ObjectiveAnalysisResult:
            return output_model(stated_objective="s", inferred_objective="i",
                                objective_alignment="a", rationale="r")
        if output_model is AssumptionExcavationResult:
            return output_model(assumptions=[Assumption(
                assumption="x", assumption_type="implicit", importance="high",
                impact_if_wrong="i", rationale="r",
            )])
        if output_model is InformationGapResult:
            return output_model(information_gaps=[InformationGap(
                gap="x", importance="high", impact_if_known="i",
                acquisition_method="user_question", rationale="r",
            )])
        if output_model is ExpertPanelResult:
            return output_model(expert_panel_perspectives=[ExpertPerspective(
                perspective_type="t", perspective_name="n", rationale="r", question="q",
            )])
        if output_model is AlternativeFramingResult:
            return output_model(alternative_framings=[AlternativeFraming(
                framing="f", rationale="r", difference_from_original="d", potential_value="v",
            )])
        if output_model is MetaQuestionResult:
            return output_model(meta_questions=[MetaQuestion(
                question="mq", rationale="r", potential_impact="i",
            )])
        if output_model is PromptRefinementResult:
            return output_model(prompt="REFINED_PROMPT",
                                revision=Revision(phase="PROMPT_REFINEMENT",
                                                  description="d", rationale="r"))
        if output_model is ConvergenceResult:
            self._cnt["conv"] += 1
            status = "CONVERGED" if self._cnt["conv"] >= 2 else "NEAR_CONVERGENCE"
            return output_model(convergence_status=status, rationale="r",
                                prompt_delta_assessment="d",
                                remaining_opportunities=[])
        raise AssertionError(f"unexpected output_model: {output_model!r}")


class _AnswerStub:
    """Records calls; returns distinct text per input to make judge ordering testable."""

    model = "answer-stub-model"

    def __init__(self):
        self.calls: list[str] = []

    def generate_text(self, prompt, **kw):
        self.calls.append(prompt)
        return f"ANSWER({prompt[:30]})"

    def generate_structured(self, *a, **kw):
        raise AssertionError("answer provider should not be asked for structured output")


class _JudgeStub:
    """Multi-lens judge stub.

    Since M3B-α.4, a single benchmark run can ask the judge for three kinds of
    structured output: the M3A comparative verdict (``ComparativeJudgmentResult``),
    per-criterion rubric scores (a verdict with a ``raw_score`` field), and
    per-property verdicts (a verdict with a ``holds`` field). This stub dispatches
    on the requested ``output_model`` so the same judge can serve all three lenses.
    ``property_holds`` and ``rubric_raw_score`` let tests steer the non-M3A lenses.
    """

    model = "judge-stub-model"

    def __init__(self, winner="b", materiality="material",
                 property_holds=True, rubric_raw_score=4):
        self.winner = winner
        self.materiality = materiality
        self.property_holds = property_holds
        self.rubric_raw_score = rubric_raw_score

    def generate_text(self, *a, **kw):
        return ""

    def generate_structured(self, prompt, output_model, **kw):
        fields = set(output_model.model_fields)
        if output_model is ComparativeJudgmentResult:
            return ComparativeJudgmentResult(
                winner=self.winner, materiality=self.materiality,
                rationale="r", key_differences=["d"],
            )
        if "holds" in fields:      # property-check verdict
            return output_model(holds=self.property_holds, rationale="r")
        if "raw_score" in fields:  # rubric-criterion verdict
            return output_model(raw_score=self.rubric_raw_score, rationale="r")
        raise AssertionError(f"unexpected output_model: {output_model!r}")


class _AlwaysCrash:
    def __init__(self, exc_type):
        self.exc_type = exc_type

    def generate_text(self, *a, **kw):
        raise self.exc_type("boom")

    def generate_structured(self, *a, **kw):
        raise self.exc_type("boom")


# --- tests ------------------------------------------------------------------


def _case(name="c1") -> TestCase:
    return TestCase(name=name, category="cat", raw_question="why is the sky blue?")


def test_run_benchmark_persists_artifacts_and_judges(tmp_path: Path):
    report = run_benchmark(
        [_case("philo_case")],
        pf_provider=_PFStub(),
        answer_provider=_AnswerStub(),
        judge_provider=_JudgeStub(winner="b", materiality="material"),
        output_dir=tmp_path,
        max_iterations=1,
        rng=random.Random(0),
    )
    assert len(report.test_case_results) == 1
    r = report.test_case_results[0]
    assert r.errors == []
    assert r.comparative_judgment is not None
    assert r.raw_answer.startswith("ANSWER(")
    assert r.refined_answer.startswith("ANSWER(")
    # disk artifacts
    case_dir = tmp_path / "cases" / "philo_case"
    assert (case_dir / "problem_state.json").exists()
    assert (case_dir / "raw_answer.txt").exists()
    assert (case_dir / "refined_answer.txt").exists()
    # problem_state_path is relative to run dir
    assert r.problem_state_path == "cases/philo_case/problem_state.json"


def test_failure_containment_continues_after_judge_failure(tmp_path: Path):
    """Case 2 of 3 fails at judge time; benchmark must still return all 3 results."""
    cases = [_case(f"c{i}") for i in range(3)]

    class _JudgeCrashesOnSecond:
        calls = 0
        def generate_text(self, *a, **kw): return ""
        def generate_structured(self, prompt, output_model, **kw):
            _JudgeCrashesOnSecond.calls += 1
            if _JudgeCrashesOnSecond.calls == 2:
                raise RuntimeError("boom")
            return ComparativeJudgmentResult(
                winner="a", materiality="minor", rationale="r", key_differences=[]
            )

    report = run_benchmark(
        cases,
        pf_provider=_PFStub(),
        answer_provider=_AnswerStub(),
        judge_provider=_JudgeCrashesOnSecond(),
        output_dir=tmp_path,
        max_iterations=1,
        rng=random.Random(0),
    )
    assert len(report.test_case_results) == 3
    # exactly one errored
    errored = [r for r in report.test_case_results if r.errors]
    assert len(errored) == 1
    assert errored[0].comparative_judgment is None
    assert "judge failed" in errored[0].errors[0]
    # aggregate is over completed
    assert report.aggregate.n_cases == 3
    assert report.aggregate.n_completed == 2
    assert report.aggregate.n_errored == 1


def test_aggregate_three_way_rates():
    # Construct three results: one refined-win-material, one raw-win-minor, one tie.
    def mk(winner_actual, materiality):
        from problemform.eval.models import ComparativeJudgment, TestCaseResult
        return TestCaseResult(
            test_case=_case(),
            raw_prompt="q",
            refined_prompt="q+",
            raw_answer="x", refined_answer="y",
            comparative_judgment=ComparativeJudgment(
                target="answer",
                presented_first_actual="raw",
                winner="a", winner_actual=winner_actual,
                materiality=materiality, rationale="r", key_differences=[],
            ),
        )
    results = [
        mk("refined", "material"),
        mk("raw", "minor"),
        mk("tie", "stylistic_only"),
    ]
    agg = _aggregate(results)
    assert agg.n_cases == 3 and agg.n_completed == 3
    assert agg.n_refined_wins == 1
    assert agg.n_raw_wins == 1
    assert agg.n_ties == 1
    assert agg.refined_win_rate == pytest.approx(1/3)
    assert agg.raw_win_rate == pytest.approx(1/3)
    assert agg.tie_rate == pytest.approx(1/3)
    assert agg.material_improvement_rate == pytest.approx(1/3)
    assert agg.degradation_rate == pytest.approx(0.0)


def test_aggregate_with_only_errored_cases_returns_none_rates():
    from problemform.eval.models import TestCaseResult
    bad = TestCaseResult(
        test_case=_case(),
        raw_prompt="q", refined_prompt="q",
        raw_answer="", refined_answer="",
        comparative_judgment=None,
        errors=["boom"],
    )
    agg = _aggregate([bad])
    assert agg.n_completed == 0
    assert agg.refined_win_rate is None
    assert agg.raw_win_rate is None
    assert agg.material_improvement_rate is None
    assert agg.degradation_rate is None


def test_detect_same_family_warns_on_same_provider():
    w = _detect_same_family("openai", "gpt-5.4", "openai", "gpt-5.4")
    assert w is not None and "self-preference" in w


def test_detect_same_family_returns_none_when_cross_provider():
    assert _detect_same_family("openai", "gpt-5.4", "anthropic", "claude-sonnet-4-6") is None


def test_aggregate_runtime_sums_by_role_including_partial_timing():
    """`_aggregate_runtime` maps timing keys to roles correctly and tolerates
    cases that captured only partial timing (errored mid-pipeline)."""
    from problemform.eval.engine import _aggregate_runtime
    from problemform.eval.models import TestCaseResult

    def mk(timing: dict[str, float], name: str = "c", errors=None) -> TestCaseResult:
        return TestCaseResult(
            test_case=_case(name),
            raw_prompt="q", refined_prompt="q+",
            raw_answer="", refined_answer="",
            comparative_judgment=None,
            errors=errors or [],
            timing=timing,
        )

    results = [
        # Full case: pf=10, raw=1, refined=2, judge=3.
        mk({"pf_run": 10.0, "raw_answer": 1.0, "refined_answer": 2.0, "judge": 3.0}, "ok"),
        # Errored after raw answer: pf=5, raw=0.5, no refined/judge.
        mk({"pf_run": 5.0, "raw_answer": 0.5}, "errored", errors=["x"]),
    ]
    rt = _aggregate_runtime(results)
    assert rt.pf_seconds == pytest.approx(15.0)         # 10 + 5
    assert rt.answer_seconds == pytest.approx(3.5)       # (1 + 2) + 0.5
    assert rt.judge_seconds == pytest.approx(3.0)        # 3 + 0
    assert rt.total_seconds == pytest.approx(21.5)


def test_on_progress_emits_expected_event_sequence(tmp_path: Path):
    events = []
    run_benchmark(
        [_case("c1"), _case("c2")],
        pf_provider=_PFStub(),
        answer_provider=_AnswerStub(),
        judge_provider=_JudgeStub(winner="b", materiality="material"),
        output_dir=tmp_path,
        max_iterations=1,
        rng=random.Random(0),
        on_progress=events.append,
    )

    kinds = [e.kind for e in events]
    expected = (
        ["run_start"]
        + ["case_start"] + ["step"] * 4 + ["case_done"]
        + ["case_start"] + ["step"] * 4 + ["case_done"]
        + ["run_done"]
    )
    assert kinds == expected

    # case_index / total are correct on case_start events
    case_starts = [e for e in events if e.kind == "case_start"]
    assert [e.case_index for e in case_starts] == [0, 1]
    assert all(e.total == 2 for e in case_starts)

    # step events carry both case and step
    steps = [e for e in events if e.kind == "step"]
    assert [e.step for e in steps[:4]] == [
        "problemform_refinement", "raw_answer", "refined_answer", "comparative_judge",
    ]
    assert all(e.case is not None for e in steps)

    # case_done events carry a timing dict populated with the four sub-steps
    case_dones = [e for e in events if e.kind == "case_done"]
    assert len(case_dones) == 2
    for e in case_dones:
        assert e.timing is not None
        assert {"pf_run", "raw_answer", "refined_answer", "judge"} <= set(e.timing.keys())


def test_on_progress_emits_case_errored_on_judge_failure(tmp_path: Path):
    """A judge exception produces case_errored (not case_done) with errors populated."""
    class _AlwaysFailingJudge:
        def generate_text(self, *a, **kw):
            return ""

        def generate_structured(self, *a, **kw):
            raise RuntimeError("boom")

    events = []
    run_benchmark(
        [_case("c1")],
        pf_provider=_PFStub(),
        answer_provider=_AnswerStub(),
        judge_provider=_AlwaysFailingJudge(),
        output_dir=tmp_path,
        max_iterations=1,
        rng=random.Random(0),
        on_progress=events.append,
    )

    kinds = [e.kind for e in events]
    assert "case_errored" in kinds
    assert "case_done" not in kinds

    errored = next(e for e in events if e.kind == "case_errored")
    assert errored.errors is not None and any("judge failed" in m for m in errored.errors)


import pytest  # placed at end to avoid noise above


# --- M3B-α.4: rubric + property integration ---------------------------------


def _formulation_rubric() -> Rubric:
    return Rubric(
        name="formq_test",
        description="test formulation rubric",
        target="formulation",
        mode="absolute",
        criteria=[
            RubricCriterion(name="clarity", description="is it clear?", weight=1.0,
                            scoring="graded_5"),
        ],
    )


def _mixed_property_suite() -> list[PropertyCheck]:
    return [
        PropertyCheck(name="form_prop", description="formulation names a claim",
                      target="formulation", expected=True),
        PropertyCheck(name="art_prop", description="answer addresses the request",
                      target="artifact", expected=True),
    ]


def _case_with_props(name="c1") -> TestCase:
    return TestCase(
        name=name, category="cat", raw_question="why is the sky blue?",
        expected_properties=["elicits the observer's altitude", "avoids jargon"],
    )


def test_activate_expected_properties_are_formulation_targeted():
    """Corpus expected_properties activate as target=formulation, expected=True (option B)."""
    checks = _activate_expected_properties(_case_with_props())
    assert [c.target for c in checks] == ["formulation", "formulation"]
    assert all(c.expected is True for c in checks)
    # Descriptions preserved verbatim; names are unique, stable slugs.
    assert [c.description for c in checks] == [
        "elicits the observer's altitude", "avoids jargon",
    ]
    assert len({c.name for c in checks}) == 2


def test_rubric_and_property_evaluations_populate_and_aggregate(tmp_path: Path):
    report = run_benchmark(
        [_case_with_props("cA")],
        pf_provider=_PFStub(),
        answer_provider=_AnswerStub(),
        judge_provider=_JudgeStub(property_holds=True, rubric_raw_score=4),
        output_dir=tmp_path,
        max_iterations=1,
        rubrics=[_formulation_rubric()],
        property_suites=_mixed_property_suite(),
        rng=random.Random(0),
    )
    r = report.test_case_results[0]

    # Rubric ran against both formulation subjects (raw + refined).
    assert {e.subject for e in r.rubric_evaluations} == {"raw", "refined"}
    assert all(e.rubric_name == "formq_test" for e in r.rubric_evaluations)

    # Property results include: shared suite (form + artifact) and the two
    # activated expected_properties (formulation), each for raw + refined.
    names = {p.property_name for p in r.property_check_results}
    assert {"form_prop", "art_prop"} <= names
    activated = [p for p in r.property_check_results if p.property_name not in
                 {"form_prop", "art_prop"}]
    assert activated and all(p.target == "formulation" for p in activated)

    # Aggregates present and lens-separated on the report.
    assert "formq_test" in report.aggregate_rubrics
    assert report.aggregate_rubrics["formq_test"].mean_delta is not None
    assert {"form_prop", "art_prop"} <= set(report.aggregate_properties)
    assert report.aggregate_properties["form_prop"].refined_pass_rate == 1.0

    # M3A lens untouched: the case still completes.
    assert report.aggregate.n_completed == 1


def test_rubric_delta_reflects_raw_vs_refined_scores(tmp_path: Path):
    """A judge that scores the refined formulation higher yields a positive delta."""

    class _ScoringJudge:
        model = "scoring-judge"

        def generate_text(self, *a, **kw):
            return ""

        def generate_structured(self, prompt, output_model, **kw):
            fields = set(output_model.model_fields)
            if output_model is ComparativeJudgmentResult:
                return ComparativeJudgmentResult(
                    winner="b", materiality="material", rationale="r",
                    key_differences=[])
            if "holds" in fields:
                return output_model(holds=True, rationale="r")
            # Refined formulation subject is "REFINED_PROMPT" (from _PFStub).
            score = 4 if "REFINED_PROMPT" in prompt else 2
            return output_model(raw_score=score, rationale="r")

    report = run_benchmark(
        [_case("cD")],
        pf_provider=_PFStub(),
        answer_provider=_AnswerStub(),
        judge_provider=_ScoringJudge(),
        output_dir=tmp_path,
        max_iterations=1,
        rubrics=[_formulation_rubric()],
        rng=random.Random(0),
    )
    agg = report.aggregate_rubrics["formq_test"]
    # raw: graded_5 score 2 -> 0.5 ; refined: score 4 -> 1.0 ; delta 0.5.
    assert agg.raw_mean_aggregate == pytest.approx(0.5)
    assert agg.refined_mean_aggregate == pytest.approx(1.0)
    assert agg.mean_delta == pytest.approx(0.5)


def test_rubric_and_property_timing_flows_into_aggregate_runtime(tmp_path: Path):
    """Rubric/property lens time is counted in the run's aggregate runtime."""
    report = run_benchmark(
        [_case_with_props("cR")],
        pf_provider=_PFStub(),
        answer_provider=_AnswerStub(),
        judge_provider=_JudgeStub(),
        output_dir=tmp_path,
        max_iterations=1,
        rubrics=[_formulation_rubric()],
        property_suites=_mixed_property_suite(),
        rng=random.Random(0),
    )
    rt = report.aggregate_runtime
    # Both lenses ran, so both contribute non-negative time and are tracked.
    assert rt.rubric_seconds >= 0.0
    assert rt.property_seconds >= 0.0
    # The per-case timing dict carries the lens keys the aggregate sums from.
    t = report.test_case_results[0].timing
    assert "rubric" in t and "property" in t
    assert rt.rubric_seconds == pytest.approx(t["rubric"])
    assert rt.property_seconds == pytest.approx(t["property"])
    # Total reconciles: it includes every per-role component, lenses included.
    assert rt.total_seconds == pytest.approx(
        rt.pf_seconds + rt.answer_seconds + rt.judge_seconds
        + rt.rubric_seconds + rt.property_seconds
    )


def test_rubric_failure_does_not_drop_m3a_completion(tmp_path: Path):
    """A failing rubric lens records an error but leaves the M3A verdict intact."""

    class _RubricFailingJudge:
        model = "rubric-failing-judge"

        def generate_text(self, *a, **kw):
            return ""

        def generate_structured(self, prompt, output_model, **kw):
            fields = set(output_model.model_fields)
            if output_model is ComparativeJudgmentResult:
                return ComparativeJudgmentResult(
                    winner="b", materiality="material", rationale="r",
                    key_differences=[])
            if "raw_score" in fields:
                raise RuntimeError("rubric judge boom")
            return output_model(holds=True, rationale="r")

    report = run_benchmark(
        [_case("cF")],  # no expected_properties: isolate the rubric failure
        pf_provider=_PFStub(),
        answer_provider=_AnswerStub(),
        judge_provider=_RubricFailingJudge(),
        output_dir=tmp_path,
        max_iterations=1,
        rubrics=[_formulation_rubric()],
        rng=random.Random(0),
    )
    r = report.test_case_results[0]
    assert any("rubric" in m for m in r.errors)          # failure recorded
    assert r.rubric_evaluations == []                    # nothing scored
    assert r.comparative_judgment is not None             # M3A lens intact
    assert report.aggregate.n_completed == 1              # not dropped
    assert report.aggregate.n_errored == 0
