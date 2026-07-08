# Property suites

Each YAML file under this directory is a **property suite** — a collection of binary assertions about a formulation or an artifact, evaluated by an LLM judge. Property checks are *regression-shaped*: they codify "this should always be true" (or "always be false") rather than measuring graded quality. For graded scoring, see [`benchmarks/rubrics/`](../rubrics/).

See [`docs/designs/milestone_03b_rubrics_and_properties.md`](../../docs/designs/milestone_03b_rubrics_and_properties.md) for the design rationale and how property checks compose with M3A's comparative-answer judgment and M3B's rubric framework.

## File shape

The loader (`problemform.eval.corpus.load_property_suite`) accepts either a single YAML file or a directory walked recursively. Each file may take either of two shapes:

**Keyed-suite form.** A mapping with a top-level `properties` list. Other top-level keys (e.g. `suite_name`) are ignored:

```yaml
suite_name: answer_quality_baseline
properties:
  - name: addresses_audience
    description: The answer addresses the intended audience.
    target: artifact          # "formulation" | "artifact"
    expected: true            # default true
  - name: factually_accurate
    description: The answer is factually accurate.
    target: artifact
```

**Bare-list form.** Top-level is a list of property dicts:

```yaml
- name: surfaces_central_claim
  description: The formulation names a central claim.
  target: formulation
- name: no_hidden_assumption
  description: No load-bearing assumption is left implicit.
  target: formulation
```

Both forms produce a flat `list[PropertyCheck]`; directories aggregate every file's properties in path-sorted order.

## Target axis

- **`target: artifact`** — the property is asserted about a downstream answer. The shipped [`artifact_baseline_v1.yaml`](artifact_baseline_v1.yaml) suite is the reference example.
- **`target: formulation`** — the property is asserted about the formulation itself. Category-agnostic; usable on non-question inputs once corpus diversification (M3B-β) lands. Since **M3B-α.4**, each case's `TestCase.expected_properties` strings activate as `target=formulation` checks (see below).

## Expected polarity

`expected: true` (the default) asserts the property *holds*. `expected: false` asserts it *fails to hold* — useful for "the refined formulation should NOT introduce X."

A `PropertyCheckResult` records:

- `holds: bool` — the judge's verdict on whether the property actually holds.
- `expected: bool` — what the property's `expected` field said.
- `passed: bool` — `holds == expected`. The pass-rate aggregate uses `passed`.

## Per-case vs shared properties

M3B-α property checks come from two sources:

1. **Per-case `TestCase.expected_properties`** (existing field). Since **M3B-α.4** each string activates as a `target=formulation, expected=True` property check applied only to its case, evaluated against that case's raw and refined formulation. (The original design intended `target=artifact`; a corpus review found the shipped strings are predominantly formulation-shaped — see the "Activation of `TestCase.expected_properties`" amendment in [the design doc](../../docs/designs/milestone_03b_rubrics_and_properties.md). Artifact-target coverage is retained by shared suites like `artifact_baseline_v1`.)
2. **Shared suites under this directory**, applied across cases. The shipped seed suite is [`artifact_baseline_v1.yaml`](artifact_baseline_v1.yaml). The repeatable `--property-suite <path>` CLI flag selects suites at run time (M3B-α.4); with no flag, this directory is default-loaded.

Per-case formulation-target properties — i.e. a `formulation_properties` field on `TestCase` — are deferred to M3B-β corpus diversification. Until then, formulation-target assertions belong in shared suites here.

## Shipped in M3B-α.2

- [`artifact_baseline_v1.yaml`](artifact_baseline_v1.yaml) — four baseline artifact-target binary assertions (`addresses_stated_request`, `no_unnecessary_refusal`, `no_obvious_unsupported_facts`, `respectful_tone`).

This suite shipped as data in α.2. Property-check execution (running these against a subject via an LLM judge) landed in **M3B-α.3** along with the rubric runner; engine integration, aggregation, reporting, and the `--property-suite` CLI flag landed in **M3B-α.4**. Loader tests live in [`tests/test_eval_corpus.py`](../../tests/test_eval_corpus.py); runner and integration tests in `tests/test_eval_property_runner.py`, `tests/test_eval_engine.py`, and `tests/test_eval_cli.py`.
