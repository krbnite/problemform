# Milestone 3: Evaluation & Benchmarking Framework — Design Reference

## Preamble

This is the **design reference** for ProblemForm's Milestone 3 (Prompt Evaluation). It captures the full architectural thinking — including elements that are not yet implemented and elements that have been explicitly rejected — so future maintainers can trace decisions back to their reasoning instead of re-litigating settled questions.

This document is **not the active implementation plan**. The active plan is whatever Phase is currently being executed; the implementation order section at the end gives the long-term sequence.

### Status as of 2026-06

- **Phase A**: in design; implementation begins after this document is committed.
- **Phases B / C / D**: deferred, designed in this document, no code yet.

### Labeling convention

Every meaningful architectural element below is tagged with one of:

- **[APPROVED — Phase A]**: in the current implementation scope. Build it now.
- **[DEFERRED — Phase B/C/D]**: in the long-term architecture but not the current scope. Don't build yet.
- **[REJECTED]**: considered and explicitly not planned. Don't re-propose without reopening the discussion.

If a section has no tag, it's pure context (philosophy, rationale, tradeoffs) that applies across all phases.

---

## 1. Context & philosophy

ProblemForm's value proposition is unfalsifiable today: the system produces longer, more detailed prompts, but we have no instrument to measure whether the prompts are actually *better*. Without one, the project is steering by vibes — and the natural failure mode of a problem-formulation system is to produce elaborate prompts that are no more useful than the originals.

The framework's job is **measurement, not advocacy.** It should be capable of saying "no, ProblemForm did not help on this question," and the reporting should make that easy to see.

Three principles follow:

1. **Comparative > absolute, where possible.** "Which is better?" with a held-out judge is more robust than "rate from 1–5"; absolute scores drift over time as judge models change, while pairwise win rates are at least internally consistent within a run.
2. **Answer quality is the headline.** Refined prompts are an intermediate artifact; the user receives an answer. The framework prioritizes `raw_answer vs refined_answer` over `raw_prompt vs refined_prompt`.
3. **Bias and noise are first-class.** LLM-as-judge has well-known position, verbosity, and self-preference biases; ignoring them means publishing improvements that don't exist. The architecture builds in mitigations from day one.

---

## 2. Recommended architecture

Three layers that mirror the existing `state / workflow / render` separation in the rest of the project:

```
+--------------------------------------------------------------+
|  Corpus  (user-owned, version-controlled YAML)               |
|    - TestCase definitions                                    |
|    - Rubric definitions                  [DEFERRED]          |
+----------------------+---------------------------------------+
                       |  loaded by
                       v
+--------------------------------------------------------------+
|  Engine  (Python, pure functions over Pydantic models)       |
|  +--------------------------------------------------------+  |
|  |  Pipeline per test case:                               |  |
|  |   1. ProblemForm run        (PF provider)              |  |
|  |   2. Answer generation x2   (Answer provider)          |  |
|  |   3. Comparative judgment   (Judge provider)           |  |
|  |   4. Rubric evaluations     (Judge provider) [DEFER]   |  |
|  |   5. Property checks        (Judge provider) [DEFER]   |  |
|  +--------------------------------------------------------+  |
|  Three independent provider roles, all using existing        |
|  LLMProvider Protocol and make_provider() factory.           |
+----------------------+---------------------------------------+
                       |  emits
                       v
+--------------------------------------------------------------+
|  Reporter                                                    |
|    - BenchmarkReport JSON (machine-readable, full provenance)|
|    - Markdown summary (headline metric, breakdowns, samples) |
+--------------------------------------------------------------+
```

### Three distinct LLM provider roles  **[APPROVED — Phase A]**

The most important structural decision.

| Role | Job | Default |
|---|---|---|
| **PF provider** | Drives the ProblemForm pipeline (analysis to synthesis to judgment). | Whatever the user already uses for `problemform run`. |
| **Answer provider** | Produces an answer to `raw_question` and to `refined_prompt`. | Same family as PF provider by default. The thing being tested is the *prompt's effect on this model's answer*. |
| **Judge provider** | Renders the pairwise verdict (and rubric scores when those land). | Strongly recommend a *different model family* from the Answer provider (to mitigate self-preference). The framework will **warn** when this is not the case but will not block. |

