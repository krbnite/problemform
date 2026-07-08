# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

ProblemForm is a human-AI collaborative **problem-formulation** system. Its goal is not to answer the user's question but to iteratively refine the question/prompt/problem statement itself until convergence. Treat the authoritative spec as `docs/problemform_constitution.md` — when implementation decisions are ambiguous, defer to the Constitution's phase definitions and to `docs/architecture.md`.

## Status

Milestones 1 (Pure Python Core) and 2 (CLI) of `docs/roadmap.md` are complete. The end-to-end pipeline runs through both providers, every phase has working handlers and prompts, dedup/caps bound the artifact lists, the synthesizer receives a compact context, the convergence judge is driven by prompt-delta materiality, and the `problemform` CLI exposes `analyze` / `synthesize` / `judge` / `run` / `explain` / `export` / `agent` (single-phase dispatch).

**Immediate next milestone is M3: Prompt Evaluation.** This is a deliberate architectural shift — evaluation infrastructure is now considered a prerequisite to LangGraph (M4). Before orchestration complexity, the project will establish rubric-based prompt and answer evaluation, golden test sets, comparative scoring between raw and refined prompts, and `problemform eval` / `problemform benchmark` CLI surfaces. See M3 in `docs/roadmap.md` for the full scope and success criteria.

## Planning guidance

When proposing or implementing new work in this codebase, assume:

- **M3 (Prompt Evaluation) is the active priority.** Workstreams that move the project toward measurable benchmarks (rubrics, golden sets, comparative scoring, eval CLI commands, regression-test infrastructure) come before workstreams that add orchestration, UI, or platform reach.
- **LangGraph is M4, not M3.** Do not introduce LangGraph nodes, graph state, or graph-orchestration libraries until M3 has produced a stable benchmark suite that can be used to validate the LangGraph migration preserves quality.
- **New features should be evaluable.** When proposing a change to a prompt, agent, workflow logic, or convergence behavior, also note how it will be measured under the M3 benchmark suite (or how it will be retrofitted once the suite exists). "Did this materially improve question quality, prompt quality, or answer quality?" is the question the M3 framework needs to answer for every change.
- **Evaluation infrastructure precedes orchestration infrastructure.** When trading off scope, prefer the version of a change that lands evaluable behavior over one that lands additional architectural sophistication. Architectural sophistication (LangGraph, MCP, Streamlit, observability) is downstream of being able to measure whether the system actually works.

## Environment & common commands

Conda (path-based env lives at `./.conda`, see `docs/environment.md`):

```bash
conda create -p ./.conda python=3.11
conda activate ./.conda
pip install -e .[dev]             # pydantic, typer, rich, python-dotenv + pytest + both LLM SDKs
# or
pip install -e .[all]             # runtime deps + both LLM SDKs (openai + anthropic)
pip install -e .[openai]          # runtime deps + just OpenAI
pip install -e .[anthropic]       # runtime deps + just Anthropic
```

The OpenAI and Anthropic SDKs are **optional extras** — `pyproject.toml` keeps each behind its own extra so users with only one provider configured can install just that one. The SDK imports inside `problemform/core/language_models.py` are lazy (deferred to provider `__init__`), so missing the other SDK never breaks import of the module.

API keys are loaded via `problemform/config.py` from a `.env` file (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).

Tests:

```bash
pytest -q                         # whole suite
pytest tests/path/to/test.py::test_name  # single test
```

There is no lint/format config checked in yet.

## Architecture

The system is a sequence of phases that each read and update a shared `ProblemState`, looping until a Convergence Evaluator marks the formulation `CONVERGED`. Phase order, per `docs/architecture.md`:

`Objective Analysis → Assumption Excavation → Information Gap Detection → Expert Panel → Alternative Framing → Meta Questions → Prompt/Question Synthesis → Convergence Evaluation → (loop or finish)`

Code mapping:

