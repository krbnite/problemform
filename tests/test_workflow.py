from problemform.core.state import initialize_state
from problemform.core.workflow import (
    ALTERNATIVE_FRAMINGS_CAP,
    ANALYSIS_PHASES,
    ASSUMPTIONS_CAP,
    EXPERT_PANEL_CAP,
    FULL_PIPELINE,
    INFORMATION_GAPS_CAP,
    JUDGMENT_PHASES,
    META_QUESTIONS_CAP,
    SYNTHESIS_PHASES,
    _LEADING_TEMPLATES,
    _merge_unique,
    _norm,
    alternative_framing,
    analyze,
    assumption_excavation,
    expert_panel_generation,
    information_gap_detection,
    meta_question_generation,
    prompt_refinement,
    run,
    synthesize,
)
from problemform.models import (
    AlternativeFraming,
    AlternativeFramingResult,
    Assumption,
    AssumptionExcavationResult,
    ConvergenceResult,
    ExpertPanelResult,
    ExpertPerspective,
    InformationGap,
    InformationGapResult,
    MetaQuestion,
    MetaQuestionResult,
    ProblemState,
    PromptRefinementResult,
    PromptVersion,
    Revision,
)


def test_full_pipeline_covers_canonical_phases():
    phases = [phase for phase, _ in FULL_PIPELINE]
    assert phases == [
        "OBJECTIVE_ANALYSIS",
        "ASSUMPTION_EXCAVATION",
        "INFORMATION_GAP_DETECTION",
        "EXPERT_PANEL_GENERATION",
        "ALTERNATIVE_FRAMING",
        "META_QUESTION_GENERATION",
        "PROMPT_REFINEMENT",
        "CONVERGENCE_EVALUATION",
    ]


def test_pipeline_slices_match_doc():
    assert [p for p, _ in ANALYSIS_PHASES] == [
        "OBJECTIVE_ANALYSIS",
        "ASSUMPTION_EXCAVATION",
        "INFORMATION_GAP_DETECTION",
        "EXPERT_PANEL_GENERATION",
        "ALTERNATIVE_FRAMING",
        "META_QUESTION_GENERATION",
    ]
    assert [p for p, _ in SYNTHESIS_PHASES] == ["PROMPT_REFINEMENT"]
    assert [p for p, _ in JUDGMENT_PHASES] == ["CONVERGENCE_EVALUATION"]


def test_run_reaches_convergence_and_populates_state(stub_llm):
    state = run("How do I get better at X?", stub_llm, max_iterations=3)

    assert state.convergence_status == "CONVERGED"
    assert state.stated_objective == "stated"
    assert state.inferred_objective == "inferred"
    assert state.assumptions and state.information_gaps
    assert state.expert_panel_perspectives and state.alternative_framings
    assert state.meta_questions
    # initial v0 + one refinement per iteration (stub returns CONVERGED on 2nd pass)
    assert len(state.prompt_versions) >= 2
    assert state.final_prompt == state.prompt_versions[-1].prompt
    assert state.final_prompt != state.raw_input


def test_run_stops_at_max_iterations_when_not_converging(stub_llm):
    # Force the stub to never converge.
    class NeverConverges:
        def __init__(self, inner):
            self._inner = inner

        def generate_text(self, *a, **kw):
            return self._inner.generate_text(*a, **kw)

        def generate_structured(self, prompt, output_model, **kw):
            result = self._inner.generate_structured(prompt, output_model, **kw)
            from problemform.models import ConvergenceResult

            if output_model is ConvergenceResult:
                return ConvergenceResult(
                    convergence_status="NOT_CONVERGED",
                    rationale="r",
                    remaining_opportunities=[],
                )
            return result

    state = run("q", NeverConverges(stub_llm), max_iterations=2)
    assert state.convergence_status == "NOT_CONVERGED"
    assert state.final_prompt is not None


# ---------- dedup ------------------------------------------------------------


def test_merge_unique_preserves_order_and_skips_dupes():
    out = _merge_unique(["a", "b"], ["b", "c", "a", "d"], key=lambda s: s.lower())
    assert out == ["a", "b", "c", "d"]


def test_merge_unique_case_insensitive_when_key_normalizes():
    out = _merge_unique(["Foo"], ["FOO ", "  foo", "bar"], key=lambda s: " ".join(s.lower().split()))
    assert out == ["Foo", "bar"]


