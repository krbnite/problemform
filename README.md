# ProblemForm

**ProblemForm is a human–AI collaborative system for refining questions, prompts, and problem statements. Its goal is not to answer the user's question — it is to produce the highest-quality formulation of the question itself.**

A well-formed question is often more valuable than a confident answer to the wrong one. ProblemForm makes the act of formulation explicit and inspectable: a structured pipeline drives an LLM through objective analysis, assumption excavation, gap detection, expert perspectives, alternative framings, and meta-questions, then synthesizes a refined prompt and judges whether further refinement would change anything material.

The authoritative description of the methodology lives in [`docs/problemform_constitution.md`](docs/problemform_constitution.md). The architectural overview is in [`docs/architecture.md`](docs/architecture.md).

---

## Why this exists

LLM output quality is bounded by prompt quality. Most prompts are written once, off the cuff, and never inspected. ProblemForm treats prompt formulation as a workflow with phases, artifacts, and a convergence criterion — so the formulation itself becomes something you can read, version, evaluate, and improve.

---

## What kinds of things can ProblemForm refine?

| Formulation Type | What the user is trying to do | What should refinement look like? | Why test it? | Example |
|---|---|---|---|---|
| **Questions** | Ask for information or understanding. | Clarify what is being asked, surface hidden assumptions and constraints, reduce ambiguity, and identify missing context. | Questions are the traditional benchmark for ProblemForm and remain the primary comparison point. | *"Why do eclipses happen?"* |
| **Decisions** | Choose between one or more possible courses of action. | Expose hidden tradeoffs, identify missing constraints or objectives, clarify decision criteria, and recognize when the user has already done so. | Tests whether ProblemForm improves decision quality rather than merely generating recommendations. | *"Should I leave my stable software job to join a startup?"* |
| **Dilemmas** | Resolve a conflict where competing values or obligations make there unlikely to be a single objectively correct answer. | Surface the competing values, stakeholders, and tradeoffs without prematurely assuming one should dominate. | Tests whether ProblemForm recognizes value conflicts instead of treating every problem as an optimization task. | *"Should a company delay launching a biased AI model or release it and patch later?"* |
| **Beliefs** | Express something believed to be true. | Distinguish claims from evidence, identify assumptions, clarify ambiguous terms, and reformulate the belief into something that can be investigated or challenged. | Tests whether ProblemForm can transform beliefs into better objects of inquiry. | *"AI will replace software engineers within ten years."* |
| **Arguments** | Justify a conclusion through reasoning. | Make premises, conclusions, assumptions, and inferential structure explicit while preserving the author's position. | Tests whether ProblemForm improves the representation of reasoning itself, independent of whether the conclusion is true. | *Aquinas' First Way.* |
| **Goals** | Describe a desired future state or objective. | Clarify success criteria, motivations, constraints, priorities, dependencies, and timelines. | Tests whether ProblemForm can make vague aspirations more actionable without prescribing solutions. | *"I want to become a better engineering manager."* |
| **Plans** | Describe a proposed course of action for achieving a goal. | Surface assumptions, risks, missing steps, dependencies, resource constraints, and alternative strategies while preserving the author's overall intent. | Tests whether ProblemForm improves execution readiness rather than judging whether a plan is good. | *"We should migrate our backend to Kubernetes next quarter."* |
| **Explanations** | Help someone understand a concept or phenomenon. | Clarify the explanatory goal, audience, scope, assumptions, and potential misconceptions. | Tests whether ProblemForm can improve explanatory requests beyond simple question answering. | *"Explain quantum tunneling to a high school student."* |
| **Instructions** | Tell a person or agent to perform a task. | Clarify objectives, constraints, ordering, success criteria, and edge cases while reducing ambiguity. | Tests whether ProblemForm improves task execution by making instructions more precise and complete. | *"Summarize this paper in five bullet points."* |
| **Prompts** | Guide an AI system toward producing a desired output. | Clarify objectives, audience, constraints, evaluation criteria, and missing context while preserving the user's intent. | Tests whether ProblemForm can recursively improve AI interactions by producing better prompts. | *"Write a children's story about dragons."* |
| **Specifications** | Define the desired behavior, requirements, or constraints of a system or product. | Surface ambiguities, distinguish requirements from implementation decisions, clarify edge cases, and identify missing requirements. | Tests whether ProblemForm improves engineering requirements before implementation begins. | *"Design an API that processes online payments."* |

---

## Key concepts

