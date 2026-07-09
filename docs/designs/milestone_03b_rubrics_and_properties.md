---
title: "Milestone 3B design reference: rubrics, property checks, and the formulation target"
document_type: "design"
status: "active"
created: "2026-06-05"
updated: "2026-07-09"
author: "Claude Code"
authoritative_reference: "docs/problemform_constitution.md"
related:
  documents:
    - "docs/problemform_constitution.md"
    - "docs/designs/problemform_scope.md"
    - "docs/designs/milestone_03_evaluation_framework.md"
    - "docs/backlog.md"
  issues:
    - 8
    - 9
    - 12
---

# Milestone 3B design reference: rubrics, property checks, and the formulation target

**Status: active design pass. Tests the working hypothesis from [`problemform_scope.md`](problemform_scope.md). Sections labeled *Hypothesis*, *Decision*, or *Open question* signal the resolution status of each claim.**

## Context

M3A landed `problemform benchmark`: a per-case pipeline that refines a raw question via the ProblemForm phases, generates two answers (raw and refined), runs a position-randomized comparative judgment on the answer pair, and aggregates a three-way scoreboard plus material-improvement and degradation rates over a YAML corpus.

M3B is the next planned milestone in `docs/roadmap.md`: "rubric-based prompt and answer evaluation, expected properties and behavioral assertions, answer-level quality comparisons, benchmark reporting and score aggregation." M3B was originally framed as adding more-sophisticated evaluation mechanisms (rubrics, property checks) on top of M3A's comparative-judgment substrate.

The scope-question design note ([`problemform_scope.md`](problemform_scope.md)) reframes M3B as something potentially larger: the **bridge** from question refinement to general problem formulation. The key reframe is that M3A measures a composite signal (`ProblemForm × Answer Model`) and only operates on inputs that have natural "answer" artifacts. M3B's mechanisms — rubrics and property checks — are scope-agnostic by construction. Whether they become the bridge depends on a single design choice: **the evaluation target**.

This document is the design pass that takes that choice seriously. It is not a complete implementation plan; it is the design reference that an M3B implementation patch will follow, similar in form to [`milestone_03_evaluation_framework.md`](milestone_03_evaluation_framework.md). Specific implementation patches (data-model additions, CLI commands, corpus formats) come later, scoped to the smallest reviewable units as in #4A / progress visibility.

The four working hypotheses from the scope note are addressed throughout, with explicit resolution at the end:

- **H1.** Path B (judging the formulation directly) is a viable generalization path beyond questions.
- **H2.** M3B's mechanisms are scope-agnostic enough to implement Path B if designed with the target as a first-class axis.
- **H3.** M3B-as-bridge is the more strategically valuable framing.
- **H4.** Implied issue ordering: #8+#9 → #6 → #7.

## The target axis (the core design decision)

The scope note identifies "what is the evaluation target?" as the load-bearing question for M3B. The original M3A design doc treats answers as the implicit target. The scope note proposes treating the target as a first-class parameter ranging over `{formulation, artifact}`.

This design adopts that axis and extends it slightly to make the comparative-vs-absolute dimension explicit:

- **Target** — what is being evaluated? `formulation` (the prompt / problem statement ProblemForm produces) or `artifact` (the downstream output, today an answer).
- **Mode** — how is it evaluated? `absolute` (score this one thing on its own merits) or `comparative` (compare two things head-to-head).

Cross-producting these gives four evaluation contracts:

| Mode \ Target | `formulation` | `artifact` |
|---|---|---|
| `absolute` | Score the formulation against criteria. | Score the answer against criteria. |
| `comparative` | Compare raw-formulation to refined-formulation. | Compare raw-answer to refined-answer. (M3A.) |

**Decision.** Both rubrics and property checks carry an explicit `target` and `mode`. The framework supports all four combinations from day one. This is the H2-resolution: the mechanisms are scope-agnostic if and only if this axis is exposed; designing for it costs one design parameter and avoids a costly retrofit. The axis is not a new mechanism — it's a contract on existing ones.