These roles each get their own `--*-provider` / `--*-model` flag and reuse `problemform.core.language_models.make_provider`.

**Why three roles and not one?** The value proposition has the structure "does refining a prompt to model X cause model X to give a better answer, as judged by model Y?" Conflating any pair of these undermines the measurement.

### Alternatives considered (rejected)  **[REJECTED]**

- **Single absolute-score-only system**: simpler, but absolute LLM scores are notoriously unreliable across runs and unstable as judge models update. Comparative judgments are the load-bearing primitive; absolute rubric scores are supplementary.
- **Coding/regex-based property checks**: more deterministic, but the kinds of properties ProblemForm cares about ("disambiguates 'nothing'", "separates semantics from metaphysics") are not regex-checkable. We need an LLM judge for these.
- **Human-only evaluation**: highest signal, lowest throughput; not viable for regression testing. We may support exporting cases for human spot-checking but won't require it.
- **Statistical comparison of generated answer embeddings**: tempting, but answers can be cosmetically identical and substantively different (or vice versa). Embedding similarity doesn't map cleanly to "is this better?"
- **Answer-generation wrapper prompt**: rejected as a confound. The eval would conflate ProblemForm's effect with the wrapper's effect. Engine calls `provider.generate_text(...)` directly on both `raw_question` and `refined_prompt`. If the answer model needs framing instructions, that belongs upstream of ProblemForm (encoded by the synthesizer itself).
- **HTML report**: Markdown renders everywhere, diffs cleanly in PRs, and matches existing CLI conventions. We can add HTML later if eyeballing 50+ cases becomes painful.

---

## 3. Data model

All Pydantic, following the existing `problemform.models` conventions. Lives in a new `problemform/eval/models.py`.

### Corpus types

**[APPROVED — Phase A]**

```python
class TestCase(BaseModel):
    name: str
    category: str
    raw_question: str
    tags: list[str] = []
    expected_properties: list[str] = []     # stored; NOT evaluated until Phase B
    expected_failure_modes: list[str] = []  # stored; NOT evaluated until Phase B
    notes: str | None = None
    schema_version: int = 1
```

**[DEFERRED — Phase B]**

```python
class RubricCriterion(BaseModel):
    name: Literal["accuracy", "completeness", "relevance", "clarity",
                  "actionability"] | str
    description: str
    scale_min: int = 1
    scale_max: int = 5

class Rubric(BaseModel):
    name: str
    description: str
    criteria: list[RubricCriterion]
    schema_version: int = 1
```

### Per-case evaluation types

**[APPROVED — Phase A]**

```python
Materiality = Literal["material", "minor", "stylistic_only", "degradation"]

class ComparativeJudgment(BaseModel):
    target: Literal["answer"]                    # only "answer" in Phase A
    presented_first_actual: Literal["raw", "refined"]
    winner: Literal["a", "b", "tie"]
    winner_actual: Literal["raw", "refined", "tie"]   # de-anonymized
    materiality: Materiality
    rationale: str
    key_differences: list[str]
    # Answer text is NOT duplicated here. It lives once in the parent
    # TestCaseResult to avoid triplicate copies inside the JSON.

class TestCaseResult(BaseModel):
    test_case: TestCase
    raw_prompt: str
    refined_prompt: str
    problem_state_path: str | None
    raw_answer: str                              # inline; see rationale below
    refined_answer: str                          # inline
    comparative_judgment: ComparativeJudgment | None   # None when case errored
    errors: list[str] = []
    timing: dict[str, float] = {}                # phase -> seconds

class AggregateMetrics(BaseModel):
    n_cases: int
    n_completed: int
    n_errored: int
    n_refined_wins: int
    n_raw_wins: int
    n_ties: int
    refined_win_rate: float | None
    raw_win_rate: float | None
    tie_rate: float | None
    material_improvement_rate: float | None  # winner_actual=="refined" AND materiality=="material"
    degradation_rate: float | None           # materiality=="degradation"

class BenchmarkReport(BaseModel):
    run_id: str                              # ISO + 6-char hash
    started_at: datetime
    finished_at: datetime
    config: dict                             # roles, models, max_iterations, position-randomized flag
    bias_warnings: list[str] = []            # populated when same-family judging detected
    test_case_results: list[TestCaseResult]
    aggregate: AggregateMetrics
    schema_version: int = 1
```

