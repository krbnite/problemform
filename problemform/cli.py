from __future__ import annotations

import os
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


@app.command()
def benchmark(
    suite: Path = typer.Argument(
        ..., exists=True, file_okay=False, dir_okay=True, readable=True,
        help="Path to a benchmarks suite directory (YAML test cases)",
    ),
    pf_provider: str = typer.Option(None, "--pf-provider"),
    pf_model: str = typer.Option(None, "--pf-model"),
    answer_provider: str = typer.Option(None, "--answer-provider"),
    answer_model: str = typer.Option(None, "--answer-model"),
    judge_provider: str = typer.Option(None, "--judge-provider"),
    judge_model: str = typer.Option(None, "--judge-model"),
    rubric: list[Path] = typer.Option(
        None, "--rubric",
        help="Rubric YAML file or directory (repeatable). Overrides the shipped "
             "default rubrics when given.",
    ),
    property_suite: list[Path] = typer.Option(
        None, "--property-suite",
        help="Property-suite YAML file or directory (repeatable). Overrides the "
             "shipped default suites when given. (Per-case expected_properties "
             "always activate regardless of this flag.)",
    ),
    answer_comparison: bool | None = typer.Option(
        None, "--answer-comparison/--no-answer-comparison",
        help="Force the M3A answer-comparison lens on/off for all cases "
             "(default: per-formulation-type policy).",
    ),
    max_iterations: int = typer.Option(1, "--max-iterations", min=1),
    output: Path = typer.Option(
        None, "--output",
        help="Run directory (default: .problemform/eval_runs/<auto-id>/)",
    ),
    format: str = FormatOpt,
) -> None:
    """Run a YAML test-case suite end-to-end and write JSON + Markdown reports.

    Uses three provider roles: ProblemForm (refines the prompt), Answer
    (generates raw and refined answers), and Judge (compares them). Each role
    has its own --*-provider / --*-model flags; unset flags fall through to
    the defaults already used by `problemform run`.

    Rubric and property lenses (M3B) run alongside the M3A comparative judgment:
    without --rubric / --property-suite the shipped defaults load; explicit flags
    override the defaults. Each case's expected_properties activate as
    formulation-target checks in every run.
    """
    # Lazy imports so eval is loaded only when the command runs.
    from problemform.eval.corpus import (
        CorpusError,
        load_property_suite,
        load_rubrics,
        load_test_cases,
    )
    from problemform.eval.defaults import (
        load_default_properties,
        load_default_rubrics,
    )
    from problemform.eval.engine import _detect_same_family, run_benchmark
    from problemform.eval.policy import answer_comparison_applies
    from problemform.eval.report import write_run

    try:
        cases = load_test_cases(suite)
    except CorpusError as exc:
        _die(str(exc))
    if not cases:
        _die(f"no YAML test cases found in {suite}")

    # Resolve the rubric + property lenses: explicit flags override the shipped
    # defaults; absent flags fall back to benchmarks/rubrics + benchmarks/properties.
    if rubric:
        try:
            rubrics = [r for path in rubric for r in load_rubrics(path)]
        except CorpusError as exc:
            _die(str(exc))
    else:
        rubrics, reason = load_default_rubrics()
        if reason:
            err.print(f"[yellow]warning:[/yellow] {reason}")

    if property_suite:
        try:
            property_suites = [p for path in property_suite for p in load_property_suite(path)]
        except CorpusError as exc:
            _die(str(exc))
    else:
        property_suites, reason = load_default_properties()
        if reason:
            err.print(f"[yellow]warning:[/yellow] {reason}")

    # Resolve role-specific env vars before falling through to make_provider's
    # generic PROBLEMFORM_PROVIDER / PROBLEMFORM_MODEL fallback. Precedence:
    # CLI flag > role-specific env var > generic env var > built-in default.
    # The PROBLEMFORM_EVAL_* prefix scopes these to the evaluation framework;
    # they do NOT affect the workflow's convergence judge.
    answer_provider = answer_provider or os.environ.get("PROBLEMFORM_EVAL_ANSWER_PROVIDER")
    answer_model = answer_model or os.environ.get("PROBLEMFORM_EVAL_ANSWER_MODEL")
    judge_provider = judge_provider or os.environ.get("PROBLEMFORM_EVAL_JUDGE_PROVIDER")
    judge_model = judge_model or os.environ.get("PROBLEMFORM_EVAL_JUDGE_MODEL")

    # M3B-β.1: only build the answer provider when at least one case will use the
    # M3A answer-comparison lens (per-type policy, honoring the CLI override). A
    # wholly formulation-only corpus (or --no-answer-comparison) needs no answer
    # provider and emits no same-family warning. Providers are built in the
    # pf → answer → judge order.
    will_run_answer_lens = any(
        answer_comparison_applies(c.formulation_type, override=answer_comparison)
        for c in cases
    )

    pf_provider_obj = _make_provider_or_die(pf_provider, pf_model)
    if will_run_answer_lens:
        answer_provider_obj = _make_provider_or_die(answer_provider, answer_model)
        answer_provider_name = answer_provider_obj.__class__.__name__
        answer_provider_model = answer_provider_obj.model
    else:
        answer_provider_obj = None
        answer_provider_name = answer_provider_model = "not_used"
    judge_provider_obj = _make_provider_or_die(judge_provider, judge_model)

    bias_warnings: list[str] = []
    if will_run_answer_lens:
        warn = _detect_same_family(
            answer_provider_obj.__class__.__name__, answer_provider_obj.model,
            judge_provider_obj.__class__.__name__, judge_provider_obj.model,
        )
        if warn:
            err.print(f"[yellow]warning:[/yellow] {warn}")
            bias_warnings.append(warn)

    if output is None:
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        output = Path(".problemform/eval_runs") / ts

    config = {
        "pf_provider": pf_provider_obj.__class__.__name__,
        "pf_model": pf_provider_obj.model,
        "answer_provider": answer_provider_name,
        "answer_model": answer_provider_model,
        "judge_provider": judge_provider_obj.__class__.__name__,
        "judge_model": judge_provider_obj.model,
        "max_iterations": max_iterations,
        "position_randomized": True,
        "judgments_per_pair": 1,
        "answer_comparison": (
            "forced_on" if answer_comparison is True
            else "forced_off" if answer_comparison is False
            else "per_type_policy"
        ),
    }

    err.print(f"[dim]Running benchmark over {len(cases)} cases; output: {output}")

    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table

    from problemform.eval.engine import ProgressEvent
    from problemform.eval.report import format_seconds as _fmt_seconds

    progress = Progress(
        SpinnerColumn(),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("{task.description}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=err,
        transient=False,
    )

    with progress, _structured_output_errors():
        task_id = progress.add_task("", total=len(cases))

        def on_progress(event: ProgressEvent) -> None:
            if event.kind == "run_start":
                progress.update(task_id, description="[dim]starting…")
                return
            if event.kind == "case_start":
                assert event.case is not None
                progress.update(
                    task_id,
                    description=f"[bold]{event.case.name}[/bold]",
                )
                return
            if event.kind == "step":
                assert event.case is not None and event.step is not None
                progress.update(
                    task_id,
                    description=f"[bold]{event.case.name}[/bold] · [cyan]{event.step}[/cyan]",
                )
                progress.console.print(
                    f"[dim]\\[{event.case_index + 1}/{event.total}] "
                    f"{event.case.name} · {event.step}[/dim]"
                )
                return
            if event.kind in ("case_done", "case_errored"):
                assert event.case is not None
                elapsed = _fmt_seconds(sum((event.timing or {}).values()))
                if event.kind == "case_done":
                    progress.console.print(
                        f"[green]✓[/green] {event.case.name} ({elapsed})"
                    )
                else:
                    err_summary = "; ".join(event.errors or []) or "no detail"
                    progress.console.print(
                        f"[red]✗[/red] {event.case.name} ({elapsed}) — errors: {err_summary}"
                    )
                progress.advance(task_id)
                return
            if event.kind == "run_done":
                progress.update(task_id, description="[dim]done")
                return

        report = run_benchmark(
            cases,
            pf_provider=pf_provider_obj,
            answer_provider=answer_provider_obj,
            judge_provider=judge_provider_obj,
            output_dir=output,
            max_iterations=max_iterations,
            rubrics=rubrics,
            property_suites=property_suites,
            answer_comparison_override=answer_comparison,
            config=config,
            bias_warnings=bias_warnings,
            on_progress=on_progress,
        )

    # Run-level role breakdown headline (stderr).
    rt = report.aggregate_runtime
    err.print(
        f"[bold]Run total:[/bold] {_fmt_seconds(rt.total_seconds)} "
        f"(PF {_fmt_seconds(rt.pf_seconds)}, "
        f"Answer {_fmt_seconds(rt.answer_seconds)}, "
        f"Judge {_fmt_seconds(rt.judge_seconds)}, "
        f"Rubric {_fmt_seconds(rt.rubric_seconds)}, "
        f"Property {_fmt_seconds(rt.property_seconds)})"
    )

    # Per-case timing breakdown (stderr; report contents unchanged).
    timing_table = Table(title="Per-case timing", show_lines=False)
    timing_table.add_column("Case", overflow="fold")
    timing_table.add_column("Total", justify="right")
    timing_table.add_column("PF", justify="right")
    timing_table.add_column("Raw", justify="right")
    timing_table.add_column("Refined", justify="right")
    timing_table.add_column("Judge", justify="right")
    timing_table.add_column("Rubric", justify="right")
    timing_table.add_column("Property", justify="right")
    for r in report.test_case_results:
        t = r.timing or {}
        total_s = sum(t.values())
        timing_table.add_row(
            r.test_case.name,
            _fmt_seconds(total_s),
            _fmt_seconds(t.get("pf_run", 0.0)) if "pf_run" in t else "—",
            _fmt_seconds(t.get("raw_answer", 0.0)) if "raw_answer" in t else "—",
            _fmt_seconds(t.get("refined_answer", 0.0)) if "refined_answer" in t else "—",
            _fmt_seconds(t.get("judge", 0.0)) if "judge" in t else "—",
            _fmt_seconds(t.get("rubric", 0.0)) if "rubric" in t else "—",
            _fmt_seconds(t.get("property", 0.0)) if "property" in t else "—",
        )
    err.print(timing_table)

    write_run(report, output)

    # Emit the requested format to stdout for piping.
    if format == "json":
        console.print_json(report.model_dump_json())
    elif format == "md":
        from problemform.eval.report import render_markdown as render_eval_md
        console.print(Markdown(render_eval_md(report)))
    else:
        _die(f"unknown --format {format!r}; expected 'md' or 'json'")


if __name__ == "__main__":
    app()
