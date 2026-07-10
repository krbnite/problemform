# CLI Commands

## analyze

Run all analytical phases of ProblemForm without generating a refined prompt.

Runs:

- Objective Analysis
- Assumption Excavation
- Information-Gap Detection
- Expert Panel Generation
- Alternative Framing
- Meta-Question Generation

Outputs an updated ProblemState containing the accumulated analysis artifacts.

Does not perform prompt synthesis.

Does not perform convergence evaluation.

Purpose:

- Understand the current formulation.
- Identify assumptions, information gaps, perspectives, alternative framings, and meta questions.
- Create a ProblemState that may be further refined, judged, exported, or inspected.

---

## synthesize

Generate a refined prompt from an existing ProblemState.

Runs:

- Prompt Synthesis

Outputs:

- Refined prompt
- Updated prompt history
- Updated ProblemState

Does not perform additional analysis.

Does not perform convergence evaluation.

Purpose:

- Transform analytical insights into an improved formulation.

---

## judge

Evaluate whether the current formulation has reached convergence.

Runs:

- Convergence Evaluation

Outputs:

- Convergence status
- Convergence rationale
- Remaining opportunities for refinement

Does not perform additional analysis or synthesis.

Purpose:

- Determine whether further refinement is likely to produce material improvements.

---

## run

Execute the complete ProblemForm workflow.

Each iteration performs:

- Objective Analysis
- Assumption Excavation
- Information-Gap Detection
- Expert Panel Generation
- Alternative Framing
- Meta-Question Generation
- Prompt Synthesis
- Convergence Evaluation

Stops when:

- Convergence status is CONVERGED, or
- max_iterations is reached.

Outputs:

- Final prompt
- Final ProblemState
- Prompt history
- Convergence assessment

Purpose:

- Fully refine a problem formulation using the complete ProblemForm methodology.

---

## explain

Display the contents of the current ProblemState in a human-readable format.

May include:

- objectives
- assumptions
- information gaps
- expert panel perspectives
- alternative framings
- meta questions
- prompt history
- convergence status

Does not modify the ProblemState.

Purpose:

- Inspection
- Transparency
- Debugging
- Understanding how ProblemForm arrived at its conclusions

---

## export

Persist a ProblemState and its artifacts to an external format.

Supported formats may include:

- JSON
- Markdown

Exported information may include:

- raw input
- objectives
- assumptions
- information gaps
- expert panel perspectives
- alternative framings
- meta questions
- prompt history
- final prompt
- convergence assessment

Does not modify the ProblemState.

Purpose:

- Save work
- Share results
- Resume refinement later
- Integrate with external tools or workflows

---

## agent

Run a single ProblemForm phase against an existing ProblemState.

Invocation:

```
problemform agent <agent-name> <state-path> [--output PATH] [--provider PROV] [--model NAME] [--format {md|json}]
```

Supported agent names:

- objective-analysis
- assumption-excavation
- information-gap-detection
- expert-panel
- alternative-framing
- meta-questions
- prompt-synthesis
- convergence-evaluation

Runs exactly the corresponding phase from the workflow against the loaded
ProblemState and returns the updated state.

Outputs:

- Updated ProblemState written to `--output PATH` when provided.
- Otherwise printed to stdout in the chosen `--format` (default `md`).

Validation:

- Unknown agent names produce a clear error listing the supported names.
- Missing or unreadable state files fail with a clear error.
- Malformed state JSON fails with a clear parse-failure error.

Purpose:

- Manual orchestration
- Debugging individual phases
- Experimentation with custom workflows
- Re-running one phase without re-running the full pipeline

Notes:

- `agent` is an advanced command intended for experimentation, debugging, and workflow customization.
- The standard ProblemForm workflow should normally be executed via `analyze`, `synthesize`, `judge`, or `run`.
- Agents may be executed multiple times against the same ProblemState.
- Users are responsible for ensuring that the resulting workflow remains logically coherent when manually orchestrating agents.

---

## benchmark