def test_merge_unique_dedupes_within_new_batch():
    out = _merge_unique([], ["x", "x", "y"], key=lambda s: s)
    assert out == ["x", "y"]


class _SinglePhaseStub:
    """Returns a fixed structured result for one specific output_model class."""

    def __init__(self, output_model_cls, payload):
        self.output_model_cls = output_model_cls
        self.payload = payload

    def generate_text(self, *a, **kw):
        return ""

    def generate_structured(self, prompt, output_model, **kw):
        assert output_model is self.output_model_cls
        return self.payload


def _assumption(text="a budget exists", t="implicit", imp="high"):
    return Assumption(
        assumption=text, assumption_type=t, importance=imp,
        impact_if_wrong="i", rationale="r",
    )


def _gap(text="missing review criteria"):
    return InformationGap(
        gap=text, importance="high", impact_if_known="i",
        acquisition_method="user_question", rationale="r",
    )


def _perspective(name="senior engineer", question="what does done look like?"):
    return ExpertPerspective(
        perspective_type="domain expert", perspective_name=name,
        rationale="r", question=question,
    )


def _framing(text="frame as a learning opportunity"):
    return AlternativeFraming(
        framing=text, rationale="r", difference_from_original="d", potential_value="v",
    )


def _meta(text="is the deadline real?"):
    return MetaQuestion(question=text, rationale="r", potential_impact="i")


def test_assumption_excavation_dedupes_across_calls():
    a = _assumption()
    llm = _SinglePhaseStub(AssumptionExcavationResult, AssumptionExcavationResult(assumptions=[a]))
    s = initialize_state("q")
    s = assumption_excavation(s, llm)
    s = assumption_excavation(s, llm)
    assert len(s.assumptions) == 1


def test_assumption_excavation_dedupes_near_duplicates():
    same = AssumptionExcavationResult(assumptions=[_assumption("A budget exists.")])
    casey = AssumptionExcavationResult(assumptions=[_assumption("  a budget exists. ")])
    s = initialize_state("q")
    s = assumption_excavation(s, _SinglePhaseStub(AssumptionExcavationResult, same))
    s = assumption_excavation(s, _SinglePhaseStub(AssumptionExcavationResult, casey))
    assert len(s.assumptions) == 1


def test_information_gap_detection_dedupes_across_calls():
    payload = InformationGapResult(information_gaps=[_gap()])
    llm = _SinglePhaseStub(InformationGapResult, payload)
    s = initialize_state("q")
    s = information_gap_detection(s, llm)
    s = information_gap_detection(s, llm)
    assert len(s.information_gaps) == 1


def test_expert_panel_dedupes_on_composite_key():
    same = ExpertPanelResult(expert_panel_perspectives=[_perspective()])
    other_q = ExpertPanelResult(
        expert_panel_perspectives=[_perspective(question="what's the review rubric?")]
    )
    llm_same = _SinglePhaseStub(ExpertPanelResult, same)
    llm_other = _SinglePhaseStub(ExpertPanelResult, other_q)
    s = initialize_state("q")
    s = expert_panel_generation(s, llm_same)
    s = expert_panel_generation(s, llm_same)        # same name + same question → skip
    s = expert_panel_generation(s, llm_other)       # same name + different question → keep
    assert len(s.expert_panel_perspectives) == 2


def test_alternative_framing_dedupes_across_calls():
    payload = AlternativeFramingResult(alternative_framings=[_framing()])
    llm = _SinglePhaseStub(AlternativeFramingResult, payload)
    s = initialize_state("q")
    s = alternative_framing(s, llm)
    s = alternative_framing(s, llm)
    assert len(s.alternative_framings) == 1


def test_meta_question_generation_dedupes_across_calls():
    payload = MetaQuestionResult(meta_questions=[_meta()])
    llm = _SinglePhaseStub(MetaQuestionResult, payload)
    s = initialize_state("q")
    s = meta_question_generation(s, llm)
    s = meta_question_generation(s, llm)
    assert len(s.meta_questions) == 1


