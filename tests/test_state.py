from problemform.core.state import initialize_state, transition_to_phase
from problemform.models import Revision


def test_initialize_state_seeds_v0_prompt_version():
    state = initialize_state("hello")
    assert state.raw_input == "hello"
    assert state.phase == "INITIAL_INPUT"
    assert state.convergence_status == "NOT_CONVERGED"
    assert len(state.prompt_versions) == 1
    assert state.prompt_versions[0].version == 0
    assert state.prompt_versions[0].prompt == "hello"


def test_transition_to_phase_is_immutable():
    state = initialize_state("hello")
    moved = transition_to_phase(state, "OBJECTIVE_ANALYSIS")
    assert moved.phase == "OBJECTIVE_ANALYSIS"
    assert state.phase == "INITIAL_INPUT"


def test_add_prompt_version_versions_are_monotonic():
    state = initialize_state("hello")
    state.add_prompt_version(
        "v1", revision=Revision(phase="PROMPT_REFINEMENT", description="d")
    )
    state.add_prompt_version(
        "v2", revision=Revision(phase="PROMPT_REFINEMENT", description="d")
    )
    versions = [pv.version for pv in state.prompt_versions]
    assert versions == [0, 1, 2]