Run a YAML test-case suite end-to-end and write JSON + Markdown reports. For
*answerable* formulation types the report compares answers produced from the raw
formulation against answers from the ProblemForm-refined prompt (the M3A lens);
for *formulation-only* types that lens is skipped and the signal comes from the
formulation rubric (see **Answer-lens gating** below).

Invocation:

```
problemform benchmark <suite-path> \
    [--pf-provider PROV] [--pf-model NAME] \
    [--answer-provider PROV] [--answer-model NAME] \
    [--judge-provider PROV] [--judge-model NAME] \
    [--rubric PATH ...] [--property-suite PATH ...] \
    [--answer-comparison | --no-answer-comparison] \
    [--max-iterations N] \
    [--output PATH] \
    [--format {md|json}]
```

Three provider roles:

- **ProblemForm provider** — runs the refinement pipeline on each test case's raw formulation.
- **Answer provider** — generates one answer from the raw formulation and one from the refined prompt, **for answer-applicable cases only**. It is constructed lazily: if no case in the run uses the answer lens, it is not built at all (see **Answer-lens gating**).
- **Judge provider** — performs the position-randomized comparative judgment (answerable cases) and scores rubric criteria / property checks.

Each role has its own `--*-provider` / `--*-model` flags. Resolution precedence is:

1. The role's CLI flag (e.g. `--answer-provider`).
2. The role's environment variable, if defined:
   - Answer role: `PROBLEMFORM_EVAL_ANSWER_PROVIDER`, `PROBLEMFORM_EVAL_ANSWER_MODEL`.
   - Comparative Answer Judge role: `PROBLEMFORM_EVAL_JUDGE_PROVIDER`, `PROBLEMFORM_EVAL_JUDGE_MODEL`.
   - ProblemForm role: no role-specific variables; it uses the generic ones directly.

The `PROBLEMFORM_EVAL_*` variables are scoped to the evaluation framework. They do not affect the workflow's Convergence Judge (the `convergence_evaluation` phase in `run` or the standalone `judge` command).
3. The generic environment variables `PROBLEMFORM_PROVIDER` / `PROBLEMFORM_MODEL` (the same fallback `problemform run` uses).
4. The built-in defaults (`openai` + `DEFAULT_OPENAI_MODEL`).

Per-case workflow:

1. Refine the raw formulation via `problemform.core.workflow.run` (default `--max-iterations 1`).
2. **If the case is answer-applicable** (see gating): generate `raw_answer` and
   `refined_answer` from the answer provider, and run one position-randomized
   comparative judgment on the pair. Otherwise these three steps are **skipped** —
   no answers, no judge call, no answer artifacts — and the case is recorded as
   *answer-skipped*.
3. Score any configured rubrics and property checks against the raw and refined subjects (see next).
4. Persist artifacts and append a result entry.

Answer-lens gating (M3B-β.1):

The M3A answer-comparison lens runs only for formulation types whose refinement
naturally induces a downstream artifact whose quality we care about. The policy lives
in `problemform/eval/policy.py`:

- **Answerable** (lens runs): `question`, `explanation`, `instruction`, `prompt`, `specification`.
- **Formulation-only** (lens skipped): `argument`, `belief`, `decision`, `dilemma`, `goal`, `plan`.
- **`unspecified` / unknown** → answerable (legacy behavior).
- `--answer-comparison` / `--no-answer-comparison` force the lens on/off for the whole
  run, overriding the per-type policy; omitting the flag uses the policy.

Consequences of a skip: no answer-provider calls, no comparative judgment
(`comparative_judgment` is `null`), and no `raw_answer.txt` / `refined_answer.txt`
written. Such a case counts in `n_answer_skipped` (not `n_errored`) and its Winner
renders as `skipped`. When **no** case in a run is answer-applicable (a wholly
formulation-only corpus, or `--no-answer-comparison`), the **answer provider is not
constructed**, the same-family warning is not emitted, and the report Configuration
records the Answer role as `not_used`. A `ValueError` is raised up front if an answer
provider is required by policy but unavailable.

Rubric and property lenses (M3B-α):

Alongside the comparative answer judgment, each run applies two further lenses. All three are reported **in parallel and never collapsed into a single score**.

