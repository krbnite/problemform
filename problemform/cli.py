from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown

import problemform.config  # noqa: F401  triggers load_dotenv()
from problemform.cli_render import render_markdown
from problemform.core.language_models import StructuredOutputError, make_provider
from problemform.core.state import transition_to_phase
from problemform.core.workflow import (
    alternative_framing,
    analyze as do_analyze,
    assumption_excavation,
    convergence_evaluation,
    expert_panel_generation,
    information_gap_detection,
    judge as do_judge,
    meta_question_generation,
    objective_analysis,
    prompt_refinement,
    run as do_run,
    synthesize as do_synthesize,
)
from problemform.models import Phase, ProblemState

app = typer.Typer(help="ProblemForm: collaborative problem formulation.")
console = Console()
err = Console(stderr=True)


FormatOpt = typer.Option("md", "--format", "-f", help="md or json")
ProviderOpt = typer.Option(None, "--provider", "-p", help="openai or anthropic")
ModelOpt = typer.Option(None, "--model", "-m")
SaveOpt = typer.Option(
    None,
    "--save",
    help="Write resulting ProblemState JSON to PATH ('-' for stdout)",
)
StateOpt = typer.Option(
    None,
    "--state",
    help="Load a ProblemState JSON from PATH ('-' for stdin)",
)
CheckpointOpt = typer.Option(
    None,
    "--checkpoint",
    help="Write ProblemState JSON to PATH after every phase (recoverable on Ctrl-C)",
)


def _die(msg: str) -> None:
    err.print(f"[red]error:[/red] {msg}")
    raise typer.Exit(2)


def _load_state(path: Path | None) -> ProblemState | None:
    if path is None:
        return None
    if str(path) == "-":
        text = sys.stdin.read()
    else:
        try:
            text = Path(path).read_text()
        except OSError as exc:
            _die(f"could not read state file {path}: {exc}")
    try:
        return ProblemState.model_validate_json(text)
    except ValueError as exc:
        _die(f"failed to parse state JSON at {path}: {exc}")


def _write_text_or_die(path: Path, text: str) -> None:
    """Write a file, surfacing OSError as a friendly CLI error."""
    try:
        path.write_text(text)
    except OSError as exc:
        _die(f"could not write file {path}: {exc}")


def _make_provider_or_die(provider, model):
    """Build a provider, surfacing the two known user-facing init errors."""
    try:
        return make_provider(provider, model)
    except ValueError as exc:
        # Unknown provider name from make_provider.
        _die(f"provider error: {exc}")
    except ImportError as exc:
        # SDK extra not installed (raised by the lazy import inside the provider).
        _die(str(exc))


@contextmanager
def _structured_output_errors():
    """Convert provider structured-output failures into a clean CLI error.

    Catches the public umbrella ``StructuredOutputError`` (and its subclasses
    ``TruncatedResponseError``, ``RefusalError``, ``EmptyResponseError``,
    ``ContentFilterError``) without intercepting unexpected errors.
    """
    try:
        yield
    except StructuredOutputError as exc:
        _die(f"LLM provider error: {exc}")


def _save_state(state: ProblemState, path: Path | None) -> bool:
    """Save the state. Returns True if stdout was consumed by the save."""
    if path is None:
        return False
    payload = state.model_dump_json(indent=2)
    if str(path) == "-":
        sys.stdout.write(payload + "\n")
        return True
    _write_text_or_die(Path(path), payload)
    return False


def _emit(state: ProblemState, fmt: str) -> None:
    if fmt == "json":
        console.print_json(state.model_dump_json())
    elif fmt == "md":
        console.print(Markdown(render_markdown(state)))
    else:
        _die(f"unknown --format {fmt!r}; expected 'md' or 'json'")


def _progress(phase: Phase, _state: ProblemState) -> None:
    err.log(f"[dim]✓ {phase}")


def _make_progress(checkpoint: Path | None):
    if checkpoint is None:
        return _progress

    def on_phase(phase: Phase, state: ProblemState) -> None:
        _write_text_or_die(Path(checkpoint), state.model_dump_json(indent=2))
        err.log(f"[dim]✓ {phase} (checkpoint: {checkpoint})")

    return on_phase


@app.command()
def analyze(
    prompt: str = typer.Argument(None, help="Raw input prompt (omit if --state given)"),
    state: Path = StateOpt,
    provider: str = ProviderOpt,
    model: str = ModelOpt,
    format: str = FormatOpt,
    save: Path = SaveOpt,
    checkpoint: Path = CheckpointOpt,
) -> None:
    """Run all six analytical phases. No synthesis or judgment."""
    loaded = _load_state(state)
    base: str | ProblemState | None = loaded if loaded is not None else prompt
    if base is None:
        _die("PROMPT or --state required")
    provider_obj = _make_provider_or_die(provider, model)
    with _structured_output_errors():
        out = do_analyze(base, provider_obj, on_phase=_make_progress(checkpoint))
    if not _save_state(out, save):
        _emit(out, format)


