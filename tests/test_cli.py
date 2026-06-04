from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from problemform import cli as cli_module
from problemform.cli import app
from problemform.models import ProblemState


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def _patch_provider(monkeypatch, stub_llm):
    monkeypatch.setattr(cli_module, "make_provider", lambda *a, **kw: stub_llm)


def _state_from_json(text: str) -> ProblemState:
    return ProblemState.model_validate_json(text)


def test_analyze_runs_six_analytical_phases_no_synthesis(runner):
    result = runner.invoke(app, ["analyze", "q", "--save", "-", "--format", "json"])
    assert result.exit_code == 0, result.stderr
    state = _state_from_json(result.stdout)
    assert state.assumptions
    assert state.information_gaps
    assert state.expert_panel_perspectives
    assert state.alternative_framings
    assert state.meta_questions
    assert len(state.prompt_versions) == 1
    assert state.convergence_status == "NOT_CONVERGED"


def test_synthesize_requires_state(runner):
    result = runner.invoke(app, ["synthesize"])
    assert result.exit_code == 2


def test_synthesize_appends_prompt_version(runner, tmp_path: Path):
    analyzed = runner.invoke(app, ["analyze", "q", "--save", "-", "--format", "json"])
    state_path = tmp_path / "state.json"
    state_path.write_text(analyzed.stdout)

    result = runner.invoke(
        app, ["synthesize", "--state", str(state_path), "--save", "-", "--format", "json"]
    )
    assert result.exit_code == 0, result.stderr
    state = _state_from_json(result.stdout)
    assert len(state.prompt_versions) == 2
    assert state.prompt_versions[-1].revision is not None


def test_judge_requires_state(runner):
    assert runner.invoke(app, ["judge"]).exit_code == 2


def test_judge_short_circuits_when_no_synthesis_yet(runner, tmp_path: Path):
    # Cold-start: only v0 exists. Judge should not call the LLM and should
    # return NOT_CONVERGED since there is no delta to assess.
    analyzed = runner.invoke(app, ["analyze", "q", "--save", "-", "--format", "json"])
    state_path = tmp_path / "state.json"
    state_path.write_text(analyzed.stdout)

    result = runner.invoke(
        app, ["judge", "--state", str(state_path), "--save", "-", "--format", "json"]
    )
    assert result.exit_code == 0, result.stderr
    state = _state_from_json(result.stdout)
    assert state.convergence_status == "NOT_CONVERGED"
    assert state.last_convergence is not None
    assert state.last_convergence.prompt_delta_assessment == (
        "No prior synthesized prompt to compare against."
    )


def test_judge_updates_convergence_status_after_synthesis(runner, tmp_path: Path):
    analyzed = runner.invoke(app, ["analyze", "q", "--save", "-", "--format", "json"])
    a_path = tmp_path / "a.json"
    a_path.write_text(analyzed.stdout)
    synthesized = runner.invoke(
        app, ["synthesize", "--state", str(a_path), "--save", "-", "--format", "json"]
    )
    s_path = tmp_path / "s.json"
    s_path.write_text(synthesized.stdout)

    result = runner.invoke(
        app, ["judge", "--state", str(s_path), "--save", "-", "--format", "json"]
    )
    assert result.exit_code == 0, result.stderr
    state = _state_from_json(result.stdout)
    assert state.convergence_status == "NEAR_CONVERGENCE"


def test_run_default_max_iterations_is_one(runner):
    # stub returns NEAR_CONVERGENCE on the 1st convergence call and CONVERGED on the 2nd.
    # With the new default of --max-iterations=1, only one convergence call fires,
    # so the final state should still be NEAR_CONVERGENCE.
    result = runner.invoke(app, ["run", "q", "--format", "json"])
    assert result.exit_code == 0, result.stderr
    state = _state_from_json(result.stdout)
    assert state.convergence_status == "NEAR_CONVERGENCE"


def test_run_to_convergence(runner):
    result = runner.invoke(
        app, ["run", "q", "--max-iterations", "3", "--format", "json"]
    )
    assert result.exit_code == 0, result.stderr
    state = _state_from_json(result.stdout)
    assert state.convergence_status == "CONVERGED"
    assert state.final_prompt is not None


def test_explain_renders_markdown(runner, tmp_path: Path):
    run_res = runner.invoke(app, ["run", "q", "--save", str(tmp_path / "s.json")])
    assert run_res.exit_code == 0
    explain = runner.invoke(app, ["explain", str(tmp_path / "s.json")])
    assert explain.exit_code == 0
    assert "Convergence" in explain.stdout


