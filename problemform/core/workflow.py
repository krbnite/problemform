from collections.abc import Callable

from problemform.agents import (
    OBJECTIVE_ANALYSIS_PROMPT,
    ASSUMPTION_EXCAVATION_PROMPT,
    INFORMATION_GAP_DETECTION_PROMPT,
    EXPERT_PANEL_GENERATION_PROMPT,
    ALTERNATIVE_FRAMING_PROMPT,
    META_QUESTION_GENERATION_PROMPT,
    PROMPT_REFINEMENT_PROMPT,
    CONVERGENCE_EVALUATION_PROMPT,
)
from problemform.core.language_models import LLMProvider
from problemform.core.state import initialize_state, transition_to_phase
from problemform.models import (
    AlternativeFramingResult,
    AssumptionExcavationResult,
    ConvergenceResult,
    ExpertPanelResult,
    InformationGapResult,
    MetaQuestionResult,
    ObjectiveAnalysisResult,
    Phase,
    ProblemState,
    PromptRefinementResult,
    PromptVersion,
)

PHASE_DEFAULT_TEMPERATURES: dict[Phase, float] = {
    "OBJECTIVE_ANALYSIS": 0.0,
    "ASSUMPTION_EXCAVATION": 0.0,
    "INFORMATION_GAP_DETECTION": 0.0,
    "EXPERT_PANEL_GENERATION": 0.2,
    "ALTERNATIVE_FRAMING": 0.7,
    "META_QUESTION_GENERATION": 0.4,
    "PROMPT_REFINEMENT": 0.0,
    "CONVERGENCE_EVALUATION": 0.0,
}


def _problem_context(state: ProblemState) -> str:
    return state.model_dump_json(indent=2)


def objective_analysis(state: ProblemState, llm: LLMProvider) -> ProblemState:
    result = llm.generate_structured(
        prompt=OBJECTIVE_ANALYSIS_PROMPT.replace("{problem_context}", _problem_context(state)),
        output_model=ObjectiveAnalysisResult,
        temperature=PHASE_DEFAULT_TEMPERATURES["OBJECTIVE_ANALYSIS"],
    )
    return state.model_copy(
        update={
            "stated_objective": result.stated_objective,
            "inferred_objective": result.inferred_objective,
        }
    )


def assumption_excavation(state: ProblemState, llm: LLMProvider) -> ProblemState:
    result = llm.generate_structured(
        prompt=ASSUMPTION_EXCAVATION_PROMPT.replace("{problem_context}", _problem_context(state)),
        output_model=AssumptionExcavationResult,
        temperature=PHASE_DEFAULT_TEMPERATURES["ASSUMPTION_EXCAVATION"],
    )
    return state.model_copy(
        update={"assumptions": [*state.assumptions, *result.assumptions]}
    )


def information_gap_detection(state: ProblemState, llm: LLMProvider) -> ProblemState:
    result = llm.generate_structured(
        prompt=INFORMATION_GAP_DETECTION_PROMPT.replace("{problem_context}", _problem_context(state)),
        output_model=InformationGapResult,
        temperature=PHASE_DEFAULT_TEMPERATURES["INFORMATION_GAP_DETECTION"],
    )
    return state.model_copy(
        update={"information_gaps": [*state.information_gaps, *result.information_gaps]}
    )


def expert_panel_generation(state: ProblemState, llm: LLMProvider) -> ProblemState:
    result = llm.generate_structured(
        prompt=EXPERT_PANEL_GENERATION_PROMPT.replace("{problem_context}", _problem_context(state)),
        output_model=ExpertPanelResult,
        temperature=PHASE_DEFAULT_TEMPERATURES["EXPERT_PANEL_GENERATION"],
    )
    return state.model_copy(
        update={
            "expert_panel_perspectives": [
                *state.expert_panel_perspectives,
                *result.expert_panel_perspectives,
            ]
        }
    )


def alternative_framing(state: ProblemState, llm: LLMProvider) -> ProblemState:
    result = llm.generate_structured(
        prompt=ALTERNATIVE_FRAMING_PROMPT.replace("{problem_context}", _problem_context(state)),
        output_model=AlternativeFramingResult,
        temperature=PHASE_DEFAULT_TEMPERATURES["ALTERNATIVE_FRAMING"],
    )
    return state.model_copy(
        update={
            "alternative_framings": [
                *state.alternative_framings,
                *result.alternative_framings,
            ]
        }
    )


def meta_question_generation(state: ProblemState, llm: LLMProvider) -> ProblemState:
    result = llm.generate_structured(
        prompt=META_QUESTION_GENERATION_PROMPT.replace("{problem_context}", _problem_context(state)),
        output_model=MetaQuestionResult,
        temperature=PHASE_DEFAULT_TEMPERATURES["META_QUESTION_GENERATION"],
    )
    return state.model_copy(
        update={"meta_questions": [*state.meta_questions, *result.meta_questions]}
    )


def prompt_refinement(state: ProblemState, llm: LLMProvider) -> ProblemState:
    result = llm.generate_structured(
        prompt=PROMPT_REFINEMENT_PROMPT.replace("{problem_context}", _problem_context(state)),
        output_model=PromptRefinementResult,
        temperature=PHASE_DEFAULT_TEMPERATURES["PROMPT_REFINEMENT"],
    )
    next_version = PromptVersion(
        version=len(state.prompt_versions),
        prompt=result.prompt,
        revision=result.revision,
    )
    return state.model_copy(
        update={"prompt_versions": [*state.prompt_versions, next_version]}
    )


def convergence_evaluation(state: ProblemState, llm: LLMProvider) -> ProblemState:
    result = llm.generate_structured(
        prompt=CONVERGENCE_EVALUATION_PROMPT.replace("{problem_context}", _problem_context(state)),
        output_model=ConvergenceResult,
        temperature=PHASE_DEFAULT_TEMPERATURES["CONVERGENCE_EVALUATION"],
    )
    return state.model_copy(update={"convergence_status": result.convergence_status})


def loop_should_continue(state: ProblemState) -> bool:
    return state.convergence_status != "CONVERGED"


PhaseHandler = Callable[[ProblemState, LLMProvider], ProblemState]

PHASE_PIPELINE: list[tuple[Phase, PhaseHandler]] = [
    ("OBJECTIVE_ANALYSIS", objective_analysis),
    ("ASSUMPTION_EXCAVATION", assumption_excavation),
    ("INFORMATION_GAP_DETECTION", information_gap_detection),
    ("EXPERT_PANEL_GENERATION", expert_panel_generation),
    ("ALTERNATIVE_FRAMING", alternative_framing),
    ("META_QUESTION_GENERATION", meta_question_generation),
    ("PROMPT_REFINEMENT", prompt_refinement),
    ("CONVERGENCE_EVALUATION", convergence_evaluation),
]


def run(
    raw_input: str,
    llm: LLMProvider,
    *,
    max_iterations: int = 5,
) -> ProblemState:
    state = initialize_state(raw_input)
    for _ in range(max_iterations):
        for phase, handler in PHASE_PIPELINE:
            state = transition_to_phase(state, phase)
            state = handler(state, llm)
        if not loop_should_continue(state):
            break
    return state.model_copy(
        update={"final_prompt": state.prompt_versions[-1].prompt}
    )
