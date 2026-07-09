---
title: "M3B-α.4 implementation plan: integration phase"
document_type: "plan"
status: "approved"
created: "2026-07-08"
updated: "2026-07-08"
author: "Claude Code"
authoritative_reference: "docs/designs/milestone_03b_rubrics_and_properties.md"
related:
  documents:
    - "docs/designs/milestone_03b_rubrics_and_properties.md"
    - "docs/designs/problemform_scope.md"
    - "docs/designs/milestone_03_evaluation_framework.md"
    - "claudes-m3b-alpha-implementation-plan.md"
  issues:
    - 12
scope:
  inspected:
    - "problemform/eval/models.py"
    - "problemform/eval/corpus.py"
    - "problemform/eval/engine.py"
    - "problemform/eval/report.py"
    - "problemform/eval/rubric_runner.py"
    - "problemform/eval/property_runner.py"
    - "problemform/eval/scoring.py"
    - "problemform/cli.py"
    - "benchmarks/rubrics/"
    - "benchmarks/properties/"
    - "benchmarks/default/"
    - "docs/designs/milestone_03b_rubrics_and_properties.md"
    - "GitHub issue #12"
---

# Plan: M3B-α.4 — Integration

**Status (original): proposed. Awaiting approval before code lands. One blocking
decision (item 4) requires the user's ruling.**

---

## Amendment log

> This document was never committed to git in its "proposed" state, so this
> in-document log — rather than git history — is the record of what changed
> after authoring. The original plan body below is preserved verbatim; changes
> are recorded here and cross-referenced inline with **[Amended …]** notes.

**2026-07-08 — Plan approved; item 4 resolved as option B.**
Resolved via an external review chain (all under `docs/plans/`):
`doc02` (ChatGPT approval) → `doc03` (Codex review) → `doc04` (ChatGPT final).
Front-matter `status` changed `proposed → approved` to reflect this.

- **Item 4 (the blocking decision): option B.** Activate
  `TestCase.expected_properties` as **`target=formulation`, `expected=True`**.
- **Careful phrasing of the deviation (per doc03/doc04):** the current corpus
  `expected_properties` are *predominantly* formulation-shaped, though a few are
  mixed or answer-readable (Codex flagged the control case
  `what_causes_eclipses` in particular). For α.4, formulation-target activation
  is the cleaner *default* because it produces coherent signal on the current
  corpus and aligns with the M3B bridge goal of first-class formulation
  evaluation. It is an implementation correction grounded in corpus reality, not
  a redesign.
- **Artifact coverage is not lost:** `artifact_baseline_v1` continues to provide
  genuine `target=artifact` property checks, default-loaded independently.
- **Deferred to the cleanup queue** (tracked in `docs/backlog.md`, not blocking
  α.4): (1) a design-doc amendment in
  `docs/designs/milestone_03b_rubrics_and_properties.md` (which still says
  `target=artifact` at its `expected_properties` activation section); (2) the
  stale `benchmarks/properties/README.md` language; (3) any backlog / property
  README wording that still implies `expected_properties` are artifact-target by
  default.

---

α.1, α.2, and α.3 are complete. α.4 is the integration phase: wire the existing
M3B pieces (runners, models, loaders, prompts, default YAMLs) into the benchmark
execution path while preserving the separation between the three lenses — M3A
comparative answer judgment, rubric evaluations, and property checks.

## Guiding constraint

α.4 is a **wiring** phase, not a design phase. The runners
(`rubric_runner.py`, `property_runner.py`), models
(`Rubric`, `PropertyCheck`, `AbsoluteRubricEvaluation`, `PropertyCheckResult`,
`RubricAggregate`, `PropertyAggregate`), loaders (`load_rubrics`,
`load_property_suite`), judge prompts, and default YAMLs already exist and are
unit-tested (α.1–α.3). α.4 connects them to `run_benchmark`, the report, and the
CLI, keeping the **three lenses parallel and never collapsed into one score**.

Recommended to land as **two commits** mirroring the α.1–α.3 discipline; tests
land with each:

- **α.4a** — engine integration + cross-case aggregation + `run_benchmark` /
  `_run_one_case` signature threading + engine/aggregation tests.
- **α.4b** — report sections + disagreement diagnostic + CLI flags +
  default-loading + report/CLI tests.

## Scope (from issue #12, restated)

In scope:

- Integrate rubric/property runners into `run_benchmark`.
- Populate `TestCaseResult.rubric_evaluations`.
- Populate `TestCaseResult.property_check_results`.
- Compute `aggregate_rubrics`.
- Compute `aggregate_properties`.
- Render rubric/property sections in `report.md`.
- Add disagreement diagnostics without collapsing metrics into one score.
- Add benchmark CLI flags `--rubric` and `--property-suite`.
- Default-load project rubrics/properties when no explicit flags are passed.
- Activate existing `TestCase.expected_properties` as property checks.
- Stub-driven tests only; no real API calls.