def test_prompt_refinement_still_accumulates_history():
    payload = PromptRefinementResult(
        prompt="refined",
        revision=Revision(phase="PROMPT_REFINEMENT", description="d", rationale="r"),
    )
    llm = _SinglePhaseStub(PromptRefinementResult, payload)
    s = initialize_state("q")
    s = prompt_refinement(s, llm)
    s = prompt_refinement(s, llm)
    s = prompt_refinement(s, llm)
    # v0 (initial) + 3 refinements
    assert len(s.prompt_versions) == 4
    assert [pv.version for pv in s.prompt_versions] == [0, 1, 2, 3]


# ---------- final_prompt tracking --------------------------------------------


def _refine_payload(prompt_text: str, rationale: str) -> PromptRefinementResult:
    return PromptRefinementResult(
        prompt=prompt_text,
        revision=Revision(
            phase="PROMPT_REFINEMENT",
            description=f"synthesized {prompt_text!r}",
            rationale=rationale,
        ),
    )


def test_single_synthesis_sets_final_prompt():
    payload = _refine_payload("refined v1", "raised clarity")
    s = initialize_state("raw")
    assert s.final_prompt is None
    s = prompt_refinement(s, _SinglePhaseStub(PromptRefinementResult, payload))
    assert [pv.version for pv in s.prompt_versions] == [0, 1]
    assert s.prompt_versions[0].prompt == "raw"
    assert s.prompt_versions[1].prompt == "refined v1"
    assert s.final_prompt == "refined v1"


def test_two_syntheses_preserve_history_and_bump_final_prompt():
    p1 = _refine_payload("refined v1", "first improvement")
    p2 = _refine_payload("refined v2", "second improvement")
    s = initialize_state("raw")
    s = prompt_refinement(s, _SinglePhaseStub(PromptRefinementResult, p1))
    v1_snapshot = s.prompt_versions[1]
    s = prompt_refinement(s, _SinglePhaseStub(PromptRefinementResult, p2))

    assert [pv.version for pv in s.prompt_versions] == [0, 1, 2]
    assert [pv.prompt for pv in s.prompt_versions] == ["raw", "refined v1", "refined v2"]
    assert s.final_prompt == "refined v2"
    # v1 untouched: previous prompt versions are not overwritten or rewritten
    assert s.prompt_versions[1] == v1_snapshot


def test_each_prompt_version_keeps_its_revision_rationale():
    p1 = _refine_payload("refined v1", "first improvement")
    p2 = _refine_payload("refined v2", "second improvement")
    s = initialize_state("raw")
    s = prompt_refinement(s, _SinglePhaseStub(PromptRefinementResult, p1))
    s = prompt_refinement(s, _SinglePhaseStub(PromptRefinementResult, p2))

    assert s.prompt_versions[0].revision is not None
    assert s.prompt_versions[0].revision.phase == "INITIAL_INPUT"
    assert s.prompt_versions[1].revision.rationale == "first improvement"
    assert s.prompt_versions[2].revision.rationale == "second improvement"


def test_library_synthesize_updates_final_prompt(stub_llm):
    s = analyze("q", stub_llm)
    assert s.final_prompt is None                    # analyze must not touch final_prompt
    s = synthesize(s, stub_llm)
    assert s.final_prompt == s.prompt_versions[-1].prompt
    assert s.final_prompt != s.raw_input


def test_analyze_does_not_set_final_prompt(stub_llm):
    s = analyze("q", stub_llm)
    assert s.final_prompt is None
    assert s.prompt_versions[-1].prompt == "q"        # still just v0


def test_run_does_not_double_artifacts_across_iterations(stub_llm):
    # stub_llm returns 1 of each artifact every call; with dedup, 2 iterations still yields 1 each.
    state = run("q", stub_llm, max_iterations=3)
    assert len(state.assumptions) == 1
    assert len(state.information_gaps) == 1
    assert len(state.expert_panel_perspectives) == 1
    assert len(state.alternative_framings) == 1
    assert len(state.meta_questions) == 1
    # prompt_versions still grows (initial + at least one refinement)
    assert len(state.prompt_versions) >= 2


# ---------- normalization + caps ---------------------------------------------


import pytest


def test_norm_strips_punctuation_case_whitespace():
    assert _norm("  Hello, World!! ") == "hello world"


@pytest.mark.parametrize("tpl", _LEADING_TEMPLATES)
def test_norm_strips_each_leading_template(tpl):
    assert _norm(f"{tpl} foo bar") == "foo bar"