**Decision.** M3A's existing comparative-answer-judgment fits into this contract as `(target=artifact, mode=comparative)`. M3A is therefore one quadrant of M3B's surface, not a separate framework. No M3A changes are required for backward compatibility; new M3B mechanisms layer alongside.

**Decision.** The "Path B" the scope note describes is the `target=formulation` half of this contract. M3B-as-bridge means **first-class support for `target=formulation`**, both absolute and comparative. M3B-as-continuation would mean adding only the `target=artifact, mode=absolute` quadrant — sophistication without generalization. The first-class formulation target is the bridge.

## Rubric framework (#8)

### What a rubric is

A rubric is a named, ordered collection of weighted criteria, evaluated against a target. Each criterion is judged by an LLM and produces a numeric score plus a short rationale. The rubric's aggregate is a weighted average of per-criterion scores.

Rubrics are *graded* — they produce continuous (or many-valued discrete) signal. They are best suited to "how good is this on these dimensions?" questions, where judgment is non-binary and aggregating signal across dimensions is informative.

### Schema

```python
class RubricCriterion(BaseModel):
    name: str
    description: str          # what the criterion is asking
    weight: float = 1.0        # for weighted aggregation
    scoring: Literal["binary", "graded_3", "graded_5"] = "graded_5"
    rationale_required: bool = True

class Rubric(BaseModel):
    name: str
    description: str
    target: Literal["formulation", "artifact"]
    mode: Literal["absolute", "comparative"]
    criteria: list[RubricCriterion]
    schema_version: int = 1
    notes: str | None = None
```

Two evaluation result types, distinguished by mode:

```python
class CriterionScore(BaseModel):
    criterion_name: str
    score: float              # 0.0-1.0 normalized regardless of raw scale
    raw_score: int             # what the judge returned on the criterion's scale
    rationale: str

class AbsoluteRubricEvaluation(BaseModel):
    rubric_name: str
    target: Literal["formulation", "artifact"]
    subject: Literal["raw", "refined"]
    criterion_scores: list[CriterionScore]
    aggregate_score: float    # weighted average of normalized scores

class CriterionComparison(BaseModel):
    criterion_name: str
    winner: Literal["a", "b", "tie"]
    winner_actual: Literal["raw", "refined", "tie"]
    rationale: str

class ComparativeRubricEvaluation(BaseModel):
    rubric_name: str
    target: Literal["formulation", "artifact"]
    presented_first_actual: Literal["raw", "refined"]
    criterion_comparisons: list[CriterionComparison]
    overall_winner: Literal["raw", "refined", "tie"]
    overall_materiality: Materiality    # reuse from M3A
```

`Materiality` is reused from M3A unchanged. `presented_first_actual` mirrors M3A's bias-mitigation pattern — comparative rubric evaluations are position-randomized per call.

### Aggregation

- **Absolute mode.** `aggregate_score = sum(weight_i * normalized_score_i) / sum(weight_i)`. Normalization maps the criterion's raw scoring scale (`binary`, `graded_3`, `graded_5`) to `[0, 1]`. The aggregate is informative both per-subject (how good is the refined formulation?) and as a delta (refined_aggregate − raw_aggregate) when both subjects are scored under the same rubric.
- **Comparative mode.** Per-criterion winners aggregate into an overall verdict by majority vote with ties broken by the judge in a separate final pass. The overall materiality is judged once, not per criterion.

**Decision.** When a rubric is used in absolute mode against both raw and refined subjects in the same run, the engine produces a *delta report*: per-criterion score differences and overall aggregate delta. This is the natural comparison vehicle for absolute-mode rubrics; comparative-mode rubrics are only needed when the per-criterion judgment benefits from seeing both subjects side by side (e.g., for subjective criteria where calibration drifts when scoring in isolation).

### How rubric criteria differ by target

A `target=formulation` rubric asks questions about the formulation:

