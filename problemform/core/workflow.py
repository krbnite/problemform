import json
import string
from collections.abc import Callable
from typing import TypeVar

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


def _synthesis_context(state: ProblemState) -> str:
    """Compact projection of ProblemState for the Prompt Synthesizer.

    Drops fields the synthesizer does not need to act on (analytical-phase
    rationale, prior prompt versions, judge output, bookkeeping). Keeps only
    the text-bearing signal that drives prompt synthesis. Significantly
    reduces input tokens vs. ``_problem_context``.
    """
    latest_prompt = None
    if state.prompt_versions:
        latest = state.prompt_versions[-1]
        latest_prompt = {"version": latest.version, "prompt": latest.prompt}
    payload = {
        "raw_input": state.raw_input,
        "stated_objective": state.stated_objective,
        "inferred_objective": state.inferred_objective,
        "assumptions": [
            {"assumption": a.assumption, "importance": a.importance}
            for a in state.assumptions
        ],
        "information_gaps": [
            {"gap": g.gap, "importance": g.importance}
            for g in state.information_gaps
        ],
        "expert_panel_questions": [
            {"perspective_name": p.perspective_name, "question": p.question}
            for p in state.expert_panel_perspectives
        ],
        "alternative_framings": [
            {"framing": f.framing} for f in state.alternative_framings
        ],
        "meta_questions": [
            {"question": m.question} for m in state.meta_questions
        ],
        "latest_prompt": latest_prompt,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


T = TypeVar("T")

_LEADING_TEMPLATES = (
    "reframe the issue as",
    "reframe the problem as",
    "treat the problem as",
    "treat the issue as",
    "ask whether",
    "determine whether",
)

ASSUMPTIONS_CAP = 8
INFORMATION_GAPS_CAP = 8
EXPERT_PANEL_CAP = 8
ALTERNATIVE_FRAMINGS_CAP = 8
META_QUESTIONS_CAP = 8


def _norm(s: str) -> str:
    s = s.lower()
    s = s.translate(str.maketrans("", "", string.punctuation))
    s = " ".join(s.split())
    for tpl in sorted(_LEADING_TEMPLATES, key=len, reverse=True):
        if s == tpl:
            return ""
        if s.startswith(tpl + " "):
            s = s[len(tpl) + 1 :]
            break
    return s.strip()


def _merge_unique(
    existing: list[T],
    new: list[T],
    key: Callable[[T], str],
    cap: int | None = None,
) -> list[T]:
    seen = {key(x) for x in existing}
    out = list(existing)
    for item in new:
        if cap is not None and len(out) >= cap:
            break
        k = key(item)
        if k in seen:
            continue
        seen.add(k)
        out.append(item)
    return out


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
        update={
            "assumptions": _merge_unique(
                state.assumptions,
                result.assumptions,
                key=lambda a: _norm(a.assumption),
                cap=ASSUMPTIONS_CAP,
            )
        }
    )


def information_gap_detection(state: ProblemState, llm: LLMProvider) -> ProblemState:
    result = llm.generate_structured(
        prompt=INFORMATION_GAP_DETECTION_PROMPT.replace("{problem_context}", _problem_context(state)),
        output_model=InformationGapResult,
        temperature=PHASE_DEFAULT_TEMPERATURES["INFORMATION_GAP_DETECTION"],
    )
    return state.model_copy(
        update={
            "information_gaps": _merge_unique(
                state.information_gaps,
                result.information_gaps,
                key=lambda g: _norm(g.gap),
                cap=INFORMATION_GAPS_CAP,
            )
        }
    )


def expert_panel_generation(state: ProblemState, llm: LLMProvider) -> ProblemState:
    result = llm.generate_structured(
        prompt=EXPERT_PANEL_GENERATION_PROMPT.replace("{problem_context}", _problem_context(state)),
        output_model=ExpertPanelResult,
        temperature=PHASE_DEFAULT_TEMPERATURES["EXPERT_PANEL_GENERATION"],
    )
    return state.model_copy(
        update={
            "expert_panel_perspectives": _merge_unique(
                state.expert_panel_perspectives,
                result.expert_panel_perspectives,
                key=lambda p: _norm(p.perspective_name + "|" + p.question),
                cap=EXPERT_PANEL_CAP,
            )
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
            "alternative_framings": _merge_unique(
                state.alternative_framings,
                result.alternative_framings,
                key=lambda f: _norm(f.framing),
                cap=ALTERNATIVE_FRAMINGS_CAP,
            )
        }
    )


def meta_question_generation(state: ProblemState, llm: LLMProvider) -> ProblemState:
    result = llm.generate_structured(
        prompt=META_QUESTION_GENERATION_PROMPT.replace("{problem_context}", _problem_context(state)),
        output_model=MetaQuestionResult,
        temperature=PHASE_DEFAULT_TEMPERATURES["META_QUESTION_GENERATION"],
    )
    return state.model_copy(
        update={
            "meta_questions": _merge_unique(
                state.meta_questions,
                result.meta_questions,
                key=lambda m: _norm(m.question),
                cap=META_QUESTIONS_CAP,
            )
        }
    )


