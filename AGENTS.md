# AGENTS.md

**Shared, tool-neutral contract for every coding agent working in this repository**
(Claude Code, Codex, ChatGPT, and any future agent). Read this first. When this file conflicts with a task-specific prompt, the explicit user task takes precedence.

Tool-specific overlays extend — never duplicate — this file:
[`CLAUDE.md`](CLAUDE.md) for Claude Code. Keep *this* file tool-neutral and
**status-free**: current milestone and progress live in
[`docs/roadmap.md`](docs/roadmap.md), not here.

Changes to AGENTS.md should be rare. Prefer updating the authoritative document it references, or a tool-specific overlay, rather than expanding this shared contract.

Everything below either states a durable rule/convention or points to the
authoritative source. When something already lives authoritatively elsewhere, this
file links rather than restates — so there is one source of truth per fact.

---

## Project purpose

ProblemForm is a human–AI collaborative **problem-formulation** system: its goal is
not to answer the user's question but to iteratively refine the question / prompt /
problem statement *itself* until it converges. The deliverable is the **formulation**,
not the answer.

Authoritative sources — defer to these when anything here is ambiguous:

- **What the system should do:** [`docs/problemform_constitution.md`](docs/problemform_constitution.md) (the authoritative behavioral spec).
- **How it is built:** [`docs/architecture.md`](docs/architecture.md) and [`docs/implementation.md`](docs/implementation.md).
- **User-facing overview:** [`README.md`](README.md).

## Documentation map

One source of truth per topic. Consult the right doc before working in that area.

| Topic | Authoritative doc |
|---|---|
| Behavioral spec (what/why) | [`docs/problemform_constitution.md`](docs/problemform_constitution.md) |
| Architecture / workflow | [`docs/architecture.md`](docs/architecture.md) |
| Constitution → code mapping | [`docs/implementation.md`](docs/implementation.md) |
| **Current milestone & status** | [`docs/roadmap.md`](docs/roadmap.md) |
| CLI command semantics | [`docs/cli_commands.md`](docs/cli_commands.md) |
| Terminology | [`docs/glossary.md`](docs/glossary.md) |
| Environment / setup | [`docs/environment.md`](docs/environment.md) |
| Dependencies | [`docs/dependencies.md`](docs/dependencies.md) |
| Ideas / not-yet-active work | [`docs/backlog.md`](docs/backlog.md) |
| Doc metadata convention | [`docs/DOCUMENTS_METADATA.md`](docs/DOCUMENTS_METADATA.md) |
| Design references (durable) | [`docs/designs/`](docs/designs/README.md) |
| Implementation plans (time-bound) | [`docs/plans/`](docs/plans/README.md) |
| Findings / audits / validation runs | `docs/reports/` (dated records) |

## Environment & commands

Path-based conda env at `./.conda` (details in [`docs/environment.md`](docs/environment.md)):

```bash
conda create -p ./.conda python=3.11 && conda activate ./.conda
pip install -e .[dev]        # runtime deps + both LLM SDKs + pytest
```

The OpenAI and Anthropic SDKs are **optional extras** (`.[openai]`, `.[anthropic]`,
`.[all]`); their imports are lazy so a missing provider SDK never breaks import. API
keys load from a root `.env` (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).

**Tests:**
```bash
pytest -q                                   # whole suite
pytest tests/path::test_name                # single test
```
There is no checked-in lint/format config. **Any behavior change ships with tests.**

## Repository orientation

Package-level map (see [`docs/architecture.md`](docs/architecture.md) /
[`docs/implementation.md`](docs/implementation.md) for file-level detail):

- `problemform/core/` — the refinement pipeline: one function per phase, the pipeline
  tables, the run loop, and the `LLMProvider` protocol + providers.
- `problemform/eval/` — the evaluation framework (benchmark engine, rubric/property
  runners, the formulation-type policy registry, report rendering).
- `problemform/agents/` — one `PROMPT` constant per phase role.
- `problemform/cli.py` — the Typer CLI.
- `benchmarks/cases/` — the canonical benchmark corpus (one suite dir per formulation
  type); `benchmarks/rubrics/` and `benchmarks/properties/` are sibling resources.
- `docs/`, `tests/` — as mapped above.

Pipeline: `Objective Analysis → Assumption Excavation → Information-Gap Detection →
Expert Panel → Alternative Framing → Meta Questions → Prompt Synthesis → Convergence`,
looping until converged.

## Architectural invariants