- Does the formulation name a central claim or objective?
- Does it surface load-bearing assumptions?
- Does it identify the strongest counter-position?
- Does it state what evidence would change the user's mind?
- Does it articulate constraints or success criteria?
- Does it avoid burying the user's intent under template scaffolding?

A `target=artifact` rubric asks questions about the answer:

- Does the answer address the question?
- Is it factually accurate?
- Is it actionable?
- Does it acknowledge limits of its applicability?
- Is its length proportionate to its substance?

These are not the same criteria. The `target` axis isn't just routing — it changes what's being measured. The framework does not auto-translate; rubric authors write criteria appropriate to the target.

### Default rubrics

Two default rubrics ship with the framework to seed adoption and serve as references:

- **`formulation_quality_v1`**. `target=formulation, mode=absolute`. Five criteria: `central_claim_clarity`, `assumption_surfacing`, `constraint_articulation`, `alternative_framing_coverage`, `meta_question_presence`. This rubric is the bridge made concrete — it's the first measurement instrument that applies uniformly to questions and non-questions. The `meta_question_presence` criterion is phrased to apply beyond literal question-shaped inputs (higher-order frame / clarification need / uncertainty / decision point); H2 validation should confirm this phrasing holds for arguments, decision briefs, and other non-question formulations.
- **`answer_quality_v1`**. `target=artifact, mode=absolute`. Five criteria: `directness`, `factual_care`, `reasoning_quality`, `constraint_satisfaction`, `usefulness`. This rubric extends M3A's existing comparative judgment with finer-grained signal on the answers it already produces. The criteria were revised from an earlier sketch (which listed addresses-input-intent / factual accuracy / actionability / calibrated confidence / proportionate length) to be more operational for absolute-mode LLM judging without external fact verification: `factual_accuracy` becomes `factual_care` (calibration and overclaiming, which a judge can assess); `proportionate_length` is folded into `directness` / `usefulness` / `constraint_satisfaction` rather than kept as a first-class criterion.

Both default rubrics live under `benchmarks/rubrics/` (the directory mentioned but deferred in the M3A design doc). Test cases name which rubrics apply to them; suite-wide defaults are also supported.

## Property check framework (#9)

### What a property check is

A property check is a named binary assertion about a target: it either holds or it doesn't. Property checks are *binary*, *targeted*, and *regression-shaped*. They are best suited to "does this satisfy this specific property?" questions where the answer is intended to be unambiguous and the value lives in tracking the property across many cases.

Property checks differ from rubric criteria in three ways:

- **Output is binary**, not graded.
- **Each property is independent**, not weighted into an aggregate quality score.
- **The use case is regression assertion**, not quality measurement. A property check codifies "this should always be true"; a rubric criterion codifies "this is more or less met."

A single rubric criterion with `scoring=binary` can do the same mechanical work as a property check. The distinction is semantic and reporting-shaped, not mechanical: rubrics report aggregate quality; property checks report compliance rates.

### Schema

```python
class PropertyCheck(BaseModel):
    name: str
    description: str
    target: Literal["formulation", "artifact"]
    expected: bool = True       # most properties assert presence; some assert absence

class PropertyCheckResult(BaseModel):
    property_name: str
    target: Literal["formulation", "artifact"]
    subject: Literal["raw", "refined"]
    holds: bool
    expected: bool
    passed: bool                # holds == expected
    rationale: str
```

Property checks operate only in absolute mode. Comparative-mode binary judgments are subsumed by `mode=comparative` rubrics with `scoring=binary`.

### Activation of `TestCase.expected_properties`

The existing `TestCase.expected_properties: list[str]` field has carried hand-written property strings since M3A but has been "stored but not evaluated." M3B activates it. The original design intent (below) interpreted each string as a `target=artifact, expected=True` property check by default — the historical M3A interpretation. New per-case `formulation_properties: list[str]` (`target=formulation`) and shared property suites under `benchmarks/properties/` extend this.

