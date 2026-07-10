---
title: "M3B-β.1 implementation plan: formulation-type policy registry + answer-lens gating"
document_type: "plan"
status: "approved"
created: "2026-07-10"
updated: "2026-07-10"
author: "Claude Code"
authoritative_reference: "docs/designs/m3b_beta_corpus_diversification.md"
related:
  documents:
    - "docs/designs/m3b_beta_corpus_diversification.md"
    - "docs/plans/m3b_beta_0_plan_by_claude.md"
    - "docs/reports/m3b_alpha_validation_2026-07-08.md"
  issues:
    - 6
scope:
  inspected:
    - "problemform/eval/models.py"
    - "problemform/eval/engine.py"
    - "problemform/eval/report.py"
    - "problemform/cli.py (benchmark)"
    - "problemform/eval/defaults.py"
---

# M3B-β.1 implementation plan: policy registry + answer-lens gating

**Status: approved** (two Codex review rounds + user revisions). The first β phase
that *consumes* `formulation_type`: a **type→evaluation-policy registry** that gates
the M3A answer-comparison lens. A **deliberate behavior change**, scoped so it affects
only cases typed as formulation-only; answerable and `unspecified`/legacy cases behave
exactly as today.

## Answerable policy (authoritative)

**Criterion:** a type is *answerable* when the refinement naturally induces a
downstream response/artifact **whose quality we care about**.

- **Answerable (answer lens ON):** `question`, `explanation`, `instruction`, `prompt`, `specification`.
- **Formulation-only (answer lens OFF):** `argument`, `belief`, `decision`, `dilemma`, `goal`, `plan`.
- **`unspecified` / unknown → answerable** (legacy/back-compat).
- Overridable per run via CLI. Supersedes earlier design-doc wording; reconciled there
  in β.1.2 (see *Design-doc reconciliation*).

## Design

### `problemform/eval/policy.py` — formulation-type policy registry
Extensible abstraction (β.2+ grows the *policy*, not the registry):
- `@dataclass(frozen=True) class FormulationPolicy` — immutable per-type policy; β.1
  field `answer_comparison: bool = True`; later fields (default rubrics/suites) add
  with defaults.
- `FORMULATION_POLICIES: dict[str, FormulationPolicy]` — explicit entry for **every**
  `CANONICAL_FORMULATION_TYPES` member (test asserts full coverage).
- `DEFAULT_POLICY = FormulationPolicy()` (answer_comparison=True) for `unspecified`/unknown.
- `policy_for(formulation_type) -> FormulationPolicy`;
  `answer_comparison_applies(formulation_type, *, override: bool | None = None)` —
  override wins, else `policy_for(type).answer_comparison`.
- Module comment records the criterion for consistent future classification.

### Model
- `TestCaseResult.answer_comparison_applicable: bool = True` (defaulted → pre-β.1
  `report.json` parses unchanged).
- `AggregateMetrics.n_answer_skipped: int = 0` (explicit default, additive).

### Engine
`_run_one_case` gains the resolved policy; when not applicable it skips raw/refined
answer generation + the comparative judge entirely, leaves answers `""` /
`judgment=None`, sets `answer_comparison_applicable=False`. It **still** runs the PF
pipeline + rubric/property lenses and **still records PF/rubric/property failures in
`errors[]`**. `answer_provider: LLMProvider | None`; a skipped case never touches it.
`run_benchmark` threads `answer_comparison_override: bool | None` and validates early
(see guard).

### Aggregate — three mutually-exclusive answer-lens buckets (preserves α.4)
- `n_completed` = applicable **and** comparative judgment present.
- `n_errored` = applicable **and** judgment did **not** complete (answer-lens error).
- `n_answer_skipped` = not applicable by policy.
- `n_cases = n_completed + n_errored + n_answer_skipped`.

Buckets are decided by **answer-lens status only**; `errors[]` (PF/rubric/property)
never moves a case between them. An *applicable, completed* case with a rubric failure
stays `n_completed` (**exactly the α.4 contract**); a *skipped* case with a PF/rubric
failure stays `n_answer_skipped`; both carry their errors visibly. Rates over
`n_completed`. When every case is applicable (legacy), this reduces to α.4 identically.
Full per-lens error accounting stays deferred.

### Skipped-vs-errored semantics
`answer_comparison_applicable=False` means **only** the M3A lens was intentionally not
run; it does not move the aggregate bucket and does not imply the case is clean. A
skipped case's PF/rubric/property failures remain in `errors[]`, the Errors section,
`case_errored` progress, and the per-case row — a skipped-but-errored case is never
rendered as simply clean.

