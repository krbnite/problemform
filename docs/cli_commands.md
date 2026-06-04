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