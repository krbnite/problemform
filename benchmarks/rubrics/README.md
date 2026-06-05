# Rubrics

Each YAML file under this directory is one **rubric** — a named, ordered collection of weighted criteria that an LLM judge scores against either a *formulation* (the prompt / problem statement produced by ProblemForm) or an *artifact* (the downstream answer).

See [`docs/designs/milestone_03b_rubrics_and_properties.md`](../../docs/designs/milestone_03b_rubrics_and_properties.md) for the design rationale and the role of rubrics as the bridge from question-refinement evaluation (M3A) toward general problem-formulation evaluation.

## File shape

One rubric per file. The loader (`problemform.eval.corpus.load_rubrics`) accepts either a path to a single YAML file or a path to a directory walked recursively.

```yaml
name: formulation_quality_v1
description: |
  Baseline rubric for evaluating a refined formulation's clarity, completeness,
  and surfacing of hidden assumptions. Input-agnostic on purpose.
target: formulation          # "formulation" | "artifact"
mode: absolute               # M3B-α ships absolute-mode rubrics only
schema_version: 1
notes: |
  Free-form rationale or authoring notes. Optional.
criteria:
  - name: central_claim
    description: The formulation names a central claim, objective, or problem.
    weight: 1.0                  # default 1.0
    scoring: graded_5            # "binary" | "graded_3" | "graded_5"; default graded_5
    rationale_required: true     # default true; judge must include a rationale
  - name: assumption_surfacing
    description: Load-bearing assumptions are made explicit.
  - name: ...
```

## Target axis

A rubric's `target` selects what the judge scores:

- **`formulation`** — judges score the formulation directly. Category-agnostic; works on questions, arguments, decisions, dilemmas. This is the "Path B" lens described in [`docs/designs/problemform_scope.md`](../../docs/designs/problemform_scope.md).
- **`artifact`** — judges score the downstream answer. Category-coupled (today: question-shaped inputs only). Complements M3A's comparative-answer judgment with per-criterion signal.

Different rubrics may share a `target` value; the framework runs each rubric independently and reports their results side by side.

## Mode

M3B-α ships **absolute mode only**: each rubric scores each subject (raw and refined) on its own merits, and the engine reports per-rubric aggregates plus a raw-vs-refined delta.

Comparative mode (head-to-head judging within a rubric) is deferred to M3B-β; the schema reserves the `mode` field so comparative rubrics can be added without a schema break.

## Default rubrics (planned, not yet shipped)

M3B-α.2 will ship two default rubrics here:

- `formulation_quality_v1.yaml` — `target=formulation, mode=absolute`. Seed rubric for the formulation lens.
- `answer_quality_v1.yaml` — `target=artifact, mode=absolute`. Per-criterion answer scoring parallel to M3A's comparative-answer judgment.

This directory is intentionally empty in M3B-α.1; the schema and loader land before the data.

## Authoring guidance

- **Use input-agnostic criterion language.** Prefer "the formulation," "the central claim," "the assumptions" over "the question" or "the answerer." Criteria that bake in question vocabulary won't generalize when the corpus diversifies.
- **Keep descriptions short and operational.** A criterion description should be something a judge model can score without further interpretation.
- **Bump `schema_version` when fields are added or semantics change.** Existing rubrics should remain valid against old loaders for at least one minor version.
