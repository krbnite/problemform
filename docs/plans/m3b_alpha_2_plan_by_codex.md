---
title: "M3B-α.2 implementation plan"
document_type: "plan"
status: "superseded"
created: "2026-06-05"
updated: "2026-07-08"
author: "Codex"
related:
  documents:
    - "docs/designs/milestone_03b_rubrics_and_properties.md"
  issues:
    - 12
---

# M3B-alpha.2 Implementation Plan

**Status: superseded — M3B-α.2 shipped (commit `9d74891`); retained as historical planning record.**

## Objective

M3B-alpha.2 should be a data-files-only patch that ships default rubric definitions and one small shared property suite, plus parse-only tests and minimal updates to the existing benchmark scaffolding READMEs.

It should not add runner behavior, prompt templates, CLI flags, aggregation/report rendering, API calls, benchmark execution, or model/schema changes unless the current M3B-alpha.1 schema cannot parse the intended data.

## Current M3B-alpha.1 Baseline

Latest relevant commit observed:

- `19ac2ff feat(eval): add rubric and property-check data model (M3B-alpha.1)`

Relevant alpha.1 model and loader state:

- `problemform/eval/models.py` defines `Rubric`, `RubricCriterion`, `PropertyCheck`, evaluation-result models, and aggregate models.
- `problemform/eval/corpus.py` defines `load_rubrics(path)` and `load_property_suite(path)`.
- `benchmarks/rubrics/README.md` and `benchmarks/properties/README.md` exist as scaffolding.
- No default rubric YAML files or property-suite YAML files are currently shipped under `benchmarks/rubrics/` or `benchmarks/properties/`.

## Existing Schema Fields

### `Rubric`

Required by the current schema:

- `name: str`
- `description: str`
- `target: Literal["formulation", "artifact"]`
- `mode: Literal["absolute", "comparative"]`
- `criteria: list[RubricCriterion]`

Optional/defaulted:

- `notes: str | None = None`
- `schema_version: int = 1`

Alpha.2 data should use `mode: absolute` only, even though the schema reserves `comparative` for later phases.

### `RubricCriterion`

Required by the current schema:

- `name: str`
- `description: str`

Optional/defaulted:

- `weight: float = 1.0`
- `scoring: Literal["binary", "graded_3", "graded_5"] = "graded_5"`
- `rationale_required: bool = True`

Alpha.2 data should explicitly set `weight: 1.0` and `scoring: graded_5` for every criterion. It does not need to set `rationale_required` because the alpha.1 default is already `true`.

### `PropertyCheck`

Required by the current schema:

- `name: str`
- `description: str`
- `target: Literal["formulation", "artifact"]`

Optional/defaulted:

- `expected: bool = True`

Alpha.2 shared properties should explicitly set `target: artifact` and `expected: true` for every property.

## Schema Compatibility Finding

The intended alpha.2 data can be parsed by the current alpha.1 schema and loaders.

No Python model or loader changes appear necessary for alpha.2 if the property suite uses either:

- a bare top-level list of property dicts, or
- a top-level mapping with `properties: [...]`.

Recommended alpha.2 choice: use the bare-list property-suite shape to avoid adding suite metadata, grouping semantics, or any implication that the loader should preserve suite identity.

No stop condition is triggered.

## Proposed YAML Shapes

### `benchmarks/rubrics/formulation_quality_v1.yaml`

```yaml
name: formulation_quality_v1
description: |
  Default absolute rubric for evaluating formulation quality across question-shaped
  and non-question-shaped inputs.
target: formulation
mode: absolute
schema_version: 1
criteria:
  - name: central_claim_clarity
    description: The formulation clearly states the central claim, objective, decision, or problem to be worked on.
    weight: 1.0
    scoring: graded_5
  - name: assumption_surfacing
    description: The formulation makes load-bearing assumptions explicit enough that they can be inspected or revised.
    weight: 1.0
    scoring: graded_5
  - name: constraint_articulation
    description: The formulation identifies relevant constraints, success criteria, or boundaries for the work.
    weight: 1.0
    scoring: graded_5
  - name: alternative_framing_coverage
    description: The formulation surfaces plausible alternative ways to frame the problem without losing the user's intent.
    weight: 1.0
    scoring: graded_5
  - name: meta_question_presence
    description: The formulation includes an appropriate higher-order question about what needs to be clarified, decided, or tested.
    weight: 1.0
    scoring: graded_5
```

Notes:

- Criterion names are canonical snake_case names derived from the five design-doc criteria.
- Descriptions are one-sentence and operational enough for later judge prompting.
- The language avoids "the question" so this rubric can serve the broader formulation target.