Out of scope: validation experiments; formulation-only benchmark mode;
comparative rubrics; corpus diversification; `TestCase.formulation_properties`;
changes to the refinement/convergence pipeline; any single combined score;
provider/token/cost work.

---

## 1. Default rubric/property loading

- Add a repo-root resolver (in the CLI, or a small `eval/defaults.py`):
  repo root computed from `Path(__file__).resolve().parents[N]`, then
  `DEFAULT_RUBRICS_DIR = <repo>/benchmarks/rubrics` and
  `DEFAULT_PROPERTIES_DIR = <repo>/benchmarks/properties`. Resolving from
  `__file__` (not CWD) is robust to invocation directory; the only supported
  install is editable (`pip install -e .`), so the layout is stable.
- No `--rubric` → `load_rubrics(DEFAULT_RUBRICS_DIR)` yields both shipped
  rubrics (`formulation_quality_v1`, `answer_quality_v1`).
- No `--property-suite` → `load_property_suite(DEFAULT_PROPERTIES_DIR)` yields
  `artifact_baseline_v1`'s four checks.
- If a default dir is missing, warn and continue with an empty set rather than
  erroring — a benchmark should still run.
- *Minor deferred sub-decision:* packaging defaults as `importlib.resources`
  data instead of repo-relative paths. Not needed for α.4; noted so we don't
  treat the repo-relative approach as permanent.

## 2. Override vs. extend

**Explicit flags override defaults** (both `--rubric` and `--property-suite`).
Repeatable flags accumulate among themselves but replace the default set
entirely. Rationale: cleaner mental model, matches the earlier α-plan doc's
recommendation; a user who wants defaults + custom passes the default path
explicitly. `expected_properties` activation (item 3) is **independent** of this
— it always runs regardless of `--property-suite`, because it is per-case corpus
data, not a suite.

## 3. Activating `TestCase.expected_properties`

- In the engine, convert each `case.expected_properties[i]` string into a
  `PropertyCheck(name=<slug>, description=<the string>, target=<see item 4>,
  expected=True)`.
- `name`: slugify the string (lowercase, non-alnum → `_`, truncate) with an
  index suffix for uniqueness (e.g. `elicits_the_childs_age_0`).
- These per-case checks are merged with the loaded shared property suite(s), and
  **every property runs against both subjects** (raw + refined) so
  `PropertyAggregate` can report `raw_pass_rate` vs `refined_pass_rate`.
- Target routing for the subject text: `artifact` → the generated answers
  (`raw_answer` / `refined_answer`); `formulation` → `raw_formulation` /
  `refined_prompt`.

## 4. ⚠️ Polarity review — BLOCKING DECISION (needs user ruling)

> **[Amended 2026-07-08 — RESOLVED as option B.]** Activate as
> `target=formulation, expected=True`. See the Amendment log at the top of this
> document for the full rationale and the deferred cleanup queue. The original
> analysis below is preserved unchanged.

**Polarity itself is clean.** All 20 `expected_properties` strings across the 5
corpus cases are phrased *positively* ("elicits X," "avoids one-size-fits-all,"
"resists giving a generic recommendation"). So `expected=True` is uniformly
correct; there are **no** failure-mode strings needing `expected=False`. The
separate `expected_failure_modes` field is **not** activated in α.4 (out of
scope per issue #12).

**But there is a deeper mismatch — target, not polarity.** The design doc and
issue #12 say to activate these as **`target=artifact`** (evaluated against the
*answer*). Yet the actual strings are almost all **formulation**-shaped:

- `elicits the child's age`, `elicits whether the parent can swim`,
  `surfaces latent constraints`, `disambiguates the multiple meanings of
  "nothing"`, `does not bloat the prompt with unnecessary clarifying questions`
  — these describe what the **refined prompt** does, not what an answer does.

Mechanically activating `"elicits the child's age"` as `target=artifact` asks
the judge *"does this answer elicit the child's age?"* — close to nonsensical,
since answers respond rather than elicit. On the current corpus, `target=artifact`
activation would produce largely incoherent property results.

Note: the shipped `artifact_baseline_v1` suite (`addresses_stated_request`,
`no_unnecessary_refusal`, `no_obvious_unsupported_facts`, `respectful_tone`) *is*
genuinely artifact-shaped — so coherent artifact-target property checking already
has a clean default source independent of `expected_properties`.

**Options:**

- **(A) Spec-literal** — activate as `target=artifact, expected=True` exactly as
  written. Faithful to the authoritative doc; ships knowingly-incoherent results
  on the default corpus, documented as a validation finding.
- **(B) Intent-faithful — RECOMMENDED** — activate `expected_properties` as
  **`target=formulation`** (evaluate against `refined_prompt` / `raw_formulation`).
  Matches what the strings actually mean and what the Constitution says we
  optimize (the formulation). Deviates from the design doc's literal word; log
  the deviation as a one-line design-doc amendment.
