---
title: "Plan: start work on M3B-α — implementation roadmap"
document_type: "plan"
status: "superseded"
created: "2026-06-05"
updated: "2026-07-08"
author: "Claude Code"
authoritative_reference: "docs/designs/milestone_03b_rubrics_and_properties.md"
related:
  documents:
    - "docs/designs/milestone_03b_rubrics_and_properties.md"
    - "docs/designs/problemform_scope.md"
  issues:
    - 12
---

# Plan: Start work on M3B-α — implementation roadmap

**Status: superseded — the M3B-α staircase (α.1–α.4) has since shipped; retained as the historical roadmap that framed the work.**

The user asked: should we start on M3B-α next, and if so, what should we do first? This document recommends an answer and a phased implementation plan that stays scoped to GH issue #12 and faithful to the Constitution.

## Should M3B-α be next?

**Yes.** The reasoning is consistent across three artifacts:

1. **The roadmap.** Issues #6 (corpus expansion) and #7 (calibration) are explicitly gated downstream of M3B-α in the recently-landed scope note and M3B design doc. Doing them first means doing them against a still-uncertain measurement framework. Doing M3B-α first means downstream work proceeds with both Path A and Path B available.
2. **The Constitution.** The Constitution emphasizes that "the deliverable is the formulation, not the answer." The current measurement framework (M3A) measures answers. M3B-α introduces formulation-target evaluation. The next implementation step is the one that brings the measurement closer to what the Constitution says we're optimizing for.
3. **The active hypotheses.** H1, H3, H4 from the scope note are conditionally retained pending M3B-α's validation experiments. Empirical resolution is bottlenecked on M3B-α landing. Until it lands, every downstream decision rests on unresolved hypotheses.

## Constitution alignment check

This is a measurement-framework patch, not a refinement-pipeline patch. The Constitution-bound risks to monitor:

- **Don't narrow naming.** Default rubric criterion vocabulary should generalize (e.g., "central claim," "assumptions," "constraints") rather than entrench question-specific framing ("the question," "the answerer"). This keeps the rubric usable on non-question inputs in M3B-β.
- **Don't synthesize lenses.** The design doc is explicit that M3A + rubrics + properties produce three parallel aggregates, never collapsed into one score. The implementation should keep this discipline; conflation would smuggle the M3A answer-quality assumption back into the headline.
- **Don't make Path B claim authority before validation.** Rubric scores ship as a complementary lens, not as the new ground truth. The M3A `ComparativeJudgment` stays the primary headline metric in `report.md`'s opening section until the validation experiments inform whether that priority should change.
- **Don't extend the refinement pipeline.** Tempting to add a "use the rubric to drive convergence" hook now. The design doc defers that explicitly; the convergence judge stays prompt-delta-primary until M3B-α validates.

The implementation phases below respect these constraints.

## Recommended phasing inside M3B-α

Three internal phases, each landing as its own focused commit under issue #12. The split mirrors the session-wide pattern of small reviewable patches (#4 → #4A; M3B design pass producing the design doc, then implementation as a separate exercise). All three close out under #12; no sub-issues needed.

### Phase M3B-α.1 — Data model + corpus loaders (start here)

Smallest reviewable patch. Lands the type system and the corpus-loading plumbing without touching the engine, report rendering, or CLI. Everything else builds on this.

**Files modified**

- `problemform/eval/models.py` — add `PropertyCheck`, `PropertyCheckResult`, `RubricCriterion`, `Rubric`, `CriterionScore`, `AbsoluteRubricEvaluation`. Do **not** add `TestCase.formulation_properties` in α.1; it is future-facing M3B-β corpus infrastructure, not needed to validate H1/H2. Extend `TestCaseResult` with `rubric_evaluations: list[AbsoluteRubricEvaluation]` and `property_check_results: list[PropertyCheckResult]` using `Field(default_factory=list)` (preserves backward compatibility with existing JSON). Extend `BenchmarkReport` with `aggregate_rubrics` and `aggregate_properties` using `Field(default_factory=dict)`; define `RubricAggregate` and `PropertyAggregate` only as far as α.2 aggregation requires.
- `problemform/eval/corpus.py` — add rubric and property-suite loaders that accept either a single YAML file or a directory walked recursively, matching the planned repeatable `--rubric <path>` / `--property-suite <path>` CLI flags. Reuse the `CorpusError` umbrella.
- `tests/test_eval_models.py` — round-trip serialization for each new type, plus a test asserting that a pre-M3B-α `report.json` (without the new fields) still parses via `BenchmarkReport.model_validate_json` due to defaults.
- `tests/test_eval_corpus.py` — successful YAML load and a malformed-case CorpusError test for each new loader.

**Files created**

- `benchmarks/rubrics/` (directory; one small README explaining what goes here).
- `benchmarks/properties/` (same). This supports shared property suites in α without adding per-test-case formulation-property fields yet.

**What is NOT done in this phase**

- No engine integration (runners not invoked from `run_benchmark`).
- No report.md changes.
- No CLI flags.
- No default rubrics shipped.
- No `TestCase.formulation_properties` field. If α validation needs formulation-target property checks, use `benchmarks/properties/` as shared suites; per-case formulation properties wait for M3B-β corpus diversification.