The M3A test cases gain immediate signal from this activation: the existing four `expected_properties` lines per case become four runnable property checks per case, retrofitted from documentation to test.

> **Amendment (M3B-α.4, 2026-07-08 — activation target changed to `formulation`).** When α.4 came to activate this field, a corpus review found the shipped `expected_properties` strings are *predominantly formulation-shaped* — they describe what the refined formulation should surface or preserve ("elicits the child's age", "surfaces latent constraints", "disambiguates the multiple meanings of 'nothing'"), not what a downstream answer should do — though a few are mixed or answer-readable (notably the control case `what_causes_eclipses`). Because the property-judge prompt is target-aware (it asks about the *answer* under `target=artifact` and about the *formulation* under `target=formulation`), activating these as artifact checks would ask the judge nonsensical questions and produce incoherent results on the current corpus. **α.4 therefore activates `expected_properties` as `target=formulation, expected=True`.** For α.4 this is the cleaner default: it produces coherent signal on the current corpus and aligns with the M3B bridge goal of first-class formulation evaluation. It is an implementation correction grounded in corpus reality, not a redesign. Artifact-target coverage is **not** lost — the shipped `artifact_baseline_v1` suite provides genuine `target=artifact` checks, default-loaded independently. The per-case `formulation_properties` field remains deferred to M3B-β (not added in α.4). Decision trail: `docs/plans/m3b_alpha_4_doc01_plan_by_claude.md` (item 4) and the review chain doc02→doc03→doc04.

### Aggregation

For a benchmark run with N cases, K property checks each (some shared via suites, some per-case), the aggregate reports:

- Per property: pass rate across cases (`n_passed / n_applicable`).
- Per case: pass rate across properties applied to it.
- Per target: pass rate aggregated by `formulation` vs `artifact`.

There is no weighted "overall property score." Property checks are individually meaningful; aggregating them into a single number conflates very different signals (e.g., factual accuracy and length-appropriateness).

## How M3A, rubrics, and property checks compose in one run

A benchmark run today applies one comparative answer judgment per case. M3B extends this so each case can carry:

1. Zero or more rubrics (each with its own `target` and `mode`).
2. Zero or more property checks (each with its own `target`).
3. The existing M3A comparative answer judgment (always present in the default configuration; suppressible via flag if desired).

For each case, the engine produces:

- One `TestCaseResult` with the M3A `ComparativeJudgment` (existing field).
- A list of `RubricEvaluation`s (mix of absolute and comparative depending on rubric mode).
- A list of `PropertyCheckResult`s.

All three live as siblings on `TestCaseResult`; they do not interleave. The aggregation produces three parallel aggregates on `BenchmarkReport`: the existing `aggregate` (M3A metrics), a new `aggregate_rubrics` (per-rubric absolute deltas and per-rubric comparative win-rates), and a new `aggregate_properties` (per-property pass rates).

**Decision.** M3B does *not* synthesize the three aggregates into a single overall score. Rubric authors who want a headline number define a rubric with that aggregation built in (e.g., a `formulation_quality_v1` aggregate is already a single number for that rubric). Treating M3A's comparative verdict, rubric deltas, and property compliance rates as one weighted score would conflate measurements of different things — formulation quality vs answer quality vs regression compliance. The report keeps them visually separate.

### When rubric verdicts disagree with M3A verdicts

A core motivation for M3B-as-bridge is gaining a second, independent lens. The interesting outcome — and the validation of H1 in particular — is what happens when the lenses disagree.

Three disagreement patterns to look for:

1. **M3A says refined-win-material, formulation rubric says refined wins by a small delta.** The composite signal exceeds the formulation-quality signal, meaning the answer model is amplifying small formulation gains. Suggests the M3A signal is partially answerer-driven, not formulation-driven. Diagnostic value: high.
2. **M3A says refined-win-material, formulation rubric says raw wins or ties.** The composite signal disagrees with the formulation signal. Could mean the refined formulation is structurally worse but the answer model handles it better anyway (verbosity bias is one candidate explanation). Diagnostic value: very high — this is the failure mode the scope-note confound predicts.
3. **M3A says tie, formulation rubric shows large refined delta.** The formulation improved meaningfully but didn't translate to a better answer. Could mean the formulation gains are illegible to the answer model, or the rubric is over-rewarding structural changes. Diagnostic value: moderate — distinguishes "good formulation, indifferent answerer" from "no-op formulation change."