- **(C) Don't activate in α.4** — rely on `artifact_baseline_v1` + the
  formulation rubric for α; defer `expected_properties` re-targeting to a corpus
  pass. Contradicts issue #12's explicit in-scope list.

**Recommendation: (B).** It is the only option that produces coherent property
signal on the existing corpus without new corpus authoring, and it keeps α.4
within integration scope (a target constant, not re-writing test cases). Follow
(A) only if strict spec-fidelity is preferred. **This is the one decision needed
before writing engine code**, since it changes which subject text the activated
checks are judged against.

## 5. Where aggregates are computed

In `engine.py`, alongside the existing `_aggregate`:

- `_aggregate_rubrics(results) -> dict[str, RubricAggregate]` — per
  `rubric_name`: `raw_mean_aggregate`, `refined_mean_aggregate`, `mean_delta`
  (refined − raw) from each case's `AbsoluteRubricEvaluation`s (subject raw vs
  refined), using simple means (reuse `scoring.py` helpers where applicable).
- `_aggregate_properties(results) -> dict[str, PropertyAggregate]` — per
  `property_name`: `raw_pass_rate`, `refined_pass_rate`, `n_applied`.
- Both called in `run_benchmark` and attached to
  `BenchmarkReport.aggregate_rubrics` / `.aggregate_properties`.
- `run_benchmark` / `_run_one_case` signatures extended with
  `rubrics: list[Rubric] | None = None` and
  `property_suites: list[PropertyCheck] | None = None`; runners reuse the
  existing `judge_provider` (no separate rubric-judge provider in α).
- Failure containment preserved: runner exceptions land in `errors[]`;
  per-target checks run only when their subject text exists (formulation-target
  runs when `refined_prompt` is available; artifact-target runs when answers
  were generated).

## 6. Where report sections appear

Insert **between Configuration/Runtime and Per-case results** (per design doc):

```
Headline
Configuration
Runtime
Rubric evaluations        (new)
Property checks           (new)
Disagreement diagnostic   (new)
Per-case results
Cases where refined was worse than raw
Errors
```

Three new render helpers in `report.py`. No single combined score anywhere.

## 7. Disagreement diagnostic rules

Compares **M3A's comparative-answer verdict** against each
**`target=formulation` rubric's raw→refined delta**. Artifact-target rubrics
(e.g. `answer_quality_v1`) are excluded from this diagnostic — they measure the
same axis as M3A (answer quality), so "disagreement" there is not the
high-diagnostic-value signal the design doc describes.

Named constants for later calibration: `EPS_TIE = 0.05`, `LARGE_DELTA = 0.15`.
Three patterns from the design doc:

- **P1** — M3A refined-win-`material` **and** `0 < delta < LARGE_DELTA`: answer
  model amplifying small formulation gains.
- **P2** — M3A refined-win-`material` **and** `delta ≤ EPS_TIE`: composite
  disagrees with formulation signal (highest diagnostic value).
- **P3** — M3A `tie` **and** `delta ≥ LARGE_DELTA`: formulation improved but
  didn't translate to the answer.

The section lists flagged cases with both verdicts side by side; it never merges
them into a single number.

## 8. Tests added (stub judges only)

Runner unit tests already exist (α.3:
`test_eval_rubric_runner.py`, `test_eval_property_runner.py`). α.4 adds/extends:

- **`test_eval_engine.py`** (extend) — stub judge; assert `rubric_evaluations` +
  `property_check_results` populate on `TestCaseResult`;
  `aggregate_rubrics`/`aggregate_properties` correct; `expected_properties`
  activation (with the item-4 target); M3A path unchanged; errored case still
  failure-contained.
- **`test_eval_report.py`** (extend) — new sections render; disagreement section
  populates on constructed divergent verdicts; assert **no** combined-score
  field appears.
- **`test_eval_cli.py`** (extend) — `--rubric`/`--property-suite` accepted and
  repeatable; omitting them loads defaults; explicit flags override defaults.
- **`test_eval_corpus.py`** (extend) — default-dir load smoke for both default
  dirs.
- Possibly a small aggregation test block for `_aggregate_rubrics` /
  `_aggregate_properties` in isolation.

## 9. Verification

- `pytest -q` — full suite green (currently 218; new tests add on top). All
  stub-driven; **zero real API calls**.
- CLI: `problemform benchmark --help` to confirm the two new flags render; a
  stub-provider end-to-end test that writes a report and asserts the three new
  sections plus default-loading behavior.
- Final `pytest -q` count and `--help` output to be pasted on completion.

---

## Open decision blocking start

Item 4 (A / B / C) — recommendation **(B)**. Everything else follows the
recommendations above unless changed on review.

> **[Amended 2026-07-08 — RESOLVED.]** Item 4 approved as **option B** via the
> external review chain (doc02 → doc03 → doc04). No other recommendations were
> changed on review. This decision no longer blocks start; implementation
> proceeds as the two-commit split (α.4a engine+aggregation, α.4b
> report+CLI+defaults). See the Amendment log at the top for details.
