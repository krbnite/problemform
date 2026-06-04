from problemform.core.workflow import PHASE_PIPELINE, run


def test_phase_pipeline_covers_canonical_phases():
    phases = [phase for phase, _ in PHASE_PIPELINE]
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
