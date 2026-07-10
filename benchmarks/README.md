# ProblemForm Benchmarks

This directory holds **user-maintained** evaluation test cases. The framework treats it as data, not library code — add, remove, organize, and annotate test cases as the project evolves.

See `docs/designs/milestone_03_evaluation_framework.md` for the full architecture and rationale.

## Layout

```
benchmarks/
  README.md                      # this file
  default/                       # default suite shipped with the project
    <category>/
      <case_name>.yaml           # one TestCase per file
```

Suites are organized by directory — the formulation-type dirs (`arguments/`, `decisions/`, `dilemmas/`, `goals/`, `plans/`, …) and the legacy `default/` question suite with topic subdirs (`philosophy/`, `practical/`, `control/`). The loader walks all `.yaml`/`.yml` files recursively, so the directory layout is for human convenience.

Two distinct axes live in each file:

- **`formulation_type`** — *what kind* of input this is (question, argument, decision, …; the canonical vocabulary is `CANONICAL_FORMULATION_TYPES` in `problemform/eval/models.py`). This is the axis the corpus is organized around.
- **`category`** — a free organizational/**topic** label used for reporting groupings. It is *not* the type (e.g. the legacy question cases use `philosophy`, `technical`, `control`).

## Test-case schema (Phase A)

```yaml
schema_version: 1
name: my_case_name
formulation_type: question   # what kind of input (question | argument | belief | decision | dilemma | explanation | goal | instruction | plan | prompt | specification)
category: philosophy          # free organizational/topic label — distinct from formulation_type
tags:
  - tag1
  - tag2
raw_formulation: >
  The user's original formulation, exactly as they would state it — a question,
  argument, decision, goal, and so on.
expected_properties:
  - things a good refined formulation (or answer) should do
expected_failure_modes:
  - things a bad refined formulation (or answer) should NOT do
notes: |
  Free-form notes explaining the intent of this case.
```

Field requirements:

- `name`, `category`, `raw_formulation`: required.
- `formulation_type`: optional but **recommended** — the canonical input type; defaults to `unspecified` when omitted. See the type list above.
- All other fields: optional; sensible defaults.
- `expected_properties` and `expected_failure_modes` are **stored but not evaluated** in Phase A. Phase B introduces property checks that consume these.

## The control case

The default suite includes `default/control/what_causes_eclipses.yaml`. This is a **structural guard**: a question where ProblemForm may not help (or may actively hurt). Including at least one such case in any suite prevents the benchmark from quietly becoming an advocacy artifact for ProblemForm.

When adding new suites, **include at least one control case** — a well-formed question where the right outcome may be "no change needed."

## Running a benchmark

```bash
problemform benchmark benchmarks/default \
    --pf-provider openai \
    --answer-provider openai \
    --judge-provider anthropic    # different family from answer, recommended
```

Run results land under `.problemform/eval_runs/<run-id>/` (gitignored). See `problemform benchmark --help` for all flags.