def test_norm_template_near_duplicates_collapse():
    a = _norm("Reframe the issue as semantic disambiguation.")
    b = _norm("Treat the problem as semantic disambiguation")
    assert a == b == "semantic disambiguation"


def test_norm_lone_template_collapses_to_empty():
    assert _norm("Reframe the issue as") == ""


def test_norm_strips_only_one_template_layer():
    # Nested template — only the outermost is stripped (documented MVP behavior).
    out = _norm("Reframe the issue as treat the problem as foo")
    assert out == "treat the problem as foo"


def test_alternative_framing_collapses_template_near_dupes():
    a = AlternativeFramingResult(
        alternative_framings=[_framing("Reframe the issue as semantic disambiguation.")]
    )
    b = AlternativeFramingResult(
        alternative_framings=[_framing("Treat the problem as semantic disambiguation")]
    )
    s = initialize_state("q")
    s = alternative_framing(s, _SinglePhaseStub(AlternativeFramingResult, a))
    s = alternative_framing(s, _SinglePhaseStub(AlternativeFramingResult, b))
    assert len(s.alternative_framings) == 1


def test_meta_question_collapses_template_near_dupes():
    a = MetaQuestionResult(meta_questions=[_meta("Ask whether the deadline is real")])
    b = MetaQuestionResult(meta_questions=[_meta("Determine whether the deadline is real")])
    s = initialize_state("q")
    s = meta_question_generation(s, _SinglePhaseStub(MetaQuestionResult, a))
    s = meta_question_generation(s, _SinglePhaseStub(MetaQuestionResult, b))
    assert len(s.meta_questions) == 1


def test_merge_unique_respects_cap():
    out = _merge_unique(
        [], [f"item-{i}" for i in range(20)], key=lambda s: s, cap=8
    )
    assert out == [f"item-{i}" for i in range(8)]


def test_merge_unique_cap_does_not_truncate_existing():
    existing = [f"e-{i}" for i in range(8)]
    out = _merge_unique(existing, ["new-1"], key=lambda s: s, cap=8)
    # existing items retained as-is; new item rejected because cap already reached
    assert out == existing


@pytest.mark.parametrize(
    "handler, payload_cls, item_factory, field, cap",
    [
        (assumption_excavation, AssumptionExcavationResult,
         lambda i: _assumption(f"assumption {i}"), "assumptions", ASSUMPTIONS_CAP),
        (information_gap_detection, InformationGapResult,
         lambda i: _gap(f"gap {i}"), "information_gaps", INFORMATION_GAPS_CAP),
        (expert_panel_generation, ExpertPanelResult,
         lambda i: _perspective(name=f"expert {i}", question=f"q {i}"),
         "expert_panel_perspectives", EXPERT_PANEL_CAP),
        (alternative_framing, AlternativeFramingResult,
         lambda i: _framing(f"framing {i}"), "alternative_framings",
         ALTERNATIVE_FRAMINGS_CAP),
        (meta_question_generation, MetaQuestionResult,
         lambda i: _meta(f"meta {i}"), "meta_questions", META_QUESTIONS_CAP),
    ],
)
def test_each_phase_respects_cap(handler, payload_cls, item_factory, field, cap):
    items = [item_factory(i) for i in range(cap + 4)]
    payload_kw = {field: items}
    payload = payload_cls(**payload_kw)
    s = initialize_state("q")
    s = handler(s, _SinglePhaseStub(payload_cls, payload))
    assert len(getattr(s, field)) == cap


# ---------- convergence: prompt-delta primary --------------------------------


from problemform.core.workflow import convergence_evaluation
from problemform.models import ConvergenceResult


class _RecordingPromptStub:
    """Captures the prompt passed to generate_structured and returns a fixed result."""

    def __init__(self, result: ConvergenceResult):
        self.captured: str | None = None
        self.result = result

    def generate_text(self, *a, **kw):
        return ""

    def generate_structured(self, prompt, output_model, **kw):
        assert output_model is ConvergenceResult
        self.captured = prompt
        return self.result


class _RaiseIfCalled:
    def generate_text(self, *a, **kw):
        raise AssertionError("LLM should not be called on cold start")

    def generate_structured(self, *a, **kw):
        raise AssertionError("LLM should not be called on cold start")