def test_export_json_roundtrip(runner, tmp_path: Path):
    state_path = tmp_path / "s.json"
    out_path = tmp_path / "out.json"
    assert runner.invoke(app, ["run", "q", "--save", str(state_path)]).exit_code == 0
    res = runner.invoke(
        app, ["export", str(state_path), "--format", "json", "-o", str(out_path)]
    )
    assert res.exit_code == 0
    a = _state_from_json(state_path.read_text())
    b = _state_from_json(out_path.read_text())
    assert a == b


def test_run_checkpoint_writes_state_after_each_phase(runner, tmp_path: Path):
    cp = tmp_path / "cp.json"
    result = runner.invoke(
        app, ["run", "q", "--max-iterations", "2", "--checkpoint", str(cp), "--save", str(tmp_path / "final.json")]
    )
    assert result.exit_code == 0, result.stderr
    assert cp.exists()
    # Last write should match the final state (CONVERGED) since checkpoint runs every phase.
    cp_state = ProblemState.model_validate_json(cp.read_text())
    final = ProblemState.model_validate_json((tmp_path / "final.json").read_text())
    assert cp_state.convergence_status == final.convergence_status == "CONVERGED"


def test_analyze_checkpoint_recovers_partial_state(runner, tmp_path: Path, monkeypatch, stub_llm):
    cp = tmp_path / "cp.json"

    # Force analysis to crash mid-pipeline so we can inspect the checkpoint.
    class HalfwayCrash:
        def __init__(self, inner): self._inner = inner; self.calls = 0
        def generate_text(self, *a, **kw): return self._inner.generate_text(*a, **kw)
        def generate_structured(self, prompt, output_model, **kw):
            self.calls += 1
            if self.calls > 3:
                raise RuntimeError("boom")
            return self._inner.generate_structured(prompt, output_model, **kw)

    monkeypatch.setattr(cli_module, "make_provider", lambda *a, **kw: HalfwayCrash(stub_llm))
    result = runner.invoke(app, ["analyze", "q", "--checkpoint", str(cp)])
    assert result.exit_code != 0  # crashed
    assert cp.exists()
    recovered = ProblemState.model_validate_json(cp.read_text())
    # First three phases (objective, assumption, info gap) completed before the crash.
    assert recovered.stated_objective == "stated"
    assert recovered.assumptions
    assert recovered.information_gaps
    assert not recovered.expert_panel_perspectives  # didn't get here


def test_provider_and_model_flags_reach_make_provider(runner, monkeypatch, stub_llm):
    calls: list[tuple] = []

    def recorder(provider=None, model=None):
        calls.append((provider, model))
        return stub_llm

    monkeypatch.setattr(cli_module, "make_provider", recorder)
    result = runner.invoke(
        app, ["analyze", "q", "--provider", "anthropic", "--model", "claude-opus-4-8"]
    )
    assert result.exit_code == 0, result.stderr
    assert calls == [("anthropic", "claude-opus-4-8")]


def test_provider_short_flags_reach_make_provider(runner, monkeypatch, stub_llm):
    calls: list[tuple] = []
    monkeypatch.setattr(
        cli_module,
        "make_provider",
        lambda provider=None, model=None: (calls.append((provider, model)), stub_llm)[1],
    )
    result = runner.invoke(
        app, ["run", "q", "-p", "anthropic", "-m", "claude-sonnet-4-6"]
    )
    assert result.exit_code == 0, result.stderr
    assert calls[0] == ("anthropic", "claude-sonnet-4-6")


def test_provider_defaults_when_no_flags(runner, monkeypatch, stub_llm):
    calls: list[tuple] = []
    monkeypatch.setattr(
        cli_module,
        "make_provider",
        lambda provider=None, model=None: (calls.append((provider, model)), stub_llm)[1],
    )
    result = runner.invoke(app, ["analyze", "q"])
    assert result.exit_code == 0, result.stderr
    assert calls == [(None, None)]  # make_provider itself resolves env/defaults


def test_pipe_chain_analyze_into_synthesize(runner):
    analyzed = runner.invoke(app, ["analyze", "q", "--save", "-", "--format", "json"])
    assert analyzed.exit_code == 0
    json.loads(analyzed.stdout)  # well-formed

    piped = runner.invoke(
        app,
        ["synthesize", "--state", "-", "--save", "-", "--format", "json"],
        input=analyzed.stdout,
    )
    assert piped.exit_code == 0, piped.stderr
    state = _state_from_json(piped.stdout)
    assert len(state.prompt_versions) == 2


# ---------- agent command ---------------------------------------------------


def _bootstrap_state(runner, tmp_path: Path) -> Path:
    """Run analyze and persist the result; return the state file path."""
    state_path = tmp_path / "state.json"
    res = runner.invoke(app, ["analyze", "q", "--save", str(state_path)])
    assert res.exit_code == 0, res.stderr
    return state_path