The benchmark report should surface these disagreements as a dedicated diagnostic section, analogous to M3A's existing "cases where refined was worse than raw" section. The cases where rubric and M3A disagree are the cases worth human review.

## Sub-milestone phasing

M3B's surface is large enough that landing it as a single patch is impractical. Two sub-milestones, each landing as its own reviewable change set:

### M3B-α — Bridge MVP (formulation rubrics + property checks, default rubrics, no comparative-mode rubrics)

Smallest version that exercises the bridge hypothesis:

- New Pydantic types: `RubricCriterion`, `Rubric`, `CriterionScore`, `AbsoluteRubricEvaluation`, `PropertyCheck`, `PropertyCheckResult`.
- New corpus directories: `benchmarks/rubrics/` (rubric YAMLs), `benchmarks/properties/` (shared property suites).
- New engine module: `problemform/eval/rubric_runner.py`. Runs absolute-mode rubrics against `raw_prompt` and `refined_prompt` (the formulation subjects).
- New engine module: `problemform/eval/property_runner.py`. Runs property checks against the configured target.
- Ship the two default rubrics (`formulation_quality_v1`, `answer_quality_v1`) and activate the M3A test cases' existing `expected_properties` as property checks (activated as `target=formulation` in α.4 — see the "Activation of `TestCase.expected_properties`" amendment above).
- Extend `TestCaseResult` and `BenchmarkReport` with `rubric_evaluations` and `property_check_results` siblings to the existing `comparative_judgment`. Extend `BenchmarkReport` with `aggregate_rubrics` and `aggregate_properties`.
- Extend `report.md` with `## Rubric evaluations` and `## Property checks` sections between the existing Configuration and Per-case results. The disagreement-diagnostic section described above is part of M3B-α.
- CLI: extend `benchmark` with `--rubric <path>` (repeatable) and `--property-suite <path>` (repeatable). Default behavior loads the project default rubrics if no flags given.

M3B-α is the minimum version that lets us run the validation experiments (next section) and resolve H1–H3.

### M3B-β — Comparative-mode rubrics and corpus diversification

Once M3B-α has produced evidence on the working hypotheses, M3B-β layers on:

- Comparative-mode rubrics (`ComparativeRubricEvaluation`).
- Position-randomization machinery for rubric comparisons (reuses the M3A pattern).
- Corpus expansion as called for by issue #6 (rescoped): first non-question categories — arguments, decisions, belief critiques. The Aquinas case in `problemform_scope.md` is the prototype for the argument category.
- Optional `target=delta` rubrics, if the validation experiments suggest delta-specific criteria are needed.

M3B-β is where the bridge becomes load-bearing for non-question inputs. M3B-α is where we find out whether the bridge actually carries weight.

### What's deferred to M3C (not in M3B)