- **Rubrics** (`--rubric PATH`, repeatable). Absolute-mode rubrics score a subject against weighted criteria, normalized to 0–1 and aggregated per rubric (raw mean, refined mean, and refined−raw delta). A rubric's `target` decides the subject: `formulation` scores the raw question vs the refined prompt; `artifact` scores the raw vs refined answer. `PATH` may be a single YAML file or a directory (walked recursively).
- **Property suites** (`--property-suite PATH`, repeatable). Binary "should always hold" assertions, reported as raw/refined pass rates per property. `target` routes the subject the same way as rubrics.
- **Activated `expected_properties`.** Each corpus case's `expected_properties` strings are always activated as `target=formulation`, `expected=True` checks for that case — independent of the `--property-suite` flag.
- **Disagreement diagnostic.** The report flags cases where the comparative-answer verdict and a `target=formulation` rubric's delta point in different directions (the high-value cases for human review).

Default loading and override:

- **No `--rubric`** → the shipped default rubrics load (all YAML under `benchmarks/rubrics/`: `formulation_quality_v1`, `answer_quality_v1`).
- **No `--property-suite`** → the shipped default suites load (all YAML under `benchmarks/properties/`: `artifact_baseline_v1`).
- **Passing the flag overrides** the corresponding default set entirely (it does not add to it). Repeated flags accumulate among themselves; pass the default path explicitly to include it alongside custom paths. To run with no shared property suite, point `--property-suite` at an empty directory (per-case `expected_properties` still activate).
- Default paths are resolved relative to the installed package (repo root), so they load regardless of the working directory.

Bias mitigations:

- A/B order is randomized per comparison; `presented_first_actual` is recorded.
- The judge prompt is label-agnostic — the words "raw" and "refined" are not present.
- When the answer and judge providers share a family, a self-preference warning is emitted to stderr and recorded in `BenchmarkReport.bias_warnings` — **only when the answer lens actually runs** (skipped for wholly formulation-only / `--no-answer-comparison` runs, where no answer provider is built). The run is **not** blocked.

Failure containment:

- Any exception during a case's pipeline (refinement, answer generation, or judging) is captured into the case's `errors[]`. The benchmark loop continues to the next case.
- Aggregate rates are computed over completed cases only (`n_completed`), not attempted cases (`n_cases`).

Outputs:

- `--output PATH` (default `.problemform/eval_runs/<auto-id>/`) receives:

  ```
  report.json                              # full BenchmarkReport
  report.md                                # human-readable report
  cases/<case-name>/problem_state.json     # full ProblemState per case
  cases/<case-name>/raw_answer.txt         # raw answer — answer-applicable cases only
  cases/<case-name>/refined_answer.txt     # refined answer — answer-applicable cases only
  ```

  The two answer files are **not** written for formulation-only cases (answer lens skipped).

- `--format` (default `md`) selects which of `report.json` / rendered Markdown is printed to stdout for piping. Both files are always written under `--output`.

Report contents:

- Headline scoreboard: refined-win rate, raw-win rate, tie rate, material-improvement rate, degradation rate.
- Configuration block: three providers' roles, models, position-randomized flag, judgments-per-pair, bias warnings.
- Rubric evaluations: per-rubric target, raw mean, refined mean, and refined−raw delta.
- Property checks: per-property target and raw/refined pass rates.
- Disagreement diagnostic: cases where the comparative-answer verdict and the formulation-rubric delta diverge.
- Per-case table: case | category | winner | materiality.
- Diagnostic section: cases where refined was worse than raw or marked degradation.
- Errors section: per-case error lists (including any rubric/property lens failures, which are contained per case and do not drop the case from the M3A scoreboard).

Purpose:

- Measure whether ProblemForm produces materially better answers than the raw question.
- Detect regressions in prompt refinements, agents, or workflow changes.
- Establish a stable benchmark surface that future architectural changes can be validated against.

See [`designs/milestone_03_evaluation_framework.md`](designs/milestone_03_evaluation_framework.md) for the full design rationale and [`../benchmarks/README.md`](../benchmarks/README.md) for the corpus layout.