- **`ProblemState`** — a single immutable Pydantic record that flows through the pipeline. Each phase returns a new `ProblemState` via `model_copy(update=…)`; nothing is mutated in place.
- **Eight phases** form the pipeline:
  1. **Objective Analysis** — separates the user's stated objective from the inferred one.
  2. **Assumption Excavation** — surfaces explicit, implicit, and questionable assumptions.
  3. **Information-Gap Detection** — names what's missing and how it should be acquired.
  4. **Expert Panel Generation** — drafts follow-up questions from the perspectives most likely to matter.
  5. **Alternative Framing** — reframes the problem to expose blind spots in the original framing.
  6. **Meta-Question Generation** — asks questions about the question itself.
  7. **Prompt Refinement** — synthesizes a new prompt from a compact projection of the state.
  8. **Convergence Evaluation** — compares the latest prompt against the previous one and decides whether further refinement would change the answer.
- **Prompt-delta-primary convergence.** The judge's verdict is driven by whether a competent answerer would respond meaningfully differently to the two prompt versions. Remaining "things we could still explore" are tracked but informational only.
- **`LLMProvider` protocol.** OpenAI and Anthropic are both supported through a single `generate_text` / `generate_structured` interface. SDKs are imported lazily, so it is not required to install models from each and every provider.

---

## Current capabilities

- End-to-end Python pipeline runnable from a single function (`problemform.core.workflow.run`) or from the CLI.
- Both OpenAI (via `responses.parse` structured output) and Anthropic (via JSON-with-Pydantic-validation) providers.
- Eight CLI subcommands (`analyze`, `synthesize`, `judge`, `run`, `agent`, `explain`, `export`, `benchmark`).
- Per-phase de-duplication and caps on accumulated artifacts; a compact synthesis context that keeps prompt-refinement input small.
- Friendly CLI errors for provider misconfiguration, structured-output failures, and file I/O.
- A built-in **evaluation framework** with three parallel, independently-reported lenses — comparative answer judging, absolute rubric scoring (of formulations and of answers), and behavioral property checks (see below).

---

## Evaluation framework

ProblemForm includes a benchmark harness that measures its own effect. This is deliberate: The value of a problem-formulation system can't be assumed--it has to be measured. The framework applies **three parallel lenses** to each case and reports them separately — never collapsed into a single score:

1. **Comparative answer judging** (the original lens) — compare the answer produced from the raw prompt against the answer from the refined prompt.
2. **Absolute rubric scoring** — score the *formulation* itself (and, optionally, the answer) against weighted criteria.
3. **Behavioral property checks** — binary "should always hold" assertions about the formulation or the answer.

The evaluation framework is intentionally lightweight and should be viewed as an early measurement system rather than a definitive assessment of quality.

The comparative lens works by comparing the answer an LLM produces when given the **raw question** against the answer it produces when given the **refined prompt**, and asking a third LLM which is better.

**Three provider roles**, configurable independently:

- **ProblemForm provider** — runs the refinement pipeline.
- **Answer provider** — generates the two answers (raw and refined).
- **Judge provider** — performs the comparative judgment. Using a different provider family for the judge is recommended; using the same family triggers a self-preference warning but is not blocked.

Each role accepts its own `--*-provider` / `--*-model` flags on the `benchmark` command and has dedicated environment-variable defaults (`PROBLEMFORM_EVAL_ANSWER_PROVIDER` / `PROBLEMFORM_EVAL_ANSWER_MODEL`, `PROBLEMFORM_EVAL_JUDGE_PROVIDER` / `PROBLEMFORM_EVAL_JUDGE_MODEL`) so that a cross-family evaluation setup can be configured once in `.env` rather than passed on every invocation. The ProblemForm role uses the generic `PROBLEMFORM_PROVIDER` / `PROBLEMFORM_MODEL`. See the Configuration section for the full precedence rules.

**Bias mitigation built in.** Comparative judgments are position-randomized — the judge sees opaque "A/B" labels, and the engine de-anonymizes which side was actually the refined one. The judge prompt does not contain the labels "raw" or "refined."

**Three-way reporting.** Headlines show the *refined-win rate*, the *raw-win rate*, and the *tie rate* side by side, plus a *material-improvement rate* and an explicit *degradation rate*. A high refined-win rate cannot be celebrated without also acknowledging the corresponding regressions.

**What the rates mean.** The judge attaches a four-level *materiality* to each verdict: `material` (meaningfully better in substance), `minor` (small but real improvement), `stylistic_only` (same substance, different presentation — used for ties), and `degradation` (the losing answer is substantively worse, not merely less polished — "would actively mislead or harm relative to the other," per the judge prompt). Two derived rates appear in the headline:

- **Material-improvement rate** — fraction of completed cases where the refined-prompt answer won *and* the win was rated `material`. This is the clean "ProblemForm helped" signal.
- **Degradation rate** — fraction of completed cases where the judge marked the verdict `degradation`. In practice this pairs with `winner_actual == "raw"`, i.e. the refined prompt produced an answer that is actively worse than the answer to the raw question. This is the regression signal.

Both rates use `n_completed` (errored cases excluded) as the denominator.

**Failure containment.** A single failed case (judge error, refusal, network blip) is captured into that case's `errors[]` and the run continues. Aggregate rates are computed over completed cases, not attempted ones.

**Control cases.** The shipped corpus includes a well-formed factual question (`what_causes_eclipses`) where ProblemForm may not help — or may hurt. This is a structural guard against the benchmark drifting into an advocacy artifact.

**Rubric & property lenses.** Alongside the answer comparison, each run also applies:

- **Absolute rubrics** — weighted criteria scored 0–1 and aggregated per rubric (raw vs refined mean, plus the refined−raw delta). Two ship by default: `formulation_quality_v1` (`target: formulation` — scores the raw vs refined *prompt* on central-claim clarity, assumption surfacing, constraint articulation, alternative-framing coverage, and meta-question presence) and `answer_quality_v1` (`target: artifact` — scores the answers). Because the formulation rubric evaluates the prompt directly, the harness measures inputs that have no natural downstream answer (e.g. arguments), not just questions.
- **Property checks** — binary assertions reported as raw/refined pass rates (e.g. `addresses_stated_request`). Each corpus case's `expected_properties` also activate as `target: formulation` checks.
- **Disagreement diagnostic** — cases where the comparative-answer verdict and the formulation-rubric delta point in different directions are surfaced as the high-value cases for human review: the two lenses side by side, never merged.

Select lenses with the repeatable `--rubric <path>` and `--property-suite <path>` flags. **With no flags, the shipped defaults load** (from `benchmarks/rubrics/` and `benchmarks/properties/`); **an explicit flag overrides** the corresponding default set. See [`docs/cli_commands.md`](docs/cli_commands.md) for the full semantics.

Run the default suite (all three lenses) against an OpenAI ProblemForm + Answer model and an Anthropic judge:

```bash
problemform benchmark benchmarks/default \
    --pf-provider openai \
    --answer-provider openai \
    --judge-provider anthropic
```

Outputs land under `.problemform/eval_runs/<run-id>/`:

```
report.json
report.md
cases/<case-name>/problem_state.json
cases/<case-name>/raw_answer.txt
cases/<case-name>/refined_answer.txt
```

Full design rationale: [`docs/designs/milestone_03_evaluation_framework.md`](docs/designs/milestone_03_evaluation_framework.md). Corpus layout: [`benchmarks/README.md`](benchmarks/README.md).

---

## Installation

Requires Python ≥ 3.11. A conda environment is recommended; see [`docs/environment.md`](docs/environment.md).

ProblemForm uses optional extras so you install only the LLM SDKs you actually need:

```bash
pip install -e .[dev]         # runtime deps + both SDKs + pytest
pip install -e .[all]         # runtime deps + both SDKs
pip install -e .[openai]      # runtime deps + just OpenAI
pip install -e .[anthropic]   # runtime deps + just Anthropic
```

The runtime dependencies (`pydantic`, `typer`, `rich`, `python-dotenv`, `PyYAML`) are always installed. The OpenAI and Anthropic SDKs are imported lazily inside their providers, so installing only one provider's SDK does not break import of the other.

---

## Configuration

API keys are loaded from a `.env` file at the repo root:

```
OPENAI_API_KEY=sk-…
ANTHROPIC_API_KEY=sk-ant-…
```

Defaults can be set via environment variables:

| Variable | Effect |
|---|---|
| `PROBLEMFORM_PROVIDER` | Default provider name (`openai` or `anthropic`). Used by all commands and as the fallback for every role in `benchmark`. |
| `PROBLEMFORM_MODEL` | Default model ID. Used by all commands and as the fallback for every role in `benchmark`. |
| `PROBLEMFORM_EVAL_ANSWER_PROVIDER` | Default provider name for the **Answer** role in `benchmark`. Overrides `PROBLEMFORM_PROVIDER` for this role only. |
| `PROBLEMFORM_EVAL_ANSWER_MODEL` | Default model ID for the **Answer** role in `benchmark`. Overrides `PROBLEMFORM_MODEL` for this role only. |
| `PROBLEMFORM_EVAL_JUDGE_PROVIDER` | Default provider name for the **Comparative Answer Judge** role in `benchmark`. Overrides `PROBLEMFORM_PROVIDER` for this role only. |
| `PROBLEMFORM_EVAL_JUDGE_MODEL` | Default model ID for the **Comparative Answer Judge** role in `benchmark`. Overrides `PROBLEMFORM_MODEL` for this role only. |