Durable rules that encode design intent not obvious from reading code. Do not break
them without an explicit design decision.

- **`ProblemState` is immutable.** Phases return `state.model_copy(update={...})`;
  never mutate in place. It is the single state object passed between phases — new
  phase outputs are added as fields on it.
- **Prompts live beside their agent role** as a module-level `PROMPT` constant in
  `problemform/agents/<role>.py`, never inlined in workflow code.
- **Substitute prompt placeholders with `.replace("{...}", value)`, not `str.format`.**
  Prompt bodies contain literal `{...}` JSON-schema examples that `str.format` would
  mis-parse.
- **Structured LLM output goes through `generate_structured(..., output_model=<Pydantic>)`**
  so the provider layer owns JSON parsing/validation — callers never parse.
- **Keep the phase set consistent.** The `Phase` literal, the phase-temperature table,
  the pipeline tables, and the CLI agent-command map must stay in sync when a phase is
  added or renamed.
- **List-valued artifacts are deduplicated and capped** on merge; prompt-version
  history is intentionally uncapped.
- **The three evaluation lenses stay parallel and are never collapsed into one score**
  (comparative answer judgment, absolute rubrics, property checks). A type/case may
  have fewer applicable lenses; aggregates remain separate.
- **Convergence is prompt-delta-primary:** the judge decides whether a competent
  answerer would respond meaningfully differently to the two prompt versions.
- **Provider SDKs are optional and lazy-imported** behind extras.
- **Benchmark cases are treated as versioned scientific assets.** Changes to
  benchmark cases, rubrics, or properties should preserve their evaluability and
  historical interpretability. Validation reports should remain reproducible
  against the benchmark version they describe.


## Change & review workflow

- **Small, reviewable commits.** Prefer the smallest coherent change that follows an
  existing pattern in the repo; defer the rest explicitly rather than bundling it in.
- **Behavior-changing milestone work should be planned before implementation.** For new architecture, public contract changes, evaluation semantics, or the first behavior-changing step of a milestone, write an implementation plan under docs/plans/ and expect review before implementation.
- **Preserve established contracts.** Do not redefine existing semantics as a side
  effect (e.g. aggregate buckets, error accounting). New fields should be additive and
  default-compatible so older serialized data still parses.
- **Verify at the right level.** When a change legitimately adds fields to serialized
  output, verify *semantic* invariance (metrics, counts, artifacts unchanged; only the
  additive field differs) rather than byte-identity.
- **Commit and push only when asked.** End work in a clean, tested state.

Never overwrite, revert, or commit changes you did not make unless explicitly instructed. Scope commits to the work you performed.

## Documentation lifecycle

- **Durable Markdown under `docs/` uses the front-matter schema** in
  [`docs/DOCUMENTS_METADATA.md`](docs/DOCUMENTS_METADATA.md) (`title`, `document_type`,
  `status`, `created`, `updated`, `author`, …). Update `updated` on material edits.
- **Three doc lifecycles** — see the folder READMEs:
  [`designs/`](docs/designs/README.md) are durable, authoritative "how it should work"
  references (amended in place); [`plans/`](docs/plans/README.md) are time-bound
  decision trails (usually end `superseded`); `reports/` are dated findings / audits /
  validation records.
- **Amend authoritative docs in place** with a dated note when a decision changes;
  **do not rewrite dated reports or superseded plans** as history. If a moved/renamed
  file breaks a *live link* in a historical doc, fix the link target (or add a
  relocation note) without rewriting the surrounding substance.
- **Keep status out of durable guidance.** This file and the design docs stay free of ongoing progress tracking.

## Implementation principles

- **Every behavior change should be evaluable.** For a change to a prompt, agent, workflow, or
  convergence behavior, be able to say how it will be measured under the benchmark
  suite ("did this materially improve formulation / answer quality?").
- **Do not introduce architectural sophistication ahead of need** (orchestration,
  services, UI, observability). Land evaluable behavior first; sequencing lives in
  [`docs/roadmap.md`](docs/roadmap.md).
- **Validation is outcome-neutral.** Report what the evidence shows — any direction is
  a legitimate finding; don't bake the hypothesis into the verification.

## When in doubt

Prefer:
- preserving behavior and contracts over broad refactors or clever redesigns,
- authoritative documents over duplicated explanations,
- additive changes over semantic redefinitions,
- evidence over intuition,
- small reviewable commits over large rewrites.

---

This document is intentionally small. If you find yourself wanting to expand it,
the information probably belongs in one of the authoritative documents above.