#### Notable resolved decisions

- **Answer text inline on `TestCaseResult`, NOT path-only.** Self-contained `report.json` is worth the ~20–40 KB overhead at Phase A scale and the ~1 MB overhead at 50 cases. Per-case `.txt` files are *also* written for human inspection — they are complementary (txt for humans, JSON for tools), not redundant. The path-only alternative was considered and rejected as premature optimization; revisit at Phase C if size becomes a real problem.

- **`comparative_judgment` is singular, not a list, in Phase A.** K=1 is the only mode at MVP. Phase C promotes the field to `comparative_judgments: list[ComparativeJudgment]` via a one-time schema bump (Phase A code is internal — no external consumers to migrate).

- **`AggregateMetrics` exposes the full three-way scoreboard.** The Markdown headline shows refined-wins, raw-wins, ties, material-improvement rate, and degradation rate side-by-side. A 60% refined win rate must not be celebratable without simultaneously showing the corresponding raw wins and degradations. This is structural insurance against the report becoming an advocacy artifact for ProblemForm.

- **No aggregate `overall_score`** synthesized from per-criterion scores (when rubrics arrive in Phase B). Per-criterion bars in the report; no spurious-precision averaged number.

- **`presented_first_actual` and `winner_actual`** on `ComparativeJudgment` make position-bias detectable post-hoc even if randomization is forgotten.

**[DEFERRED — Phase B]**

```python
class CriterionScore(BaseModel):
    criterion: str
    score: int
    rationale: str                               # qualitative, mandatory

class RubricEvaluation(BaseModel):
    target: Literal["raw_prompt", "refined_prompt",
                    "raw_answer", "refined_answer"]
    rubric_name: str
    scores: list[CriterionScore]
    overall_rationale: str                       # synthesis, NOT an averaged score

class PropertyCheck(BaseModel):
    property: str
    present_in_refined: bool
    present_in_raw: bool
    rationale: str
```

**[DEFERRED — later]**

```python
class GenerationMetadata(BaseModel):
    role: Literal["pf", "answer", "judge"]
    provider: str
    model: str
    temperature: float
```

Run-level role/provider/model are already captured once in `BenchmarkReport.config` for Phase A; per-case metadata would only matter if cases used different providers, which Phase A doesn't.

---

## 4. Directory structure

Two distinct roots: **corpus** (committed) and **results** (gitignored).

### Corpus (repo-committed)  **[APPROVED — Phase A]**

```
benchmarks/                               # repo root
  README.md
  default/
    philosophy/
      cosmology_nothingness.yaml
    practical/
      code_review_prep.yaml
    technical/
      api_design_rest_vs_graphql.yaml
    parenting/
      teach_kid_to_swim.yaml
    control/
      what_causes_eclipses.yaml           # control case (see Section 5)
```

**[DEFERRED — Phase B]**

```
benchmarks/
  rubrics/
    answer_quality.yaml
    prompt_quality.yaml
```

**Why `benchmarks/` at the repo root?** It's user content, not library code. Putting it inside `problemform/` would invite the implementation to assume ownership of test cases — the failure mode flagged in the original brief. Placing it at the root makes "users add/remove/organize" the obvious workflow.

### Results (gitignored)  **[APPROVED — Phase A]**

```
.problemform/                             # gitignored
  eval_runs/
    2026-06-04T16-12-00_a1b2c3/
      report.json                         # full BenchmarkReport
      report.md                           # human summary
      cases/
        cosmology_nothingness/
          problem_state.json              # full ProblemState
          raw_answer.txt
          refined_answer.txt
```

**Why `.problemform/eval_runs/` and not `problemform/.eval/`?** Eval results are local-machine artifacts. A dotted top-level config-style dir matches the precedent of `.git/`, `.vscode/`, `.conda/`; it's gitignored by convention and lives outside the package code.

Both paths are configurable via env vars (`PROBLEMFORM_BENCHMARKS_DIR`, `PROBLEMFORM_EVAL_RUNS_DIR`) and flags.

---

## 5. CLI design

Reuses the existing Typer app.