### Report
Distinguish three states — (a) skipped by policy, (b) answer-comparison failure
(applicable, judge/answer errored), (c) non-M3A lens errors. Headline annotates the
neutral **"Answer comparison skipped: N"** (not "by type" — a CLI override can also
skip answerable types); when `n_completed == 0`, degrade gracefully (M3A rows "n/a",
lead with the formulation-rubric section). Where practical, config/report records
*why* the lens was off (per-type policy vs CLI override). Sample line includes the
skipped count.

**Per-case rendering** (existing Winner/Materiality columns; they reflect the M3A
answer-lens view — PF/rubric/property errors surface in the Errors section):

| Case state | Winner | Materiality |
|---|---|---|
| Skipped, clean | `skipped` | `—` |
| Skipped, with non-M3A errors | `skipped` | `errored` |
| Applicable, answer comparison failed | `—` | `errored` |
| Applicable, completed + rubric/property error | *winner_actual* | *materiality* |

The last row preserves α.4 (verdict renders normally; the lens error appears only in
the Errors section).

### CLI
Exact nullable slash option on `benchmark`:
```python
answer_comparison: bool | None = typer.Option(
    None, "--answer-comparison/--no-answer-comparison",
    help="Force the M3A answer-comparison lens on/off (default: per-type policy).",
)
```
forwarded as `answer_comparison_override`. Plus **lazy answer-provider construction**:
- After loading cases, `will_run_answer_lens = any(answer_comparison_applies(c.formulation_type, override=answer_comparison) for c in cases)`.
- If `False` (e.g. `--no-answer-comparison`, or a wholly formulation-only corpus): do
  not construct the answer provider (`None`); do not emit the same-family warning; set
  config `answer_provider`/`answer_model` = `"not_used"`.
- If `True`: construct as today; per-case gating skips it for non-answerable cases.

### Direct-API guard
`run_benchmark` validates up front: if `answer_provider is None` **and** ≥1 case
resolves to answer-applicable, raise a clear `ValueError` immediately (not a deep
`AttributeError`).

### Design-doc reconciliation
As part of β.1.2, add a dated amendment to
`docs/designs/m3b_beta_corpus_diversification.md` recording the authoritative
answerable/formulation-only policy (resolving that doc's open question #4), so
design ↔ plan ↔ code agree. Doc amendment only, no design change.

## Phases

- **β.1.1 — policy registry + inert model/aggregate fields.** `policy.py`;
  `answer_comparison_applicable` (default True) + `n_answer_skipped` (default 0). Tests:
  resolver (answerable set, override precedence, unknown→True) + **canonical coverage**.
  Not yet consumed → **zero behavior change**.
- **β.1.2 — gating + aggregation + report + CLI + doc amendment (behavior change).**
  Engine gating; `run_benchmark` override + `LLMProvider | None` + early guard;
  `_aggregate` three-bucket; report skipped/degraded + per-case matrix + neutral
  wording + `"not_used"` config; CLI nullable flag + lazy construction; design-doc
  amendment. (β.1.2/3 combined so no intermediate commit ships engine skips without
  report support.)

## Verification

- **Semantic regression (answerable unchanged):** stub benchmark over
  `benchmarks/default` before/after. Because β.1 adds `answer_comparison_applicable`
  and `n_answer_skipped`, verify **semantic** invariance (not byte equality):
  provider/judge **call counts**, comparative judgments, all rates/aggregates, and
  answer artifacts unchanged; the only diffs are the additive metadata
  (`answer_comparison_applicable=True`, `n_answer_skipped=0`).
- **New behavior:** formulation-only suite (e.g. `benchmarks/decisions`) — headline
  degrades, `n_answer_skipped > 0`.
- **Override:** `--no-answer-comparison` skips even questions; `--answer-comparison`
  forces even formulation-only; omitted = policy. Test all three.
- **Gating assertions (stub):** skipped case → no answer-provider calls, no
  comparative-judge calls, no `raw_answer.txt`/`refined_answer.txt`, `judgment is None`,
  `answer_comparison_applicable is False`, formulation rubric still runs,
  artifact-target rubrics/properties skip empty subjects, skipped progress distinct
  from errored.
- **α.4 preserved:** applicable+completed case with a rubric error stays `n_completed`,
  renders normal Winner/Materiality, error in Errors section.
- **Skipped-with-errors:** stays in `n_answer_skipped`, yet appears in Errors,
  emits `case_errored`, per-case Materiality `errored`.
- **Config + guard:** no-provider run → config `"not_used"`;
  `run_benchmark(answer_provider=None)` with ≥1 applicable case → early `ValueError`.
- **Coverage:** every `CANONICAL_FORMULATION_TYPES` member has a registry entry.
- `pytest -q` green.

## Out of scope

Per-type default rubric/property selection (β.2); comparative-mode rubrics (β.3);
`category` retirement; prompt→formulation renames; `default/`→`questions/`. β.1 gates
the answer lens only.
