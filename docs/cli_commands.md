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

Run a YAML test-case suite end-to-end and write JSON + Markdown reports comparing answers produced from the raw question against answers produced from the ProblemForm-refined prompt.

Invocation:

```
problemform benchmark <suite-path> \
    [--pf-provider PROV] [--pf-model NAME] \
    [--answer-provider PROV] [--answer-model NAME] \
    [--judge-provider PROV] [--judge-model NAME] \
    [--max-iterations N] \
    [--output PATH] \
    [--format {md|json}]
```

Three provider roles:

- **ProblemForm provider** — runs the refinement pipeline on each test case's raw question.
- **Answer provider** — generates one answer from the raw question and one from the refined prompt.
- **Judge provider** — performs a position-randomized comparative judgment between the two answers.

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

1. Refine the raw question via `problemform.core.workflow.run` (default `--max-iterations 1`).
2. Generate `raw_answer = answer_provider.generate_text(raw_question)`.
3. Generate `refined_answer = answer_provider.generate_text(refined_prompt)`.
4. Run one position-randomized comparative judgment on the answer pair.
5. Persist artifacts and append a result entry.

Bias mitigations:

- A/B order is randomized per comparison; `presented_first_actual` is recorded.
- The judge prompt is label-agnostic — the words "raw" and "refined" are not present.
- When the answer and judge providers share a family, a self-preference warning is emitted to stderr and recorded in `BenchmarkReport.bias_warnings`. The run is **not** blocked.

Failure containment:

- Any exception during a case's pipeline (refinement, answer generation, or judging) is captured into the case's `errors[]`. The benchmark loop continues to the next case.
- Aggregate rates are computed over completed cases only (`n_completed`), not attempted cases (`n_cases`).

Outputs:

- `--output PATH` (default `.problemform/eval_runs/<auto-id>/`) receives:

  ```
  report.json                              # full BenchmarkReport
  report.md                                # human-readable report
  cases/<case-name>/problem_state.json     # full ProblemState per case
  cases/<case-name>/raw_answer.txt         # raw answer (human inspection)
  cases/<case-name>/refined_answer.txt     # refined answer (human inspection)
  ```

- `--format` (default `md`) selects which of `report.json` / rendered Markdown is printed to stdout for piping. Both files are always written under `--output`.

Report contents:

- Headline scoreboard: refined-win rate, raw-win rate, tie rate, material-improvement rate, degradation rate.
- Configuration block: three providers' roles, models, position-randomized flag, judgments-per-pair, bias warnings.
- Per-case table: case | category | winner | materiality.
- Diagnostic section: cases where refined was worse than raw or marked degradation.
- Errors section: per-case error lists.

Purpose:

- Measure whether ProblemForm produces materially better answers than the raw question.
- Detect regressions in prompt refinements, agents, or workflow changes.
- Establish a stable benchmark surface that future architectural changes can be validated against.

See [`designs/milestone_03_evaluation_framework.md`](designs/milestone_03_evaluation_framework.md) for the full design rationale and [`../benchmarks/README.md`](../benchmarks/README.md) for the corpus layout.