---
title: "M3B-β.0 implementation plan: formulation-type vocabulary (inert foundation)"
document_type: "plan"
status: "proposed"
created: "2026-07-09"
updated: "2026-07-09"
author: "Claude Code"
authoritative_reference: "docs/designs/m3b_beta_corpus_diversification.md"
related:
  documents:
    - "docs/designs/m3b_beta_corpus_diversification.md"
    - "docs/designs/milestone_03b_rubrics_and_properties.md"
    - "docs/reports/m3b_alpha_validation_2026-07-08.md"
    - "docs/plans/claudes-m3b-alpha-implementation-plan.md"
  issues:
    - 6
scope:
  inspected:
    - "problemform/eval/models.py"
    - "problemform/eval/engine.py / report.py / cli.py / defaults.py"
    - "benchmarks/ (11 type dirs + simple/)"
    - "benchmarks/README.md"
---

# M3B-β.0 implementation plan: formulation-type vocabulary

**Status: proposed.** Smallest coherent slice of the approved β design
([`m3b_beta_corpus_diversification.md`](../designs/m3b_beta_corpus_diversification.md)).
It lands the load-bearing architectural primitive — every benchmark case becomes
**typed** — as **inert metadata that nothing consumes yet**, so runtime behavior is
unchanged. The registry, answer-lens gating, and reporting changes that *consume*
this field are held to β.1+.

## Goal and non-goal

- **Goal:** make `formulation_type` a first-class, populated field on every corpus
  case, and document the type-vs-category distinction.
- **Non-goal / hard boundary — zero behavior change.** The engine, report, CLI,
  judging, rubric/property lenses, default loading, and every metric stay
  byte-for-byte identical. The only observable difference is an **additive**
  `test_case.formulation_type` field in `report.json`.

Ratified from the design doc's open questions: the vocabulary is **open** — a `str`
field plus a canonical known-set; unknown values are allowed and will fall back to a
generic policy in β.1. Not a closed `Literal`.

## Phases (α.1–α.4 style: small, independently reviewable patches)

### β.0.1 — Data model: the `formulation_type` field + canonical set

**Files**
- `problemform/eval/models.py`
  - Add `formulation_type: str = "unspecified"` to `TestCase`. Defaulted so pre-β
    `report.json` and any user case lacking the field still deserialize cleanly —
    the exact back-compat pattern α.1 used for the defaulted `rubric_evaluations` /
    `property_check_results`. The neutral `"unspecified"` default is deliberate: do
    **not** assume `"question"`.
  - Add a module-level `CANONICAL_FORMULATION_TYPES: frozenset[str]` = `{question,
    argument, belief, decision, dilemma, explanation, goal, instruction, plan,
    prompt, specification}`. Reference vocabulary only in β.0; the β.1 registry keys
    off it. (Lives in `models.py` for now; β.1 may relocate it to an
    `eval/policy.py`.)
  - One-line note in the `TestCase` docstring describing the field.
- `tests/test_eval_models.py`
  - Round-trip with `formulation_type`; the defaulted value when omitted; a legacy
    `TestCase` dict without the field parses to `"unspecified"`;
    `CANONICAL_FORMULATION_TYPES` contents.

**Do NOT**
- **No `schema_version` bump.** The field already exists and the α.1 precedent added
  defaulted fields *without* bumping it; follow that pattern. Do not introduce any
  schema-version handling/machinery for β.0.
- No engine/report/CLI/registry consumption. The field is inert.

### β.0.2 — Corpus backfill + docs + minimal name hygiene

**Files (data & docs only)**
- **Backfill** `formulation_type:` on every shipped corpus case, matching its
  directory: `default/*` → `question`; `arguments/` → `argument`; `beliefs/` →
  `belief`; `decisions/` → `decision`; `dilemmas/` → `dilemma`; `explanations/` →
  `explanation`; `goals/` → `goal`; `instructions/` → `instruction`; `plans/` →
  `plan`; `prompts/` → `prompt`; `specifications/` → `specification`; `simple/` →
  `question`.
- `benchmarks/README.md`: document `formulation_type` as the **type axis**; fix the
  schema example + prose that still says "the user's original **question**" to
  type-neutral wording; clarify that `category` is an **organizational/topic** label,
  not the type. Do **not** change `category` values or how it is consumed.
- **Minimal dedupe:** rename only the single needed duplicate — `what_should_i_do_tomorrow`
  exists in both `decisions/` and `dilemmas/`; rename the one file/case (keep the
  version that best fits its type; give the other a distinct name). No broader corpus
  reorganization. Leave `cosmology_nothingness` (`default/` + `simple/`) as-is —
  `simple/` is a scratch suite unlikely to be co-run.

**Still zero behavior change** — `formulation_type` remains unconsumed.

## Explicitly deferred (NOT in β.0)

| Deferred item | Phase | Why not β.0 |
|---|---|---|
| Type→policy registry + **answer-lens gating** | β.1 | Consumes `formulation_type`; changes behavior (skips M3A answer comparison for non-answerable types) |
| Type-aware default rubric/property selection | β.2 | Behavior change |
| Comparative-mode rubrics | β.3 | New lens |
| `category` retirement/repurposing | later | `report.py` consumes `category`; behavior/schema change |
| prompt→formulation eval renames (`raw_prompt`/`refined_prompt`) | later | Changes `report.json` schema |
| `benchmarks/default/` → `questions/` rename | later | Touches tests, README, roadmap, H1-report refs |
| Core `ProblemState` prompt→formulation | separate migration | Cross-cutting |

## Reused patterns / anchors

- **Defaulted-field back-compat:** α.1's `models.py` additions
  (`rubric_evaluations` / `property_check_results` default to empty so old
  `report.json` still parses) — mirror it for `formulation_type`.
- **Config-as-data constant:** `CANONICAL_FORMULATION_TYPES` follows the `defaults.py` /
  `PHASE_DEFAULT_TEMPERATURES` style.
- **Corpus authoring:** the existing β YAML files are the template for the key.

## Verification

- `pytest -q` green (new model tests; nothing else changes).
- Load every suite and assert each case's `formulation_type` is set and in
  `CANONICAL_FORMULATION_TYPES`.
- **Prove zero behavior change (static):** `grep -rn "formulation_type"` shows
  references only in `models.py`, the corpus YAML, and tests — *not* in `engine.py`,
  `report.py`, `cli.py`, `defaults.py`, or the runners.
- **Behavioral regression check (required, dynamic).** Run a representative benchmark
  with the deterministic stub providers (`tests/test_eval_engine._PFStub` /
  `_AnswerStub` / `_JudgeStub`) over a representative corpus (`benchmarks/default`)
  on **pre-β.0** code → *baseline*, then again **after** β.0 → *after*. Deterministic
  stubs are used precisely so LLM nondeterminism cannot mask the comparison. After
  normalizing out the inherently nondeterministic fields (`run_id`,
  `started_at`/`finished_at`, `aggregate_runtime`, per-case `timing`), assert the two
  `report.json` payloads are **identical except** for the additive
  `test_case.formulation_type` field — every headline metric, every aggregate (M3A /
  rubrics / properties), and every report section byte-identical. Also diff the
  rendered `report.md` (minus the Runtime section): identical.

## Suggested commit boundaries

Two commits mirroring the phases: (1) `feat(eval): add TestCase.formulation_type +
CANONICAL_FORMULATION_TYPES (M3B-β.0.1)`; (2) `chore(corpus): backfill formulation_type
+ type/category docs + dedupe (M3B-β.0.2)`.