This phase is roughly the size of M3A's data-model patch. Reviewable in one pass.

### Phase M3B-α.2 — Runners + engine integration + report + CLI + default rubrics

Lands the actual bridge. After M3B-α.1, this is the substantive M3B-α patch.

**Files modified**

- `problemform/eval/property_runner.py` (new) — `run_property_checks(case, raw_subjects, refined_subjects, judge_provider) -> list[PropertyCheckResult]`. Activates `TestCase.expected_properties` as `target=artifact, expected=True` checks. Uses a target-aware judge prompt that asks whether the subject (answer/artifact or formulation) satisfies the property, yes/no with rationale.
- `problemform/eval/rubric_runner.py` (new) — `run_rubric(rubric, subject_text, subject_label, judge_provider) -> AbsoluteRubricEvaluation`. Iterates criteria, calls the judge per criterion with a small prompt template, aggregates to the weighted average.
- `problemform/eval/engine.py` — extend `_run_one_case` to accept rubrics + property suites; call `run_rubric` and `run_property_checks` per case; populate `TestCaseResult.rubric_evaluations` and `property_check_results`. Extend `run_benchmark` signature with `rubrics: list[Rubric] = None` and `property_suites: list[PropertyCheck] = None` parameters. Add `_aggregate_rubrics` and `_aggregate_properties` helpers.
- `problemform/eval/report.py` — add `_rubric_evaluations_section`, `_property_checks_section`, and `_disagreement_diagnostic_section` (the disagreement section is the high-value diagnostic per the design doc). Render after Configuration, before Per-case results.
- `problemform/cli.py:benchmark` — add `--rubric <path>` (repeatable) and `--property-suite <path>` (repeatable) flags. Default behavior loads the two shipped rubrics + any per-case `expected_properties`.

**Files created**

- `benchmarks/rubrics/formulation_quality_v1.yaml` — `target=formulation, mode=absolute`. Five criteria (per the design doc): central-claim clarity, assumption surfacing, constraint articulation, alternative-framing coverage, meta-question presence. Criterion descriptions use input-agnostic language (not "the question") to keep generalization open.
- `benchmarks/rubrics/answer_quality_v1.yaml` — `target=artifact, mode=absolute`. Five criteria: addresses-input-intent, factual accuracy, actionability, calibrated confidence, proportionate length.
- `problemform/eval/prompts/rubric_judge.py` — judge prompt template for scoring a single criterion against a subject.
- `problemform/eval/prompts/property_judge.py` — judge prompt template for evaluating a single property against a subject.
- `tests/test_eval_rubric_runner.py` — unit tests with a recording stub judge: criterion iteration order, normalized scoring, weighted aggregation, raw-vs-refined delta correctness.
- `tests/test_eval_property_runner.py` — unit tests for binary verdicts, expected-polarity handling, per-property pass-rate aggregation.
- `tests/test_eval_engine.py` — extend to assert rubric + property results land on `TestCaseResult` and aggregates compute correctly; the existing M3A tests stay passing.
- `tests/test_eval_report.py` — assert the three new sections appear in `report.md` with correct contents; assert the disagreement section is populated when M3A and rubric verdicts diverge.
- `tests/test_eval_cli.py` — extend the stub smoke test to confirm `--rubric` and `--property-suite` flags work and that omitting them loads defaults.

**What is NOT done in this phase**

- No comparative-mode rubrics (deferred to M3B-β).
- No position-randomization for rubrics (only needed for comparative mode).
- No actual API runs. All tests use stub judges.
- No formulation-only benchmark mode yet. For the H2 non-question probe, run the existing pipeline but treat M3A answer metrics as non-authoritative/noisy and evaluate H2 from the formulation rubric output.

### Phase M3B-α.3 — Validation experiments + findings doc

Empirical resolution of H1, H2 (and consequently H3, H4). Cost-bounded; manual; not a code patch.

**Steps**