### `problemform benchmark <suite>`  **[APPROVED — Phase A]**

```
problemform benchmark benchmarks/default \
    [--pf-provider openai] [--pf-model gpt-5.4]                     \
    [--answer-provider anthropic] [--answer-model claude-sonnet-4-6]\
    [--judge-provider openai]   [--judge-model gpt-5.4]             \
    [--max-iterations 1]                                            \
    [--output .problemform/eval_runs/{auto-ts}]                     \
    [--format md]
```

Default behavior: runs every YAML in the suite, produces a full report. `--randomize-order` on by default; refusal to silently same-family the judge is **warn-only** (see §7).

### Deferred CLI surface  **[DEFERRED — Phase B/C]**

- **`problemform eval <input>`** [Phase B] — single-case evaluation with two modes:
  - `problemform eval state.json` — eval a saved ProblemState.
  - `problemform eval --raw "..."` — ad hoc one-off through the full pipeline.
- **`problemform report <run-dir>`** [Phase C] — re-render an existing run dir as Markdown.
- **`problemform corpus validate <suite>`** [Phase B] — syntax-check YAML.
- **`problemform corpus list <suite>`** [Phase B] — show name/category/tags table.

### Why not just extend `agent` or `run`?

`benchmark` and `eval` have fundamentally different shape (multiple cases, multiple roles, multi-stage pipeline per case). Folding them into existing commands would force `--state` and `--output` to mean two different things in different modes. Separate commands keep each surface single-purpose.

---

## 6. Evaluation workflow (per test case)

```
TestCase
  |
  |  raw_question
  v
ProblemForm.run(raw_question, pf_provider, max_iterations=1)
  |
  +---> refined_prompt = state.final_prompt
  |     problem_state snapshot persisted to cases/<name>/problem_state.json
  v
Generate answers (direct calls, no wrapper prompt):
  raw_answer      = answer_provider.generate_text(raw_question)
  refined_answer  = answer_provider.generate_text(refined_prompt)
  |
  v
Judgments (judge_provider):
  +-- Comparative judgment (answer pair)    <- Level 4, HEADLINE   [Phase A]
  +-- Rubric eval (raw_answer)              <- Level 1             [Phase B]
  +-- Rubric eval (refined_answer)          <- Level 1             [Phase B]
  +-- Comparative judgment (prompt pair)    <- Level 2             [Phase B]
  +-- Property checks vs expected_properties <- Level 3            [Phase B]
  |
  v
TestCaseResult assembled, written to cases/<name>/
+ aggregated into the BenchmarkReport at the end
```

### Failure containment  **[APPROVED — Phase A]**

Any exception during steps 2–4 of a case is caught, recorded in `TestCaseResult.errors`, and the case is marked errored. The benchmark loop **continues** to the next case. A 20-case run with one failure produces a 19-case successful report plus 1 errored entry; it does **not** abort.

- Errored cases have `comparative_judgment is None` and `errors` non-empty.
- Aggregate rates compute over `n_completed`, not `n_cases`.
- The Markdown report's Errors section lists each errored case and the phase that failed.

### Iteration budget per test case  **[APPROVED — Phase A: 1]**

Default `max_iterations = 1` for cost containment. Two motivations: (1) the per-case PF run is expensive on reasoning models; (2) `max_iterations 1` is the cheapest signal that says "the synthesizer made a meaningful change on the first pass," which is the strongest single-shot answer to "is ProblemForm helping?" Higher iteration counts opt-in via `--max-iterations N`.

### Starter corpus  **[APPROVED — Phase A: 5 cases including 1 control]**

The five starter cases are calibrated to exercise different ProblemForm strengths *and* include one **structural control** to detect cases where refinement is unnecessary or harmful.

1. **`philosophy/cosmology_nothingness.yaml`** — disambiguation under metaphysical fuzziness.
2. **`practical/code_review_prep.yaml`** — context elicitation (what kind of code, stakes, role).
3. **`technical/api_design_rest_vs_graphql.yaml`** — surfacing of latent constraints.
4. **`parenting/teach_kid_to_swim.yaml`** — context elicitation (age, fears, prior exposure).
5. **`control/what_causes_eclipses.yaml`** — **control case**. Well-formed factual question with depth (solar vs lunar, geometry, frequency). ProblemForm may add useful clarification or may bloat a well-formed question; a degradation here would be diagnostic. The control's `expected_properties` reflect "does NOT lose substance" / "remains scientifically accurate" rather than "elicits more clarification."

