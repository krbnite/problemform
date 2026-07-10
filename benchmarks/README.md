# ProblemForm Benchmarks

This directory holds **user-maintained** evaluation test cases. The framework treats it as data, not library code — add, remove, organize, and annotate test cases as the project evolves.

See `docs/designs/milestone_03_evaluation_framework.md` for the full architecture and rationale.

## Layout

```
benchmarks/
  README.md                      # this file
  cases/                         # the canonical benchmark corpus
    questions/                   # (topic subdirs: control/ parenting/ philosophy/ practical/ technical/)
    arguments/ beliefs/ decisions/ dilemmas/ explanations/
    goals/ instructions/ plans/ prompts/ specifications/
      <case_name>.yaml           # one TestCase per file
  rubrics/                       # rubric definitions (sibling resource, not a case suite)
  properties/                    # property suites (sibling resource, not a case suite)
  simple/                        # experimental scratch suite (not part of the canonical corpus)
```

`benchmarks/cases/` is the single canonical corpus root: `problemform benchmark benchmarks/cases` evaluates exactly the canonical cases. Its immediate subdirectories are the formulation-type suites (`questions/`, `arguments/`, `decisions/`, …). `rubrics/` and `properties/` are sibling resources — kept out of `cases/` so they are not mistaken for case suites — and `simple/` is an experimental scratch suite. The loader walks `.yaml`/`.yml` files recursively, so directory nesting inside a suite (e.g. `questions/philosophy/`) is for human convenience.

Two distinct axes live in each file:

- **`formulation_type`** — *what kind* of input this is (question, argument, decision, …; the canonical vocabulary is `CANONICAL_FORMULATION_TYPES` in `problemform/eval/models.py`). This is the axis the corpus is organized around.
- **`category`** — a free organizational/**topic** label used for reporting groupings. It is *not* the type (e.g. the legacy question cases use `philosophy`, `technical`, `control`).

## Test-case schema

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
- `formulation_type`: optional but **recommended** — the canonical input type; defaults to `unspecified` when omitted. See the type list above. Since M3B-β.1 it also governs whether the M3A **answer-comparison lens** runs for the case: answerable types (`question`, `explanation`, `instruction`, `prompt`, `specification`) generate answers and are judged; formulation-only types (`argument`, `belief`, `decision`, `dilemma`, `goal`, `plan`) skip the answer lens and are scored by the formulation rubric instead. See [`docs/cli_commands.md`](../docs/cli_commands.md).
- All other fields: optional; sensible defaults.
- `expected_properties`: **evaluated.** Since M3B-α.4 each string is activated as a `target=formulation`, `expected=True` **property check** run against the case's raw and refined formulation in every benchmark (formerly "stored but not evaluated"). See [`properties/README.md`](properties/README.md).
- `expected_failure_modes`: **stored, not yet evaluated** — reserved for a future failure-mode lens.

## The control case

The questions suite includes `cases/questions/control/what_causes_eclipses.yaml`. This is a **structural guard**: a question where ProblemForm may not help (or may actively hurt). Including at least one such case in any suite prevents the benchmark from quietly becoming an advocacy artifact for ProblemForm.

When adding new suites, **include at least one control case** — a well-formed question where the right outcome may be "no change needed."

## Running a benchmark

```bash
# whole canonical corpus (all formulation types)
problemform benchmark benchmarks/cases \
    --pf-provider openai \
    --answer-provider openai \
    --judge-provider anthropic    # different family from answer, recommended

# or a single type suite, e.g. just questions
problemform benchmark benchmarks/cases/questions --judge-provider anthropic
```

Run results land under `.problemform/eval_runs/<run-id>/` (gitignored). See `problemform benchmark --help` for all flags.