- `problemform/models.py` — all Pydantic data structures: `ProblemState`, per-phase artifact models (`Assumption`, `InformationGap`, `ExpertPerspective`, `AlternativeFraming`, `MetaQuestion`), per-phase result envelopes (`ObjectiveAnalysisResult`, `AssumptionExcavationResult`, `InformationGapResult`, `ExpertPanelResult`, `AlternativeFramingResult`, `MetaQuestionResult`, `PromptRefinementResult`, `ConvergenceResult` — the latter includes `prompt_delta_assessment` as a first-class field), `PromptVersion`/`Revision`, and the `Phase` / `ConvergenceStatus` literals. `ProblemState.last_convergence` carries the most recent `ConvergenceResult`. **`ProblemState` is the single piece of state passed between phases** — new phase outputs should be added as fields here.
- `problemform/core/state.py` — pure-function helpers that construct/transition `ProblemState` immutably (`initialize_state` seeds v0; `transition_to_phase` returns `state.model_copy(update={"phase": ...})`). Follow this immutable-update pattern in new phase functions.
- `problemform/core/workflow.py` — one Python function per phase plus four ordered pipeline tables (`ANALYSIS_PHASES`, `SYNTHESIS_PHASES`, `JUDGMENT_PHASES`, and `FULL_PIPELINE = ANALYSIS + SYNTHESIS + JUDGMENT`), a small `run_pipeline(state, llm, pipeline, on_phase=)` runner, and the top-level entry points `analyze` / `synthesize` / `judge` / `run`. Phase functions take `(state, llm) → ProblemState` and call `llm.generate_structured(prompt, output_model=<Envelope from models.py>)`. `PHASE_DEFAULT_TEMPERATURES` encodes design intent — divergent phases (Alternative Framing, Meta Questions) run hotter; analytic phases run at 0.
- `problemform/core/language_models.py` — `LLMProvider` `Protocol` with `generate_text` / `generate_structured`, plus concrete `OpenAIProvider` and `AnthropicProvider`, plus `make_provider(name, model)` factory (defaults from `PROBLEMFORM_PROVIDER` / `PROBLEMFORM_MODEL` env vars). OpenAI uses the structured-output `responses.parse` API; Anthropic falls back to JSON-via-text + Pydantic validation. SDK imports are lazy inside each provider's `__init__`. New phase code should depend on the `Protocol`, not the concrete classes. Structured-output failures raise `StructuredOutputError`.
- `problemform/agents/<phase>.py` — each file exports a `PROMPT` string with a single `{problem_context}` placeholder. Phase functions in `workflow.py` substitute via `PROMPT.replace("{problem_context}", _problem_context(state))` — **not** `str.format`. The replace is deliberate: every prompt body contains literal `{...}` JSON schema examples (e.g. `{"assumptions": [...]}`) that `str.format` would mis-parse as fields. `problemform/agents/__init__.py` re-exports each prompt under the uniform name `<PHASE>_PROMPT`.
- `problemform/cli.py` — Typer app with seven subcommands (`analyze`, `synthesize`, `judge`, `run`, `agent`, `explain`, `export`). `agent <name> <state-path>` dispatches through `AGENT_COMMANDS` to one phase handler. See `docs/cli_commands.md` for the authoritative semantics of each command.
- `problemform/cli_render.py` — Markdown rendering of `ProblemState`. Convergence section is delta-primary: `**Status:**` → `**Prompt delta:**` → `**Rationale:**`, with `remaining_opportunities` rendered last under an italic "informational only" label so it doesn't visually compete with the actual convergence driver.

## Conventions worth preserving