The control case is the explicit guard against the corpus naturally favoring ProblemForm. Its degradation rate matters as much as the average's win rate.

---

## 7. Bias mitigations

All of these are first-class in the data model and reflected in the report.

| Bias | Mitigation | Status |
|---|---|---|
| **Position bias** | A/B presentation order randomized per comparison. `presented_first_actual` captured. | **[APPROVED — Phase A]**: mandatory. |
| **Self-preference** | Judge family vs answer family heuristic check; **warn loudly** when they match, do not block. Override is the default (no override needed); warning printed to stderr and recorded in `BenchmarkReport.bias_warnings`. | **[APPROVED — Phase A]**: warn-only. Blocking was considered and rejected as too annoying for MVP. |
| **Verbosity bias** | Judge prompt explicitly instructs to penalize length-without-substance. Answer lengths captured for inspection. | **[APPROVED — Phase A]** |
| **Convergence-judge contamination** | Eval judge uses an independent prompt. Explicitly NOT reusing `agents/convergence_judge.py`. | **[APPROVED — Phase A]** |
| **Single-shot noise** | Architecture supports `--judgments-per-pair K` with aggregation. | **[DEFERRED — Phase C]**: MVP runs K=1; Phase C adds K>1. |
| **Specification gaming** | Encourage held-out cases via `tags: [holdout]` convention. Aggregate reports `held-out only` and `dev only` separately. | **[DEFERRED — Phase C]** |

### Honesty mechanism in the headline

The Markdown report leads with the configuration that produced it:

> **Headline:** Refined wins **60%** | Raw wins **20%** | Ties **20%** (n=5, K=1, position-randomized).
> **Material improvement rate:** 40%. **Degradation rate:** 0%.
> **Judge:** anthropic / claude-sonnet-4-6 (different family from answer model: yes)
> **Caveats:** K=1; sample size below significance threshold.

The final "Caveats" line is the cheapest insurance against developers (us) seeing 60% and forgetting the sample is 5.

---

## 8. Reporting format

Two outputs side-by-side, every run.

### `report.json`  **[APPROVED — Phase A]**

Complete `BenchmarkReport` Pydantic dump. Machine-readable. Self-contained (includes inline answer text). Used by any future `report` re-rendering and by anyone diffing across runs.

### `report.md`  **[APPROVED — Phase A]**

Human summary. Sections, in order:

1. **Headline** — refined-wins / raw-wins / ties side-by-side, material-improvement rate, degradation rate; sample size and caveats.
2. **Configuration** — providers/models for all three roles, bias mitigations active, same-family-judge warning if applicable.
3. **Aggregate scoreboard** — three-way counts, material-improvement rate, degradation rate, errors.
4. **Per-case table** — one row per case: name | category | winner | materiality.
5. **Cases where refined was worse than raw** — the diagnostic section. Populated from cases where `winner_actual == "raw"` OR `materiality == "degradation"`. Each gets key differences and judge rationale. **This section is the most important because it's the most likely to be ignored if buried.**
6. **Errors** — per-case error list with the phase that failed.

Per-case raw artifacts (full `ProblemState`, `raw_answer.txt`, `refined_answer.txt`) live in `cases/<name>/`. The Markdown report links into them.

### Deferred report content  **[DEFERRED — Phase B/C]**

- Average rubric scores per target (Phase B).
- Expected-property satisfaction delta (Phase B).
- Breakdown by category / tag beyond simple per-case display (Phase C).
- Inter-judge agreement metrics (Phase C).

### Rejected report formats  **[REJECTED]**

- **HTML.** Out of scope. Markdown renders everywhere, diffs cleanly in PRs, matches existing CLI conventions.

---

## 9. Implementation order (phased)

Each phase is independently shippable and produces a stronger signal than the previous one.

### Phase A — "Is ProblemForm helping?"  **[APPROVED — current scope]**

Smallest cut that produces a defensible headline number.