def test_agent_runs_objective_analysis_writes_output_file(runner, tmp_path: Path):
    state_path = _bootstrap_state(runner, tmp_path)
    out_path = tmp_path / "out.json"
    res = runner.invoke(
        app, ["agent", "objective-analysis", str(state_path), "--output", str(out_path)]
    )
    assert res.exit_code == 0, res.stderr
    assert out_path.exists()
    state = ProblemState.model_validate_json(out_path.read_text())
    assert state.stated_objective == "stated"


def test_agent_runs_prompt_synthesis_on_analyzed_state(runner, tmp_path: Path):
    state_path = _bootstrap_state(runner, tmp_path)
    out_path = tmp_path / "out.json"
    res = runner.invoke(
        app, ["agent", "prompt-synthesis", str(state_path), "--output", str(out_path)]
    )
    assert res.exit_code == 0, res.stderr
    state = ProblemState.model_validate_json(out_path.read_text())
    assert len(state.prompt_versions) == 2
    assert state.final_prompt is not None


def test_agent_runs_convergence_evaluation_after_synthesis(runner, tmp_path: Path):
    analyzed = _bootstrap_state(runner, tmp_path)
    after_synth = tmp_path / "synth.json"
    assert runner.invoke(
        app,
        ["agent", "prompt-synthesis", str(analyzed), "--output", str(after_synth)],
    ).exit_code == 0

    after_judge = tmp_path / "judge.json"
    res = runner.invoke(
        app,
        ["agent", "convergence-evaluation", str(after_synth), "--output", str(after_judge)],
    )
    assert res.exit_code == 0, res.stderr
    state = ProblemState.model_validate_json(after_judge.read_text())
    assert state.convergence_status == "NEAR_CONVERGENCE"
    assert state.last_convergence is not None


def test_agent_invalid_name_errors_cleanly(runner, tmp_path: Path):
    state_path = _bootstrap_state(runner, tmp_path)
    res = runner.invoke(app, ["agent", "flarble", str(state_path)])
    assert res.exit_code == 2
    # error lists every supported name so the user can self-correct
    for name in [
        "objective-analysis",
        "assumption-excavation",
        "information-gap-detection",
        "expert-panel",
        "alternative-framing",
        "meta-questions",
        "prompt-synthesis",
        "convergence-evaluation",
    ]:
        assert name in res.stderr


def test_agent_missing_state_file_errors(runner, tmp_path: Path):
    missing = tmp_path / "does-not-exist.json"
    res = runner.invoke(app, ["agent", "objective-analysis", str(missing)])
    assert res.exit_code != 0


def test_agent_malformed_state_json_errors(runner, tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json {{{")
    res = runner.invoke(app, ["agent", "objective-analysis", str(bad)])
    assert res.exit_code == 2
    assert "failed to parse state JSON" in res.stderr


def test_agent_prints_to_stdout_when_no_output_flag(runner, tmp_path: Path):
    state_path = _bootstrap_state(runner, tmp_path)
    res = runner.invoke(
        app,
        ["agent", "objective-analysis", str(state_path), "--format", "json"],
    )
    assert res.exit_code == 0, res.stderr
    state = _state_from_json(res.stdout)
    assert state.stated_objective == "stated"


# ---------- max_iterations validation --------------------------------------


def test_run_zero_max_iterations_is_rejected(runner):
    res = runner.invoke(app, ["run", "q", "--max-iterations", "0"])
    assert res.exit_code != 0
    assert "max-iterations" in (res.stderr + res.output).lower() or "0" in (res.stderr + res.output)


def test_run_negative_max_iterations_is_rejected(runner):
    res = runner.invoke(app, ["run", "q", "--max-iterations", "-3"])
    assert res.exit_code != 0


# ---------- agent updates state.phase --------------------------------------


@pytest.mark.parametrize(
    "agent_name, expected_phase",
    [
        ("objective-analysis",        "OBJECTIVE_ANALYSIS"),
        ("assumption-excavation",     "ASSUMPTION_EXCAVATION"),
        ("information-gap-detection", "INFORMATION_GAP_DETECTION"),
        ("expert-panel",              "EXPERT_PANEL_GENERATION"),
        ("alternative-framing",       "ALTERNATIVE_FRAMING"),
        ("meta-questions",            "META_QUESTION_GENERATION"),
        ("prompt-synthesis",          "PROMPT_REFINEMENT"),
        ("convergence-evaluation",    "CONVERGENCE_EVALUATION"),
    ],
)
def test_agent_updates_state_phase(runner, tmp_path: Path, agent_name, expected_phase):
    state_path = _bootstrap_state(runner, tmp_path)
    out_path = tmp_path / "out.json"
    res = runner.invoke(
        app,
        ["agent", agent_name, str(state_path), "--output", str(out_path)],
    )
    assert res.exit_code == 0, res.stderr
    state = ProblemState.model_validate_json(out_path.read_text())
    assert state.phase == expected_phase