The `PROBLEMFORM_EVAL_*` variables are **scoped to the evaluation framework**. They do not affect the workflow's Convergence Judge (the `convergence_evaluation` phase in `run` and the standalone `problemform judge` command). The workflow uses one provider end-to-end via `PROBLEMFORM_PROVIDER` / `PROBLEMFORM_MODEL`.

Resolution precedence for each role is: **CLI flag → role-specific env var → generic env var → built-in default.** The ProblemForm role in `benchmark` uses `PROBLEMFORM_PROVIDER` / `PROBLEMFORM_MODEL` directly (no separate `PROBLEMFORM_PF_*` variables); the role-specific variables exist for the Answer and Comparative Answer Judge roles, where cross-family configuration is the recommended setup.

The provider name and model can always be overridden per command with `--provider` / `--model` (or the role-specific flags on `benchmark`).

> **Note on default model IDs.** The provider defaults in source (`gpt-5.4`, `claude-sonnet-4-6`) are forward-looking. If your installed SDK doesn't recognize them, pass `--model` explicitly or set `PROBLEMFORM_MODEL`.

---

## CLI usage

| Command | Purpose |
|---|---|
| `analyze` | Run the six analytical phases only; no synthesis, no convergence judgment. |
| `synthesize` | Generate a refined prompt from an existing `ProblemState`. |
| `judge` | Run convergence evaluation against an existing `ProblemState`. |
| `run` | Loop the full pipeline (analysis → synthesis → judgment) until `CONVERGED` or `--max-iterations`. |
| `agent` | Run a single named phase against an existing `ProblemState`. Useful for debugging individual steps. |
| `explain` | Pretty-print a `ProblemState` as Markdown. |
| `export` | Persist a `ProblemState` as JSON or Markdown. |
| `benchmark` | Run a YAML test-case suite end-to-end and write JSON + Markdown reports. |

Authoritative semantics for every command: [`docs/cli_commands.md`](docs/cli_commands.md).

---

## Example workflows

**Full refinement loop, one iteration (the default):**

```bash
problemform run "How should I prepare for my upcoming code review?"
```

**Inspect the analytical phases first, then synthesize separately:**

```bash
problemform analyze "Should I use REST or GraphQL for my new API?" \
    --save state.json
problemform synthesize --state state.json --save state.json
problemform judge --state state.json --format md
```

**Re-run only one phase against a saved state:**

```bash
problemform agent meta-questions state.json --output state.json
```

**Benchmark the refinement on the shipped corpus, with a cross-family judge:**

```bash
problemform benchmark benchmarks/default \
    --pf-provider openai \
    --answer-provider openai \
    --judge-provider anthropic
```

---

## Repository structure

```
problemform/
  models.py                  # Pydantic types: ProblemState, per-phase artifacts, result envelopes
  config.py                  # .env loader
  cli.py                     # Typer app (8 subcommands)
  cli_render.py              # Markdown rendering of ProblemState
  core/
    state.py                 # initialize_state, transition_to_phase
    workflow.py              # phase functions, pipeline tables, run_pipeline
    language_models.py       # LLMProvider Protocol, OpenAI + Anthropic providers, error types
  agents/                    # one PROMPT constant per phase
  eval/
    models.py                # TestCase, ComparativeJudgment, TestCaseResult, AggregateMetrics, BenchmarkReport, Rubric, PropertyCheck + aggregate types
    corpus.py                # YAML loaders (corpus, rubrics, property suites)
    judges.py                # position-randomized comparative answer judging
    engine.py                # per-case pipeline (M3A judgment + rubric/property lenses), failure containment, aggregation
    report.py                # JSON + Markdown reporting
    scoring.py               # shared rubric/property scoring utilities
    rubric_runner.py         # absolute rubric scoring, run in the benchmark pipeline
    property_runner.py       # behavioral property checks, run in the benchmark pipeline
    defaults.py              # default rubric/property-suite resolution for benchmark
    prompts/                 # eval-only prompt constants (comparative, rubric, property judges)
benchmarks/
  default/                   # shipped test suite (5 cases incl. control)
  rubrics/                   # shipped absolute rubrics (formulation_quality_v1, answer_quality_v1)
  properties/                # shipped property suites (artifact_baseline_v1)
docs/                        # constitution, architecture, CLI spec, design references
tests/                       # pytest suite
```