def test_convergence_result_accepts_prompt_delta_assessment():
    r = ConvergenceResult(
        convergence_status="CONVERGED",
        rationale="r",
        prompt_delta_assessment="answers would be substantively identical",
        remaining_opportunities=["could add another framing"],
    )
    assert r.prompt_delta_assessment == "answers would be substantively identical"
    # Round-trip through JSON
    again = ConvergenceResult.model_validate_json(r.model_dump_json())
    assert again == r


def test_convergence_cold_start_short_circuits_without_llm():
    s = initialize_state("raw question")
    # only v0 exists
    assert len(s.prompt_versions) == 1
    s = convergence_evaluation(s, _RaiseIfCalled())
    assert s.convergence_status == "NOT_CONVERGED"
    assert s.last_convergence is not None
    assert s.last_convergence.prompt_delta_assessment == (
        "No prior synthesized prompt to compare against."
    )
    assert s.last_convergence.remaining_opportunities == []


def test_convergence_prompt_injects_previous_and_current_prompts():
    # Build a state with v0 (raw) and v1 (synthesized) so a delta exists.
    s = initialize_state("RAW_TEXT_MARKER")
    refine_payload = PromptRefinementResult(
        prompt="REFINED_TEXT_MARKER",
        revision=Revision(phase="PROMPT_REFINEMENT", description="d", rationale="r"),
    )
    s = prompt_refinement(s, _SinglePhaseStub(PromptRefinementResult, refine_payload))

    stub = _RecordingPromptStub(
        ConvergenceResult(
            convergence_status="NEAR_CONVERGENCE",
            rationale="r",
            prompt_delta_assessment="small but real improvement in scope",
            remaining_opportunities=[],
        )
    )
    s = convergence_evaluation(s, stub)
    assert stub.captured is not None
    assert "RAW_TEXT_MARKER" in stub.captured
    assert "REFINED_TEXT_MARKER" in stub.captured
    # Placeholders must have been substituted (not leaked).
    assert "{previous_prompt}" not in stub.captured
    assert "{current_prompt}" not in stub.captured
    assert "{prev_version}" not in stub.captured
    assert "{current_version}" not in stub.captured
    assert "{problem_context}" not in stub.captured


@pytest.mark.parametrize(
    "status", ["NOT_CONVERGED", "NEAR_CONVERGENCE", "CONVERGED"]
)
def test_convergence_evaluation_passes_status_through(status):
    s = initialize_state("raw")
    s = prompt_refinement(
        s,
        _SinglePhaseStub(
            PromptRefinementResult,
            PromptRefinementResult(
                prompt="refined",
                revision=Revision(phase="PROMPT_REFINEMENT", description="d", rationale="r"),
            ),
        ),
    )
    expected_delta = f"delta judgment for {status}"
    stub = _RecordingPromptStub(
        ConvergenceResult(
            convergence_status=status,
            rationale="r",
            prompt_delta_assessment=expected_delta,
            remaining_opportunities=["info-only"],
        )
    )
    s = convergence_evaluation(s, stub)
    assert s.convergence_status == status
    assert s.last_convergence is not None
    assert s.last_convergence.convergence_status == status
    assert s.last_convergence.prompt_delta_assessment == expected_delta
    assert s.last_convergence.remaining_opportunities == ["info-only"]


def test_cli_render_demotes_remaining_opportunities():
    from problemform.cli_render import render_markdown

    s = initialize_state("raw")
    s = prompt_refinement(
        s,
        _SinglePhaseStub(
            PromptRefinementResult,
            PromptRefinementResult(
                prompt="refined",
                revision=Revision(phase="PROMPT_REFINEMENT", description="d", rationale="r"),
            ),
        ),
    )
    s = convergence_evaluation(
        s,
        _RecordingPromptStub(
            ConvergenceResult(
                convergence_status="NEAR_CONVERGENCE",
                rationale="answers would differ in scope",
                prompt_delta_assessment="meaningful scope shift",
                remaining_opportunities=["could explore alternative success metrics"],
            )
        ),
    )
    md = render_markdown(s)

    # Prompt delta and rationale should appear as first-class headers in the
    # Convergence section, not buried with the remaining opportunities.
    assert "**Prompt delta:** meaningful scope shift" in md
    assert "**Rationale:** answers would differ in scope" in md
    assert "Remaining opportunities (informational only)" in md
    # Delta line should appear before the remaining-opportunities label.
    assert md.index("**Prompt delta:**") < md.index("Remaining opportunities")
    assert md.index("**Rationale:**") < md.index("Remaining opportunities")