@app.command()
def synthesize(
    state: Path = StateOpt,
    provider: str = ProviderOpt,
    model: str = ModelOpt,
    format: str = FormatOpt,
    save: Path = SaveOpt,
) -> None:
    """Generate a refined prompt from an existing ProblemState."""
    s = _load_state(state)
    if s is None:
        _die("--state required for synthesize")
    provider_obj = _make_provider_or_die(provider, model)
    with _structured_output_errors():
        out = do_synthesize(s, provider_obj)
    if not _save_state(out, save):
        _emit(out, format)


@app.command()
def judge(
    state: Path = StateOpt,
    provider: str = ProviderOpt,
    model: str = ModelOpt,
    format: str = FormatOpt,
    save: Path = SaveOpt,
) -> None:
    """Evaluate whether the current formulation has converged."""
    s = _load_state(state)
    if s is None:
        _die("--state required for judge")
    provider_obj = _make_provider_or_die(provider, model)
    with _structured_output_errors():
        out = do_judge(s, provider_obj)
    if not _save_state(out, save):
        _emit(out, format)


@app.command()
def run(
    prompt: str = typer.Argument(..., help="Raw input prompt"),
    max_iterations: int = typer.Option(1, "--max-iterations", min=1),
    provider: str = ProviderOpt,
    model: str = ModelOpt,
    format: str = FormatOpt,
    save: Path = SaveOpt,
    checkpoint: Path = CheckpointOpt,
) -> None:
    """Loop the full pipeline until CONVERGED or max_iterations."""
    provider_obj = _make_provider_or_die(provider, model)
    with _structured_output_errors():
        out = do_run(
            prompt,
            provider_obj,
            max_iterations=max_iterations,
            on_phase=_make_progress(checkpoint),
        )
    if not _save_state(out, save):
        _emit(out, format)


AGENT_COMMANDS: dict[str, tuple[Phase, "object"]] = {
    "objective-analysis":         ("OBJECTIVE_ANALYSIS",         objective_analysis),
    "assumption-excavation":      ("ASSUMPTION_EXCAVATION",      assumption_excavation),
    "information-gap-detection":  ("INFORMATION_GAP_DETECTION",  information_gap_detection),
    "expert-panel":               ("EXPERT_PANEL_GENERATION",    expert_panel_generation),
    "alternative-framing":        ("ALTERNATIVE_FRAMING",        alternative_framing),
    "meta-questions":             ("META_QUESTION_GENERATION",   meta_question_generation),
    "prompt-synthesis":           ("PROMPT_REFINEMENT",          prompt_refinement),
    "convergence-evaluation":     ("CONVERGENCE_EVALUATION",     convergence_evaluation),
}


@app.command()
def agent(
    name: str = typer.Argument(..., help="Agent name (e.g. prompt-synthesis)"),
    state_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        help="ProblemState JSON path",
    ),
    provider: str = ProviderOpt,
    model: str = ModelOpt,
    format: str = FormatOpt,
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Write the updated ProblemState JSON to PATH (default: print to stdout)",
    ),
) -> None:
    """Run a single ProblemForm phase against an existing ProblemState.

    Supported agents:
      objective-analysis, assumption-excavation, information-gap-detection,
      expert-panel, alternative-framing, meta-questions,
      prompt-synthesis, convergence-evaluation
    """
    entry = AGENT_COMMANDS.get(name)
    if entry is None:
        supported = ", ".join(AGENT_COMMANDS.keys())
        _die(f"Unknown agent {name!r}. Supported: {supported}")
    phase, handler = entry

    s = _load_state(state_path)
    s = transition_to_phase(s, phase)
    provider_obj = _make_provider_or_die(provider, model)
    with _structured_output_errors():
        out = handler(s, provider_obj)

    if output is None:
        _emit(out, format)
    else:
        _write_text_or_die(Path(output), out.model_dump_json(indent=2))


@app.command()
def explain(
    state: Path = typer.Argument(..., help="ProblemState JSON path ('-' for stdin)"),
) -> None:
    """Render a ProblemState as Markdown for inspection."""
    s = _load_state(state)
    if s is None:
        _die("state required")
    console.print(Markdown(render_markdown(s)))


@app.command()
def export(
    state: Path = typer.Argument(..., help="ProblemState JSON path ('-' for stdin)"),
    output: Path = typer.Option(None, "--output", "-o"),
    format: str = FormatOpt,
) -> None:
    """Persist a ProblemState as JSON or Markdown."""
    s = _load_state(state)
    if s is None:
        _die("state required")
    if format == "json":
        text = s.model_dump_json(indent=2)
    elif format == "md":
        text = render_markdown(s)
    else:
        _die(f"unknown --format {format!r}; expected 'md' or 'json'")
        return
    if output is None:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")
    else:
        _write_text_or_die(Path(output), text)


if __name__ == "__main__":
    app()