- `problemform/eval/models.py`: `TestCase`, `ComparativeJudgment`, `TestCaseResult`, `BenchmarkReport`, `AggregateMetrics`, `Materiality`.
- `problemform/eval/corpus.py`: YAML load + validate.
- `problemform/eval/judges.py`: comparative-judgment judge (Level 4). Position randomization mandatory.
- `problemform/eval/engine.py`: per-case pipeline (PF run; 2 direct answer generations; 1 comparative judgment). Failure containment.
- `problemform/eval/report.py`: aggregate + Markdown + JSON.
- CLI: `problemform benchmark <suite>` only.
- Starter corpus: 5 cases (4 ambiguity + 1 control).
- Tests: schema parsing, position randomization, full pipeline against stubs, failure containment.
- Documented bias caveats in the report.

**Deliverable**: `problemform benchmark benchmarks/default` produces a JSON+MD report whose headline is "refined-answer win rate, raw-answer win rate, ties, material improvement, degradation."

### Phase B — Levels 1, 2, 3 layered on  **[DEFERRED]**

- Rubric evaluations (`RubricEvaluation`, judge prompt, average scoring).
- Comparative *prompt* judgments (Level 2).
- Expected-property checks (Level 3).
- `problemform eval` single-case command.
- `problemform corpus validate` / `corpus list`.
- One built-in rubric YAML under `benchmarks/rubrics/answer_quality.yaml`.

### Phase C — Robustness  **[DEFERRED]**

- `--judgments-per-pair K>1` with majority/agreement aggregation.
- `problemform report` re-render.
- Held-out vs dev breakdowns via `tags: [holdout]`.
- Inter-judge agreement metrics when K>1.
- Failure-mode-targeted reporting.
- Promote `comparative_judgment` from singular to `comparative_judgments: list[...]` (schema bump).

### Phase D — Quality-of-life and later  **[DEFERRED]**

- HTML report or simple TUI viewer.
- Human-in-the-loop export: dump pairs to a CSV for manual scoring; ingest scored CSV back.
- Per-run diff command: `problemform benchmark diff run-A run-B`.
- Eval-CI integration (run on PRs that touch prompts).
- Cost & token accounting per role / per case.

---

## 10. MVP scope (Phase A)  **[APPROVED]**

A single sentence: **`problemform benchmark <suite>` produces a JSON + Markdown report whose headline shows refined-wins, raw-wins, ties, material-improvement rate, and degradation rate of `refined_answer` vs `raw_answer` under a (preferably cross-family) judge, with position randomization on by default and configuration captured in the report.**

Levels 1, 2, 3 strengthen the signal in later phases but do not move the headline.

---

## 11. Future extensions  **[DEFERRED — beyond Phase D]**

- Cost & token accounting per role, per case.
- Streaming results so long runs are inspectable in flight (reuse `--checkpoint` pattern).
- Judge ensemble: multiple judges with reported agreement. Best mitigation against any single judge's blind spots.
- Counterfactual analysis: "if we removed the alternative-framing phase, what would the win rate be?" Requires a configurable workflow.
- Snapshot testing for prompts. Pin reference answers and detect when prompt changes shift them beyond threshold.
- Public corpus, once the project has matured.

---

## 12. Tradeoffs & risks

These apply across all phases.

- **Cost.** A benchmark run is roughly `n_cases x (1 PF run + 2 answer gens + 1 judge call)` at Phase A; with rubrics + property checks in Phase B that grows. For 10 cases at K=1 that's ~50 LLM calls; for 50 cases at K=3 that's ~900. The eval framework can outspend the rest of the project by a wide margin if used casually. Mitigation: small default suites, judge model overridable to cheaper tier, K=1 default.
- **Reasoning-model latency.** `gpt-5.4` already takes minutes per call; eval runs will be slow. Mitigation: per-case `--checkpoint` plus eventual parallelism (deferred — adds complexity).
- **Judge gaming.** If we tune ProblemForm to win on the benchmark, the benchmark stops measuring. Mitigation: held-out cases (convention, Phase C), inter-judge agreement (Phase C), control case in starter corpus (Phase A).
- **Schema drift.** TestCase schema will evolve. Mitigation: explicit `schema_version` field with migration helpers planned for Phase C.
- **Reproducibility.** Different runs of the same benchmark give different numbers. Mitigation: capture full config in `report.json`; compare runs at fixed config.
- **False sense of rigor.** A benchmark with n=5 and K=1 looks numeric but is noisy. The "Caveats" line in the headline is the cheapest insurance against publishing single-decimal-place win rates without sample-size disclaimers.
- **Risk of orienting around a single metric.** Win rate is the headline but is not the only thing. The "Cases where refined was worse" diagnostic section is what keeps us honest. The Markdown layout makes that section unmissable on purpose.
- **No held-out evaluation infrastructure at MVP.** Phase A doesn't enforce a holdout. Phase B should not iterate prompts on the same corpus too aggressively without Phase C's split mechanism.