---

## Development & testing

```bash
pip install -e .[dev]
pytest -q
```

The test suite covers the workflow (immutability, de-duplication, convergence cold-start, compact synthesis context), both LLM providers (success and failure modes including truncation, refusal, content-filter, empty response), the CLI surface (including friendly error handling), and the full evaluation framework (corpus loading, position randomization, per-case pipeline, failure containment, aggregation, and report rendering).

Design references for non-obvious decisions live under [`docs/designs/`](docs/designs/).

---

## FAQ / design notes

### Why does `max_iterations` default to 1?

**TL;DR: Prompt quality ≠ refinement depth.**

In testing, most of the improvement in prompt quality occurs during the first refinement pass. Additional iterations often continue generating valid assumptions, perspectives, framings, and meta-questions, but the marginal gains diminish rapidly — and sometimes go negative.

Refinement quality often follows a curve like:

```
Quality
  ^
  |
10|           _____
  |         /
  |       /
  |     /
  |   /
  | /
  +-------------------->
      Iterations
```

…or worse — a peak followed by a decline:

```
Quality
  ^
10|        /\__
  |      /     \__
  |    /
  |  /
  |/
  +-------------------->
      Iterations
```

In practice we see something like:

```
Iteration 1 = transformation
Iteration 2 = optimization
Iteration 3+ = editorializing
```

Because problem formulation is inherently open-ended, the analytical phases can keep producing new artifacts indefinitely. More iterations therefore increase cost and latency while not necessarily producing proportionally better prompts. Excessive refinement can also push prompts toward being overly elaborate, academic, or procedural relative to the user's original objective.

For this reason, ProblemForm defaults to `max_iterations=1`. Additional iterations are available when deeper exploration is desired, but should be treated as an advanced option, not the default workflow.

---

## Roadmap

**Implemented:**

- Pure-Python core: `ProblemState`, all eight phase handlers, both LLM providers, end-to-end pipeline.
- CLI: eight subcommands covering the analytical phases, synthesis, judgment, full-loop execution, single-phase dispatch, inspection, and export.
- Evaluation framework (M3A): comparative answer judging, three-way reporting, position randomization, failure containment, YAML corpus loader, shipped starter suite with a control case.
- Formulation & answer rubrics + property checks (M3B-α): absolute rubric scoring with per-rubric raw/refined deltas, behavioral property checks with pass rates, the M3A-vs-formulation disagreement diagnostic, repeatable `--rubric` / `--property-suite` flags with default-loading, and a first-class non-question benchmark case (`benchmarks/arguments/`). Three lenses reported in parallel, never merged into one score.

**Planned (capability-focused; specific technologies are tracked in [`docs/roadmap.md`](docs/roadmap.md)):**

- Broader evaluation (M3B-β and later): comparative-mode rubrics, corpus diversification across non-question input types, multi-judgment aggregation (K>1), dev/held-out splits, and rubric calibration.
- Graph-based orchestration of the pipeline.
- Interactive UI for non-CLI users.
- Integration-protocol exposure for use inside other agent systems.
- Reliability, security, and observability polish.

---

## Documentation

- [`docs/problemform_constitution.md`](docs/problemform_constitution.md) — authoritative methodology spec.
- [`docs/architecture.md`](docs/architecture.md) — workflow and agent-role overview.
- [`docs/cli_commands.md`](docs/cli_commands.md) — per-command semantics.
- [`docs/environment.md`](docs/environment.md) — installation and environment setup.
- [`docs/glossary.md`](docs/glossary.md) — definitions of Information Gap, Expert Panel, Convergence, etc.
- [`docs/designs/milestone_03_evaluation_framework.md`](docs/designs/milestone_03_evaluation_framework.md) — design reference for the evaluation framework.
- [`docs/designs/problemform_scope.md`](docs/designs/problemform_scope.md) — working hypothesis on validated subset vs intended scope, the `ProblemForm × Answer Model` measurement confound, and M3B's potential role as the bridge to non-question inputs.
- [`docs/backlog.md`](docs/backlog.md) — tracked ideas, design speculation, and not-yet-active work.
- [`benchmarks/README.md`](benchmarks/README.md) — benchmark corpus layout and conventions.

---

## License

MIT. See [`LICENSE`](LICENSE).
