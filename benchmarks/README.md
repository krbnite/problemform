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

Subdirectory names under a suite (e.g. `philosophy/`, `practical/`, `control/`) are organizational; the loader walks all `.yaml`/`.yml` files recursively. Use `category:` inside each file to drive reporting groupings — the directory layout is for human convenience.

## Test-case schema (Phase A)

```yaml
schema_version: 1
name: my_case_name
category: philosophy
tags:
  - tag1
  - tag2
raw_formulation: >
  The user's original question, exactly as they would ask it.
expected_properties:
  - things a good answer or refined prompt should do
expected_failure_modes:
  - things a bad answer should NOT do
notes: |
  Free-form notes explaining the intent of this case.
```

Field requirements:

- `name`, `category`, `raw_formulation`: required.
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