# ---------- compact synthesis context ---------------------------------------


import json as _json
from problemform.core.workflow import _problem_context, _synthesis_context


def _populated_state_with_sentinels() -> ProblemState:
    """State whose verbose/judge/history fields hold sentinel strings.

    Sentinels are unique tokens so we can assert their presence or absence
    in the compact context without false positives.
    """
    return ProblemState(
        raw_input="RAW_SENTINEL",
        stated_objective="STATED_SENTINEL",
        inferred_objective="INFERRED_SENTINEL",
        assumptions=[Assumption(
            assumption="ASSUMPTION_TEXT_SENTINEL",
            assumption_type="implicit",
            importance="high",
            impact_if_wrong="IMPACT_WRONG_SENTINEL",
            rationale="ASSUMPTION_RATIONALE_SENTINEL",
        )],
        information_gaps=[InformationGap(
            gap="GAP_TEXT_SENTINEL",
            importance="high",
            impact_if_known="IMPACT_KNOWN_SENTINEL",
            acquisition_method="user_question",
            rationale="GAP_RATIONALE_SENTINEL",
        )],
        expert_panel_perspectives=[ExpertPerspective(
            perspective_type="PTYPE_SENTINEL",
            perspective_name="EXPERT_NAME_SENTINEL",
            rationale="EXPERT_RATIONALE_SENTINEL",
            question="EXPERT_QUESTION_SENTINEL",
        )],
        alternative_framings=[AlternativeFraming(
            framing="FRAMING_TEXT_SENTINEL",
            rationale="FRAMING_RATIONALE_SENTINEL",
            difference_from_original="DIFF_SENTINEL",
            potential_value="VALUE_SENTINEL",
        )],
        meta_questions=[MetaQuestion(
            question="META_TEXT_SENTINEL",
            rationale="META_RATIONALE_SENTINEL",
            potential_impact="META_IMPACT_SENTINEL",
        )],
        prompt_versions=[
            PromptVersion(version=0, prompt="V0_PROMPT_SENTINEL"),
            PromptVersion(
                version=1,
                prompt="V1_PROMPT_SENTINEL",
                revision=Revision(
                    phase="PROMPT_REFINEMENT",
                    description="REVISION_DESC_SENTINEL",
                    rationale="REVISION_RATIONALE_SENTINEL",
                ),
            ),
        ],
        convergence_status="NEAR_CONVERGENCE",
        final_prompt="FINAL_PROMPT_SENTINEL",
        last_convergence=ConvergenceResult(
            convergence_status="NEAR_CONVERGENCE",
            rationale="JUDGE_RATIONALE_SENTINEL",
            prompt_delta_assessment="DELTA_SENTINEL",
            remaining_opportunities=["OPPORTUNITY_SENTINEL"],
        ),
        phase="PROMPT_REFINEMENT",
    )


def test_synthesis_context_includes_essentials():
    s = _populated_state_with_sentinels()
    out = _synthesis_context(s)
    for needle in [
        "RAW_SENTINEL",
        "STATED_SENTINEL",
        "INFERRED_SENTINEL",
        "ASSUMPTION_TEXT_SENTINEL",
        "GAP_TEXT_SENTINEL",
        "EXPERT_NAME_SENTINEL",
        "EXPERT_QUESTION_SENTINEL",
        "FRAMING_TEXT_SENTINEL",
        "META_TEXT_SENTINEL",
        "V1_PROMPT_SENTINEL",
    ]:
        assert needle in out, f"expected {needle!r} in compact context"