def prompt_refinement(state: ProblemState, llm: LLMProvider) -> ProblemState:
    result = llm.generate_structured(
        prompt=PROMPT_REFINEMENT_PROMPT.replace("{problem_context}", _synthesis_context(state)),
        output_model=PromptRefinementResult,
        temperature=PHASE_DEFAULT_TEMPERATURES["PROMPT_REFINEMENT"],
    )
    next_version = PromptVersion(
        version=len(state.prompt_versions),
        prompt=result.prompt,
        revision=result.revision,
    )
    return state.model_copy(
        update={
            "prompt_versions": [*state.prompt_versions, next_version],
            "final_prompt": result.prompt,
        }
    )


def convergence_evaluation(state: ProblemState, llm: LLMProvider) -> ProblemState:
    # Cold start: no synthesis has happened yet, so there is no delta to judge.
    # Short-circuit to NOT_CONVERGED without spending an LLM call.
    if len(state.prompt_versions) < 2:
        cold = ConvergenceResult(
            convergence_status="NOT_CONVERGED",
            rationale="No synthesis has occurred yet; cannot assess a prompt delta.",
            prompt_delta_assessment="No prior synthesized prompt to compare against.",
            remaining_opportunities=[],
        )
        return state.model_copy(
            update={
                "convergence_status": cold.convergence_status,
                "last_convergence": cold,
            }
        )

    prev = state.prompt_versions[-2]
    curr = state.prompt_versions[-1]
    prompt = (
        CONVERGENCE_EVALUATION_PROMPT
        .replace("{previous_prompt}", prev.prompt)
        .replace("{current_prompt}", curr.prompt)
        .replace("{prev_version}", str(prev.version))
        .replace("{current_version}", str(curr.version))
        .replace("{problem_context}", _problem_context(state))
    )
    result = llm.generate_structured(
        prompt=prompt,
        output_model=ConvergenceResult,
        temperature=PHASE_DEFAULT_TEMPERATURES["CONVERGENCE_EVALUATION"],
    )
    return state.model_copy(
        update={
            "convergence_status": result.convergence_status,
            "last_convergence": result,
        }
    )


def loop_should_continue(state: ProblemState) -> bool:
    return state.convergence_status != "CONVERGED"


PhaseHandler = Callable[[ProblemState, LLMProvider], ProblemState]
OnPhase = Callable[[Phase, ProblemState], None]

ANALYSIS_PHASES: list[tuple[Phase, PhaseHandler]] = [
    ("OBJECTIVE_ANALYSIS", objective_analysis),
    ("ASSUMPTION_EXCAVATION", assumption_excavation),
    ("INFORMATION_GAP_DETECTION", information_gap_detection),
    ("EXPERT_PANEL_GENERATION", expert_panel_generation),
    ("ALTERNATIVE_FRAMING", alternative_framing),
    ("META_QUESTION_GENERATION", meta_question_generation),
]
SYNTHESIS_PHASES: list[tuple[Phase, PhaseHandler]] = [
    ("PROMPT_REFINEMENT", prompt_refinement),
]
JUDGMENT_PHASES: list[tuple[Phase, PhaseHandler]] = [
    ("CONVERGENCE_EVALUATION", convergence_evaluation),
]
FULL_PIPELINE: list[tuple[Phase, PhaseHandler]] = (
    ANALYSIS_PHASES + SYNTHESIS_PHASES + JUDGMENT_PHASES
)


def run_pipeline(
    state: ProblemState,
    llm: LLMProvider,
    pipeline: list[tuple[Phase, PhaseHandler]],
    *,
    on_phase: OnPhase | None = None,
) -> ProblemState:
    for phase, handler in pipeline:
        state = transition_to_phase(state, phase)
        state = handler(state, llm)
        if on_phase is not None:
            on_phase(phase, state)
    return state


def _coerce(state_or_input: str | ProblemState) -> ProblemState:
    if isinstance(state_or_input, ProblemState):
        return state_or_input
    return initialize_state(state_or_input)


def analyze(
    state_or_input: str | ProblemState,
    llm: LLMProvider,
    *,
    on_phase: OnPhase | None = None,
) -> ProblemState:
    return run_pipeline(_coerce(state_or_input), llm, ANALYSIS_PHASES, on_phase=on_phase)


def synthesize(
    state: ProblemState,
    llm: LLMProvider,
    *,
    on_phase: OnPhase | None = None,
) -> ProblemState:
    return run_pipeline(state, llm, SYNTHESIS_PHASES, on_phase=on_phase)


def judge(
    state: ProblemState,
    llm: LLMProvider,
    *,
    on_phase: OnPhase | None = None,
) -> ProblemState:
    return run_pipeline(state, llm, JUDGMENT_PHASES, on_phase=on_phase)


def run(
    raw_input: str,
    llm: LLMProvider,
    *,
    max_iterations: int = 5,
    on_phase: OnPhase | None = None,
) -> ProblemState:
    state = initialize_state(raw_input)
    for _ in range(max_iterations):
        state = run_pipeline(state, llm, FULL_PIPELINE, on_phase=on_phase)
        if not loop_should_continue(state):
            break
    return state