- **Immutable state updates.** `ProblemState` is never mutated in place — phase handlers return `state.model_copy(update={...})`. See `core/state.py:transition_to_phase` for the pattern.
- **Prompts live next to their agent role** (`problemform/agents/<role>.py`) and are exported as a module-level `PROMPT` constant. Don't inline prompt bodies inside workflow functions.
- **Prompt placeholder substitution uses `.replace("{problem_context}", ...)`, not `str.format`.** Prompt bodies contain literal `{...}` JSON-schema examples that `str.format` would treat as fields. Stick with `.replace` when adding new prompts or placeholders.
- **Structured LLM calls go through `generate_structured(..., output_model=<Pydantic envelope>)`** so the provider layer (not callers) owns JSON parsing and validation. Use the matching `*Result` envelope from `models.py`, not the inner item type.
- **Phase names are the `Phase` literal in `models.py`.** Keep that enum in sync with any new phase added to the workflow and with `PHASE_DEFAULT_TEMPERATURES`, the pipeline tables, and the `AGENT_COMMANDS` map in `cli.py`.
- **List-bearing artifacts are deduped and capped.** `assumption_excavation`, `information_gap_detection`, `expert_panel_generation`, `alternative_framing`, and `meta_question_generation` merge new items via `_merge_unique(existing, new, key=lambda x: _norm(...), cap=<CAP>)`. `_norm` lowercases, strips `string.punctuation`, collapses whitespace, and strips a single leading templating phrase from `_LEADING_TEMPLATES` (e.g. `"reframe the issue as"`, `"treat the problem as"`, `"ask whether"`, `"determine whether"`). Caps are per-phase constants (`ASSUMPTIONS_CAP`, `INFORMATION_GAPS_CAP`, `EXPERT_PANEL_CAP`, `ALTERNATIVE_FRAMINGS_CAP`, `META_QUESTIONS_CAP`, all 8). Caps stop accepting new items at the cap but never trim existing entries. `prompt_versions` is intentionally **uncapped** — it's a history, not an artifact list.
- **`prompt_refinement` sets `final_prompt` in the same `model_copy` that appends to `prompt_versions`.** Any code path that runs the synthesizer (`run`, `synthesize`, CLI `agent prompt-synthesis`) leaves `state.final_prompt` pointing at the latest synthesized prompt. `run` no longer re-asserts this at the end — set it in one place (`prompt_refinement`) and leave it there.
- **Synthesis uses a compact context, not the full state.** `prompt_refinement` substitutes `_synthesis_context(state)` rather than `_problem_context(state)`. The compact projection drops verbose per-artifact `rationale`/`impact_*` fields, the judge's output, prior `prompt_versions`, and bookkeeping, keeping only the text-bearing signal plus the latest prompt. This is the only phase that uses `_synthesis_context`; all other phases keep using `_problem_context` (full state dump).
- **Convergence is delta-primary.** `convergence_evaluation` passes `prompt_versions[-2]` and `prompt_versions[-1]` to the judge explicitly via `{previous_prompt}` / `{current_prompt}` / `{prev_version}` / `{current_version}` placeholders, then persists the full `ConvergenceResult` to `state.last_convergence` and the status to `state.convergence_status`. The judge's verdict is driven by whether a competent answerer would respond meaningfully differently to the two prompts; `remaining_opportunities` is rendered but informational only. **Cold start** (only `v0` in `prompt_versions`) short-circuits to `NOT_CONVERGED` without an LLM call.

## Docs

When extending the system, read the relevant doc first — they encode design intent that isn't in the code:

- `docs/problemform_constitution.md` — phase-by-phase behavioral spec (authoritative)
- `docs/architecture.md` — workflow + agent-role overview
- `docs/implementation.md` — how Constitution maps to code
- `docs/roadmap.md` — milestone scope. **M3 = Prompt Evaluation (immediate next), M4 = LangGraph, M5 = Streamlit, M6 = MCP, M7 = Polish, M8 = LangSmith.** Do not pull in LangGraph, Streamlit, MCP, or LangSmith until their milestones; specifically, LangGraph is M4 and is gated on M3 producing a working evaluation framework.
- `docs/cli_commands.md` — authoritative shape and semantics for every `problemform` subcommand (`analyze`, `synthesize`, `judge`, `run`, `agent`, `explain`, `export`).
- `docs/glossary.md` — definitions of Information Gap, Expert Panel, Convergence, etc.
- `docs/DOCUMENTS_METADATA.md` — **document-metadata convention.** All new durable Markdown documents under `docs/` (designs, audits, reports, plans, decisions, guides) must follow the YAML front-matter schema defined there. Front matter goes at the **top** of the document. Required fields: `title`, `document_type`, `status`, `created`, `updated`, `author`. Optional: `authoritative_reference`, `related` (with `documents` and `issues` sub-keys), `scope` (with `inspected`). **Do not use the deprecated fields** `active_document`, `shelved`, `files_created`, `implementation_changes` (they duplicate `status` or git history). Update `updated` on material edits; leave it for typo fixes. Existing documents that pre-date the convention may keep their original metadata until their next material edit.