def test_synthesis_context_excludes_noise():
    s = _populated_state_with_sentinels()
    out = _synthesis_context(s)
    for needle in [
        # prior prompt versions
        "V0_PROMPT_SENTINEL",
        "REVISION_DESC_SENTINEL",
        "REVISION_RATIONALE_SENTINEL",
        # judge output
        "JUDGE_RATIONALE_SENTINEL",
        "DELTA_SENTINEL",
        "OPPORTUNITY_SENTINEL",
        # per-artifact verbose rationale/impact
        "IMPACT_WRONG_SENTINEL",
        "ASSUMPTION_RATIONALE_SENTINEL",
        "IMPACT_KNOWN_SENTINEL",
        "GAP_RATIONALE_SENTINEL",
        "PTYPE_SENTINEL",
        "EXPERT_RATIONALE_SENTINEL",
        "FRAMING_RATIONALE_SENTINEL",
        "DIFF_SENTINEL",
        "VALUE_SENTINEL",
        "META_RATIONALE_SENTINEL",
        "META_IMPACT_SENTINEL",
        # bookkeeping
        "FINAL_PROMPT_SENTINEL",
    ]:
        assert needle not in out, f"unexpected {needle!r} in compact context"


def test_synthesis_context_is_meaningfully_smaller_than_full():
    """Compact projection should be substantially smaller than the full dump.

    Threshold is generous (<= 30%) so this is a regression guard against
    accidental bloat, not a fine-grained ratio assertion.
    """
    s = ProblemState(
        raw_input="example raw input that is realistic in length",
        stated_objective="x", inferred_objective="y",
        assumptions=[Assumption(
            assumption=f"assumption {i}", assumption_type="implicit",
            importance="high", impact_if_wrong="impact " * 30,
            rationale="rationale " * 30,
        ) for i in range(8)],
        information_gaps=[InformationGap(
            gap=f"gap {i}", importance="high",
            impact_if_known="known " * 30, acquisition_method="user_question",
            rationale="rationale " * 30,
        ) for i in range(8)],
        expert_panel_perspectives=[ExpertPerspective(
            perspective_type="t", perspective_name=f"expert {i}",
            rationale="rationale " * 30, question=f"question {i}",
        ) for i in range(8)],
        alternative_framings=[AlternativeFraming(
            framing=f"framing {i}", rationale="rationale " * 30,
            difference_from_original="diff " * 30,
            potential_value="value " * 30,
        ) for i in range(8)],
        meta_questions=[MetaQuestion(
            question=f"meta {i}", rationale="rationale " * 30,
            potential_impact="impact " * 30,
        ) for i in range(8)],
        prompt_versions=[PromptVersion(
            version=i, prompt=f"prompt v{i} " * 200,
            revision=Revision(phase="PROMPT_REFINEMENT", description="d", rationale="r"),
        ) for i in range(5)],
        last_convergence=ConvergenceResult(
            convergence_status="NEAR_CONVERGENCE",
            rationale="judge rationale " * 30,
            prompt_delta_assessment="delta " * 30,
            remaining_opportunities=["op " * 30 for _ in range(3)],
        ),
    )
    full = _problem_context(s)
    compact = _synthesis_context(s)
    assert len(compact) / len(full) <= 0.30, (
        f"compact={len(compact)} full={len(full)} ratio={len(compact)/len(full):.2%}"
    )


def test_synthesis_context_cold_start_when_no_prompt_versions():
    s = ProblemState(raw_input="raw")
    parsed = _json.loads(_synthesis_context(s))
    assert parsed["raw_input"] == "raw"
    assert parsed["latest_prompt"] is None


def test_prompt_refinement_uses_compact_context_not_full_state():
    """Recording stub captures the prompt; assert it contains compact-only
    signal and excludes the prior-version sentinel."""

    class _Recorder:
        def __init__(self):
            self.captured = None

        def generate_text(self, *a, **kw):
            return ""

        def generate_structured(self, prompt, output_model, **kw):
            self.captured = prompt
            return PromptRefinementResult(
                prompt="new prompt",
                revision=Revision(
                    phase="PROMPT_REFINEMENT", description="d", rationale="r"
                ),
            )

    s = _populated_state_with_sentinels()
    rec = _Recorder()
    prompt_refinement(s, rec)
    assert rec.captured is not None
    # essentials reach the synthesizer
    assert "V1_PROMPT_SENTINEL" in rec.captured
    assert "ASSUMPTION_TEXT_SENTINEL" in rec.captured
    # noise does not
    assert "V0_PROMPT_SENTINEL" not in rec.captured
    assert "JUDGE_RATIONALE_SENTINEL" not in rec.captured
    assert "FINAL_PROMPT_SENTINEL" not in rec.captured