### `benchmarks/rubrics/answer_quality_v1.yaml`

```yaml
name: answer_quality_v1
description: |
  Default absolute rubric for evaluating the quality of a downstream answer or
  artifact produced from a formulation.
target: artifact
mode: absolute
schema_version: 1
criteria:
  - name: directness
    description: The artifact directly addresses the user's stated request before adding secondary context.
    weight: 1.0
    scoring: graded_5
  - name: factual_care
    description: The artifact distinguishes known facts from uncertainty and avoids overstating claims beyond the available context.
    weight: 1.0
    scoring: graded_5
  - name: reasoning_quality
    description: The artifact explains its reasoning or decision basis clearly enough for the user to evaluate the answer.
    weight: 1.0
    scoring: graded_5
  - name: constraint_satisfaction
    description: The artifact respects explicit constraints from the user's request, such as scope, format, audience, and exclusions.
    weight: 1.0
    scoring: graded_5
  - name: usefulness
    description: The artifact provides actionable, relevant, and appropriately complete help for the user's task.
    weight: 1.0
    scoring: graded_5
```

Notes:

- `factual_care` is deliberately narrower than a broad "factually accurate" property. It evaluates care, calibration, and overclaiming against available context rather than requiring external fact verification.
- The file is still artifact-targeted, not formulation-targeted, and should not be treated as validating Path B by itself.

### `benchmarks/properties/artifact_baseline_v1.yaml`

```yaml
- name: addresses_stated_request
  description: The artifact responds to the user's stated request or input intent rather than substituting a different task.
  target: artifact
  expected: true
- name: no_unnecessary_refusal
  description: The artifact does not refuse or decline the task when the request appears answerable within policy and available context.
  target: artifact
  expected: true
- name: no_obvious_unsupported_facts
  description: The artifact does not present obvious unsupported assumptions as established facts.
  target: artifact
  expected: true
- name: respectful_tone
  description: The artifact avoids condescending, hostile, or needlessly adversarial tone.
  target: artifact
  expected: true
```

Notes:

- This uses the bare-list shape accepted by `load_property_suite`.
- The file name uses `artifact`, not `answer`, to stay aligned with the schema's target language.
- There is no `suite_name`, `schema_version`, grouping field, or other suite metadata.
- The suite avoids a broad "factually accurate" property.

## Tests To Add Later

Add parse-only tests to `tests/test_eval_corpus.py`. These should not call any runner, judge, CLI, API, or benchmark execution code.

Proposed constants:

```python
DEFAULT_RUBRICS = Path(__file__).parent.parent / "benchmarks" / "rubrics"
DEFAULT_PROPERTIES = Path(__file__).parent.parent / "benchmarks" / "properties"
```

Proposed tests:

1. `test_default_rubrics_parse_from_directory`
   - Call `load_rubrics(DEFAULT_RUBRICS)`.
   - Assert the loaded rubric names are exactly or at least:
     - `formulation_quality_v1`
     - `answer_quality_v1`
   - Assert `formulation_quality_v1.target == "formulation"` and `mode == "absolute"`.
   - Assert `answer_quality_v1.target == "artifact"` and `mode == "absolute"`.
   - Assert both rubrics have five criteria.
   - Assert every criterion has `scoring == "graded_5"` and `weight == 1.0`.

2. `test_default_rubrics_parse_from_file_paths`
   - Call `load_rubrics(DEFAULT_RUBRICS / "formulation_quality_v1.yaml")`.
   - Call `load_rubrics(DEFAULT_RUBRICS / "answer_quality_v1.yaml")`.
   - Assert each direct file path returns one rubric with the expected name.

3. `test_default_formulation_rubric_uses_canonical_criteria`
   - Load `formulation_quality_v1.yaml`.
   - Assert criterion names in order:
     - `central_claim_clarity`
     - `assumption_surfacing`
     - `constraint_articulation`
     - `alternative_framing_coverage`
     - `meta_question_presence`

4. `test_default_answer_rubric_uses_expected_criteria`
   - Load `answer_quality_v1.yaml`.
   - Assert criterion names in order:
     - `directness`
     - `factual_care`
     - `reasoning_quality`
     - `constraint_satisfaction`
     - `usefulness`

5. `test_default_property_suite_parses_from_directory`
   - Call `load_property_suite(DEFAULT_PROPERTIES)`.
   - Assert the expected property names are present:
     - `addresses_stated_request`
     - `no_unnecessary_refusal`
     - `no_obvious_unsupported_facts`
     - `respectful_tone`
   - Assert every loaded default property has `target == "artifact"` and `expected is True`.