- Multi-judge K>1 aggregation (still Phase C per M3A design doc).
- Held-out / dev splits.
- Inter-judge agreement metrics.
- Cost / token sweeps and matrix automation (issues #10, #11).
- HTML / TUI rendering.

## Validation strategy (how the M3B design pass tests its own hypotheses)

The design pass cannot fully resolve H1–H4 by reasoning alone. M3B-α produces the experiments that resolve them. The validation strategy is:

### For H1 (Path B viable)

Apply `formulation_quality_v1` (absolute mode) to the existing five-case question corpus. Two checks:

- **Internal consistency.** The rubric produces stable per-criterion scores when run multiple times against the same formulation. If criterion scores swing wildly across runs, the rubric criteria are under-specified and Path B has a calibration problem analogous to M3A's.
- **Correlation with M3A.** Cases where M3A scored refined-win materially should also show the rubric scoring refined-formulation higher than raw-formulation. If the correlation is high, the two lenses corroborate each other on questions and we have evidence Path B measures something meaningful. If it is low, we have a finding (the lenses measure different things), which is a different kind of useful but means H1 needs revisiting.

### For H2 (mechanisms scope-agnostic)

Apply `formulation_quality_v1` to a single non-question input (the Aquinas case from `problemform_scope.md`). Two checks:

- **Does it produce a coherent evaluation at all?** The rubric criteria are written input-agnostically; do they actually produce sensible criterion scores for an argument-shaped input?
- **Does the rubric distinguish ProblemForm output from the raw input?** If the refined formulation of the Aquinas case scores higher than the raw input on the formulation rubric, the framework operates on non-questions in the way the bridge hypothesis predicts.

This validation doesn't require an answer for the Aquinas case — the M3A pipeline still runs the eight phases over it, producing `final_prompt` even though no comparative answer judgment is meaningful. The rubric evaluates `raw_prompt` vs `final_prompt` directly.

### For H3 (M3B-as-bridge strategically valuable)

A function of H1 and H2. If both hold:

- Path B is real signal (H1).
- Path B operates on non-questions (H2).
- Therefore M3B does what M3A cannot (H3).

If H1 holds but H2 fails: M3B is a useful M3A supplement on questions but not a bridge.
If H2 holds but H1 fails: M3B operates on non-questions but its signal is unreliable; the bridge is wobbly.
If both fail: M3B should be reframed as continuation, not bridge.

### For H4 (issue ordering)

If H3 holds: implied ordering #8+#9 (this design + M3B-α implementation) → #6 (corpus diversification, rescoped) → #7 (calibration with both lenses available). The previous ordering changes.

If H3 doesn't hold: previous ordering reasonable. M3B is layered onto M3A for questions; #6 and #7 proceed independently.

## Resolution of working hypotheses

**At design pass closure (2026-06-05):**

- **H1.** Plausibility-resolved as plausible (the confound argument from the scope note is structurally sound). Empirical resolution awaits M3B-α implementation + validation experiment 1.
- **H2.** Design-resolved as **yes**. The target axis is exposed as a first-class parameter in both rubric and property-check schemas; mechanisms are scope-agnostic by construction. Empirical resolution (does the rubric actually produce sensible scores on non-questions?) awaits M3B-α + validation experiment 2.
- **H3.** Design-resolved as **conditionally yes** — M3B-as-bridge is adopted as the working framing for M3B-α, contingent on H1 and H2 empirically holding. If validation experiments invalidate either, this design pass's "bridge" framing should be revisited before M3B-β.
- **H4.** Provisionally retained. M3B-α is the natural next implementation patch (it lands the framework). #6 reshapes (category diversity) become natural after M3B-α validates. #7 calibration becomes more interpretable with both lenses. If H1 or H2 falls in validation, the ordering reverts.

**Empirical update (2026-07-09, from the M3B-α validation runs).** Full findings and
data in [`docs/reports/m3b_alpha_validation_2026-07-08.md`](../reports/m3b_alpha_validation_2026-07-08.md).
Recorded as the evidence supports — including the branches that would *not* have
affirmed the bridge framing, so the resolution is driven by the data rather than by
the design's prior:

- **H1 — empirically SUPPORTED for viability; Path B is complementary to, not
  redundant with, M3A.** On the 5-case question corpus (3 runs, `gpt-4o` rubric
  judge): the rubric is internally consistent (identical raw inputs scored with
  stdev ≤ 0.04 at temperature 0; aggregate raw→refined delta stable at
  +0.41/+0.41/+0.44; all 15 case-runs positive). It corroborates M3A on *direction*
  but diverges on *magnitude* — the control case (formulation Δ ≈ +0.05 yet an M3A
  material answer-win) is the scope-note confound made concrete, evidence Path B
  isolates formulation quality that M3A cannot. The failure mode that would have
  sunk H1 (an unstable, run-to-run-swinging rubric) did not occur.
- **H2 — empirically SUPPORTED on the Aquinas argument probe (one non-question
  type).** 3 clean cross-family runs (`gpt-4.1` answers, `claude-sonnet-4-6` rubric
  judge): the rubric produced coherent per-criterion scores on the argument (raw
  0.45 — a higher floor than bare questions, correctly reflecting the argument's
  pre-existing structure) and distinguished the refined formulation from the raw
  input in every run (mean Δ +0.28, no sign flips). Rubric determinism replicated
  under a *different* judge family (raw stdev 0.000). This supports scope-
  agnosticism on the **argument** shape; decisions, beliefs, and dilemmas remain
  untested, so this is not yet a general result. Had the scores been incoherent or
  shown no raw-vs-refined distinction, H2 would read "not supported" and H3 would
  take the "useful M3A supplement on questions, but not a bridge" branch — it does
  not.
- **H3 — empirically SUPPORTED on the tested cases, pending breadth.** With H1
  holding on questions and H2 holding on the argument probe, M3B does what M3A
  cannot (M3A has no leverage on the Aquinas input — no natural answer). The broad
  strategic claim still rests on more non-question types (M3B-β / #6).
- **H4 — ordering retained/strengthened.** #8+#9 (framework) landed and validated;
  proceed to **#6** (diversify to more non-question types) then **#7** (calibration,
  now concretely motivated by the H1 rubric-floor and disagreement-threshold
  findings).

Two implementation notes surfaced during validation, tracked in `docs/backlog.md`:
the `AnthropicProvider` `system`-param bug (fixed, commit `7c43fae`, which enabled
the H2 cross-family judge), and a minor Anthropic JSON-mode reliability observation.

## Open questions for M3B-α implementation

These were Q1–Q5 in the scope note; updated with this design pass's resolutions where applicable.

- **Q1 (target axis).** *Resolved.* Both `target` and `mode` are first-class axes for both rubrics and property checks. The four-quadrant contract is the framework's surface.
- **Q2 (formulation rubric criteria).** *Partially resolved.* `formulation_quality_v1` ships with five criteria as the seed rubric. Empirical work in M3B-α will determine whether these criteria are well-specified enough for reliable judgment, or whether they need iteration.
- **Q3 (bias mitigations for Path B).** *Open.* Position randomization transfers directly to comparative-mode rubrics. Verbosity bias may show up differently in formulation judging (longer formulations may be over-rewarded). Self-preference bias requires the same family-detection check as M3A. M3B-α should reuse the M3A bias-mitigation patterns where the mechanism transfers and introduce new mitigations only where it doesn't.
- **Q4 (unit of comparison for Path B).** *Resolved.* Absolute mode against raw-formulation and refined-formulation produces a delta; comparative mode against raw-vs-refined produces a head-to-head winner. Both are available. Choice depends on the rubric's authors.
- **Q5 (mixed-shape inputs).** *Deferred.* For inputs that are partially questions and partially other things, M3B-α applies both Path A (existing M3A judgment) and Path B (new formulation rubrics) and lets the disagreement diagnostic surface the mismatch. Whether the framework needs explicit input-type routing — beyond the per-rubric `target` configuration — is a question M3B-β can address with diversified-corpus data.

## What this design pass does not commit to

- It does not commit to a code patch. M3B-α is a follow-up planning + implementation pass scoped narrowly enough to be reviewable in the M3A-design-doc-plus-M3A-implementation pattern.
- It does not amend the M3A design reference. M3A remains accurate for what it ships.
- It does not amend the Constitution.
- It does not commit to the M3B-α corpus shape. The five existing M3A questions are sufficient for the H1 and H2 validation experiments; corpus diversification is M3B-β.

The deliverable of this pass is this document. The deliverable of M3B-α is the bridge made operational and the validation experiments that test whether it carries weight.
