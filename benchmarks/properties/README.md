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

- **`target: artifact`** — the property is asserted about a downstream answer. Today this covers the `TestCase.expected_properties` strings that ship with the M3A corpus (M3B-α.2 will activate these as runnable assertions).
- **`target: formulation`** — the property is asserted about the formulation itself. Category-agnostic; usable on non-question inputs once corpus diversification (M3B-β) lands.

## Expected polarity

`expected: true` (the default) asserts the property *holds*. `expected: false` asserts it *fails to hold* — useful for "the refined formulation should NOT introduce X."

A `PropertyCheckResult` records:

- `holds: bool` — the judge's verdict on whether the property actually holds.
- `expected: bool` — what the property's `expected` field said.
- `passed: bool` — `holds == expected`. The pass-rate aggregate uses `passed`.

## Per-case vs shared properties

M3B-α property checks come from two sources:

1. **Per-case `TestCase.expected_properties`** (existing field, activated in M3B-α.2). Each string is interpreted as a `target=artifact, expected=True` property check applied only to its case.
2. **Shared suites under this directory**, applied across cases via the `--property-suite <path>` CLI flag (lands in M3B-α.2).

Per-case formulation-target properties — i.e. a `formulation_properties` field on `TestCase` — are deferred to M3B-β corpus diversification. Until then, formulation-target assertions live in shared suites here.

This directory is intentionally empty in M3B-α.1; the schema and loader land before the data.
