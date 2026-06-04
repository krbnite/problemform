# helper functions for updating state
from problemform.models import ProblemState, Revision, Phase

def initialize_state(raw_input: str) -> ProblemState:
    state = ProblemState(raw_input=raw_input)
    state.add_prompt_version(
        prompt=raw_input,
        revision=Revision(
            phase="INITIAL_INPUT",
            description="Initial user input captured as v0.",
        ),
    )
    return state

def transition_to_phase(
    state: ProblemState, 
    phase: Phase,
) -> ProblemState:
    return state.model_copy(update={"phase": phase})    