6. `test_default_property_suite_parses_from_file_path`
   - Call `load_property_suite(DEFAULT_PROPERTIES / "artifact_baseline_v1.yaml")`.
   - Assert it returns four properties.
   - Assert every property has `target == "artifact"` and `expected is True`.

These tests cover both directory and explicit file-path loader behavior where cheap, matching the alpha.1 loader capabilities.

## Minimal README Updates For Eventual Implementation

Only update the scaffolding READMEs if needed:

- `benchmarks/rubrics/README.md`
- `benchmarks/properties/README.md`

Do not update the top-level README unless the implementation reveals a strict need.

Recommended README adjustments:

1. `benchmarks/rubrics/README.md`
   - Change "Default rubrics (planned, not yet shipped)" to reflect that alpha.2 ships the two YAML files.
   - Update the example criterion name from `central_claim` to `central_claim_clarity` to match the shipped formulation rubric.
   - Keep language clear that these are definitions only until runner/report integration lands in later alpha steps.

2. `benchmarks/properties/README.md`
   - Remove or revise language implying M3B-alpha.2 activates `TestCase.expected_properties`, adds `--property-suite`, or runs property checks.
   - State that alpha.2 only ships parseable shared property definitions.
   - State that runner activation, CLI flags, and aggregation/reporting remain deferred to later alpha steps.

## Ambiguities And Non-Blocking Mismatches

1. Existing design-doc default answer criteria differ from the intended alpha.2 criteria.
   - Design doc names: addresses-input-intent, factual accuracy, actionability, calibrated confidence, proportionate length.
   - Intended alpha.2 names: directness, factual_care, reasoning_quality, constraint_satisfaction, usefulness.
   - This is not a schema mismatch. It is a product/content choice. The intended alpha.2 criteria are reasonable as a smaller, less externally factual artifact-quality baseline.

2. Existing `benchmarks/properties/README.md` mentions alpha activation of per-case `expected_properties` and a `--property-suite` CLI flag.
   - Under the refined alpha.2 staircase, those are no longer alpha.2 work.
   - This is documentation drift, not a schema issue.
   - Fix only the scaffolding README text in the eventual alpha.2 patch.

3. `load_property_suite` discards suite identity.
   - This is compatible with alpha.2 because the requested property suite should not add suite metadata or grouping semantics.
   - Do not change the return type in alpha.2.

4. `RubricMode` allows `comparative`.
   - Alpha.2 should ship only `mode: absolute`.
   - No model change is needed.

5. The schema does not enforce non-empty criteria or unique criterion names.
   - The shipped YAML and parse tests should enforce the intended two five-criterion rubrics.
   - Do not add schema validators in alpha.2 unless a real parse blocker appears.

## Can Alpha.2 Be Implemented Without Python Model/Loader Changes?

Yes.

The proposed YAML shapes fit the alpha.1 `Rubric`, `RubricCriterion`, and `PropertyCheck` models and the alpha.1 `load_rubrics` / `load_property_suite` loaders.

No source-code changes are needed for models, loaders, runners, engine integration, CLI, report rendering, or prompt generation.

## Proposed File List For Eventual Alpha.2 Implementation

Files to add:

- `benchmarks/rubrics/formulation_quality_v1.yaml`
- `benchmarks/rubrics/answer_quality_v1.yaml`
- `benchmarks/properties/artifact_baseline_v1.yaml`

Files to modify:

- `tests/test_eval_corpus.py`
- `benchmarks/rubrics/README.md`
- `benchmarks/properties/README.md`

Files not to modify:

- `problemform/eval/models.py`
- `problemform/eval/corpus.py`
- `problemform/eval/engine.py`
- `problemform/eval/report.py`
- `problemform/cli.py`
- top-level `README.md`, unless a strict need is discovered

## Alpha.2 Hard Exclusions

- No runner integration.
- No prompt templates.
- No CLI flags.
- No aggregation or report rendering.
- No API calls.
- No benchmark execution.
- No activation of `TestCase.expected_properties`.
- No per-case `formulation_properties`.
- No suite metadata, grouping semantics, or loader return-type changes.
- No model/schema changes unless the current alpha.1 schema cannot parse the intended data.

## Recommended Commit Shape

One small eventual implementation commit:

`feat(eval): ship default M3B-alpha.2 rubric and property data`

The commit should contain only the three YAML data files, parse-only loader tests, and minimal scaffolding README updates.