---

## 13. Resolved decisions for Phase A  **[APPROVED — locked]**

These were open during the design process and have been resolved. Recording them here so future readers don't re-litigate.

1. **Same-provider judge policy**: **warn loudly, do not block**. Blocking was considered and rejected as too annoying for MVP. Warning surfaces in stderr and in `BenchmarkReport.bias_warnings`.
2. **Starter corpus**: **5 hand-picked cases**, including 1 explicit control case, shipped under `benchmarks/default/`.
3. **`benchmarks/` location**: **repo root**. User content, not library code.
4. **Results directory**: **`.problemform/eval_runs/`**. Gitignored, namespaced for future run types.
5. **`max_iterations` default for the per-case PF run**: **1**. Cheap, headline-friendly. Higher counts opt-in.
6. **Provenance**: **save full `ProblemState`** per case under `cases/<name>/problem_state.json`. Disk is cheaper than re-running.
7. **Error type**: **reuse `StructuredOutputError`**. No `EvaluationError` subclass; eval is just another LLM consumer.
8. **Answer text storage**: **inline on `TestCaseResult`** (`raw_answer: str`, `refined_answer: str`), plus `.txt` files for human inspection. `ComparativeJudgment` does NOT duplicate the answer text (one less copy). Path-only-on-result was considered and rejected as premature optimization.
9. **Judgments-per-pair shape**: **`comparative_judgment: ComparativeJudgment | None`** (singular). Phase C promotes to a list via schema bump.
10. **Answer-generation prompt**: **none**. Engine calls `provider.generate_text(...)` directly on both raw and refined. Wrapper prompt would be a confound.
11. **Control case form**: **factual question, not coding task**. The corpus is about question-formulation; a coding task introduces a different evaluation axis.
12. **Failure containment**: **continue, capture errors, exclude from aggregate denominators**. A 20-case run does not abort because case 17 fails.

---

## 14. Explicitly rejected / not currently planned  **[REJECTED]**

Do not re-propose these without reopening the discussion.

- Pure absolute-score-only system (no comparative primitive).
- Coding/regex-based property checks (we use an LLM judge for these).
- Human-only evaluation (we may export pairs for manual scoring later, but cannot rely on it for regression).
- Embedding similarity for answer comparison.
- HTML report (Markdown is sufficient through Phase D).
- Public corpus, until project matures.
- Answer-generation wrapper prompt (confound).
- Blocking on same-family judge (warn-only is the chosen policy).
- Path-only storage of answers in `TestCaseResult` (premature optimization).
- Per-case `GenerationMetadata` (run-level `config` is sufficient until cases vary providers).

---

## 15. When to use this document

- **Implementing Phase A**: read Section 9 (Phase A scope) and Section 13 (resolved decisions). Sections 3, 4, 5, 6, 7, 8 contain the data model, layout, CLI shape, and report shape with `[APPROVED]` tags marking what to build.
- **Starting Phase B / C / D**: read Section 9 for that phase's scope, then re-read Sections 3 and 7 to see what was deferred there. **Update this document** as the design evolves — but only to record new decisions, not to revise the historical reasoning.
- **Considering a feature that's tagged `[REJECTED]` or `[DEFERRED]`**: read the rationale in Section 14 (rejected) or Section 9 (phased deferrals) before re-proposing. If the rejection still stands, no need to discuss again.
- **Investigating a regression in benchmark results**: Sections 7 (bias mitigations) and 12 (tradeoffs & risks) document the known confounders and noise sources.

This document is architectural memory. The active milestone tracker (whatever form that takes) is the source of truth for what's currently being implemented.