1. Run `problemform benchmark benchmarks/default --rubric benchmarks/rubrics/formulation_quality_v1.yaml` against the existing M3A corpus with whatever provider trio you've been using. Capture report.json + report.md. Because explicit `--rubric` flags override default-rubric autoloading (see open question below), this keeps the H1 run focused on the formulation-quality lens.
2. Run twice or three times to assess internal consistency (rubric scores stable across runs).
3. Construct a single-case YAML for the Aquinas input. Place it under `benchmarks/non_question_probe/aquinas.yaml` (gitignored or a new tracked directory). Run `benchmark` against it with the formulation rubric. The M3A answer comparison may still execute because α does not add formulation-only benchmark mode; ignore it for H2 except as a note about why formulation-target evaluation is needed.
4. Author `docs/reports/m3b_alpha_validation_<YYYY-MM-DD>.md` with:
   - Setup (corpus version, provider trio, rubric version).
   - H1 results (question-corpus rubric scores, internal-consistency observation, correlation with M3A verdicts).
   - H2 results (Aquinas-case rubric scores, coherence assessment).
   - Empirical resolution of H1 and H2 with explicit yes / partial / no findings.
   - Implications for H3 and H4.
   - Decisions: does M3B-as-bridge survive the test? If yes, proceed to M3B-β corpus diversification (rescoped #6). If partial, propose specific adjustments. If no, propose reverting to M3A continuation.
5. Update the M3B design doc's hypothesis-resolution section in light of the findings.

Cost ballpark for the explicit `formulation_quality_v1` H1/H2 runs: ~50 rubric-judge calls for H1 (5 cases × 5 criteria × 2 subjects), ~10 for H2 (1 × 5 × 2), plus the existing M3A pipeline calls that still run. Default autoloading both rubrics would roughly double rubric-judge calls, so the validation commands should pass only the formulation rubric unless answer-quality scoring is intentionally being studied too.

Optional: also run the `answer_quality_v1` rubric on the corpus in the same run. Gives a third lens (per-criterion answer scoring) parallel to M3A's comparative answer judgment.

## What to do first (concrete first step)

**Phase M3B-α.1.** Smallest reviewable patch, lowest-risk start, unblocks everything else. Within Phase M3B-α.1, the order is:

1. `problemform/eval/models.py` — add types and field extensions. Run `pytest -q` after every save to make sure existing tests still pass (the new fields are defaulted; nothing should break).
2. `problemform/eval/corpus.py` — add the two loaders.
3. `tests/test_eval_models.py` and `tests/test_eval_corpus.py` — add focused tests. Run `pytest -q` to confirm green.
4. Commit with a message like `feat(eval): add rubric and property-check data model (M3B-α.1)`.

## Open questions to resolve before starting

- **`formulation_properties` inclusion.** The design doc lists this as M3B-α scope; the GH issue body lists it as "reconsider for M3B-β." Recommended resolution after implementation-plan review: **defer the field to M3B-β**. It is not necessary to validate H1/H2: H1 uses `formulation_quality_v1`; H2 uses the same formulation rubric on the Aquinas probe. If α needs formulation-target property checks, shared suites under `benchmarks/properties/` are enough. Adding a per-case field now is harmless technically, but it is schema surface area for corpus diversification before corpus diversification has started.
- **Default-rubric autoloading vs explicit flags.** The design doc says default behavior loads the two project default rubrics. Edge case: what should happen when the user passes only `--rubric <custom>`? Override the defaults, or add to them? Recommended: explicit flag overrides defaults (cleaner mental model, easier to reason about). The user can always pass both `--rubric formulation_quality_v1.yaml --rubric custom.yaml` if they want both.
- **Judge prompt for rubric criteria.** Should each criterion have a custom judge prompt, or should the framework use a single generic template that substitutes in criterion description? Recommended: single generic template (less per-rubric authoring cost; criterion description carries the meaning). If a criterion turns out to need bespoke prompting, we can add per-criterion override later.
- **Disagreement diagnostic threshold.** "M3A says refined-win-material vs rubric says raw wins" is obvious; "M3A says tie vs rubric shows tiny refined delta" is not. Recommended: surface only the three disagreement patterns named in the design doc, adapted for absolute-mode rubrics: rubric-vs-M3A directional mismatch, M3A material win with only a small rubric delta, and M3A tie with a large rubric delta. Define a small epsilon (e.g. `< 0.05`) as "tie/no meaningful rubric delta" and a larger threshold (e.g. `>= 0.15`) as "large rubric delta" in the report helper, with constants named so calibration can adjust them later. Do not refer to "rubric materiality classes" for absolute rubrics; they do not exist in α.
- **Provider role for rubric / property judging.** The benchmark CLI already has `--judge-provider` for M3A's comparative judge. Reuse for rubric criterion judgment, or introduce a separate `--rubric-judge-provider`? Recommended: reuse the existing `--judge-provider` for M3B-α. Separate provider configuration is M3B-β if needed.

These are not blocking — recommended resolutions are listed. They surface here so the choices are made explicitly rather than by default.

## External-review recommendation

The user asked whether to have Codex or ChatGPT Desktop review this plan.

**Codex review: worthwhile.** Codex caught real things in the constitution alignment audit — particularly the visible-quality-assessment artifact and the expert-directed-rewrite-fields gaps that this session had not captured. For an implementation plan that involves data-model design, runner architecture, and engine integration, Codex's repo-aware reading is likely to flag specific concerns this session may miss (e.g., backward-compat edge cases, naming-collision risks, redundancy with existing M3A patterns).

**ChatGPT Desktop review: less obvious value.** ChatGPT Desktop does not have repo context; review at the conceptual level is mostly a repeat of what's already documented in the M3B design doc and scope note. Could provide useful red-team feedback on the working hypothesis framing, but the design doc has already absorbed that input via the user's revision rounds.

**Recommendation:** get Codex to review this plan before any code lands. Apply revisions, then start Phase M3B-α.1. Skip ChatGPT for this specific plan; reserve it for moments where conceptual second-opinion is more valuable than repo-aware critique.

If Codex review surfaces design changes that contradict the M3B design doc or the scope note, those go back into the M3B design doc as updates (preserving the design as canonical), not into this implementation plan in isolation.
