---
title: "M3B-β design: corpus diversification and formulation-type generalization"
document_type: "design"
status: "draft"
created: "2026-07-09"
updated: "2026-07-10"
author: "Claude Code"
authoritative_reference: "docs/problemform_constitution.md"
related:
  documents:
    - "docs/problemform_constitution.md"
    - "docs/designs/problemform_scope.md"
    - "docs/designs/milestone_03b_rubrics_and_properties.md"
    - "docs/reports/m3b_alpha_validation_2026-07-08.md"
    - "docs/backlog.md"
  issues:
    - 6
    - 7
scope:
  inspected:
    - "problemform/eval/models.py"
    - "problemform/eval/engine.py"
    - "problemform/eval/corpus.py"
    - "problemform/eval/report.py"
    - "problemform/eval/defaults.py"
    - "problemform/eval/rubric_runner.py"
    - "problemform/eval/property_runner.py"
    - "problemform/eval/prompts/comparative_judge.py"
    - "problemform/cli.py (benchmark command)"
    - "benchmarks/ (11 type dirs + rubrics/properties)"
    - "benchmarks/README.md"
    - "README.md (formulation-types table)"
---

# M3B-β design: corpus diversification and formulation-type generalization

**Status: draft design proposal.** This is a design reference with a roadmap
section, *not* an implementation plan. It proposes how the evaluation framework
should evolve now that the corpus spans many formulation types. It commits no code
and defers concrete patches to a later per-phase implementation pass (β.0–β.n),
mirroring the α.1–α.4 discipline.

## Context

M3B-α shipped the evaluation framework's **target axis** (`formulation` vs
`artifact`), three parallel lenses (comparative answer judgment, absolute rubrics,
property checks), and validated the formulation rubric on questions (**H1**) and a
single argument (**H2**). H2 is the load-bearing result for this document: the
formulation rubric produced coherent, discriminating scores on a *non-question*
input, while the M3A answer comparison was meaningless there and had to be ignored.

Since then the corpus has expanded from questions-only to **11 formulation types**,
one directory each under `benchmarks/`:

| Type | Dir | Cases |
|---|---|---|
| Question | `default/` | 5 |
| Argument | `arguments/` | 1 |
| Belief | `beliefs/` | 2 |
| Decision | `decisions/` | 2 |
| Dilemma | `dilemmas/` | 2 |
| Explanation | `explanations/` | 2 |
| Goal | `goals/` | 2 |
| Instruction | `instructions/` | 2 |
| Plan | `plans/` | 2 |
| Prompt | `prompts/` | 2 |
| Specification | `specifications/` | 2 |

The README "What kinds of things can ProblemForm refine?" table already specifies,
per type, *what refinement should look like* and *why the type is worth testing* —
that table is a primary design input for this document (it is the seed for
type-specific evaluation criteria in Q4).

This is an **evaluation-layer** design (M3B). Where the refinement pipeline itself
(M1/M2) carries question-centric assumptions, this document flags them but does not
propose to rewrite the pipeline — H2 is empirical evidence that the pipeline already
produces usable formulations for at least one non-question type.

---

## Q1 — What new capabilities emerge from supporting multiple formulation types?

Supporting many types is not "more test cases"; it changes what the framework can
*measure*:

1. **Evaluation of inputs that have no natural answer.** Arguments, beliefs,
   dilemmas, goals, and specifications have no single downstream "answer" to
   compare. The formulation rubric (Path B) is the only lens that applies to them.
   The corpus makes this the common case rather than an exception — the framework
   graduates from "did the answer improve?" to "did the *formulation* improve?",
   which is what the Constitution says ProblemForm optimizes.
2. **Per-type quality profiles.** Because criteria like `assumption_surfacing`,
   `constraint_articulation`, and `meta_question_presence` are scored per case, the
   framework can report *where* ProblemForm helps by type — e.g. large
   central-claim gains on arguments, constraint gains on decisions/specifications,
   success-criteria gains on goals. This is new, actionable signal.
3. **Type-appropriate expectations.** The README table encodes different success
   conditions per type (arguments: make premises/inference explicit; decisions:
   expose tradeoffs and criteria; dilemmas: surface competing values without
   collapsing them). Multiple types let the framework check *type-appropriate*
   refinement rather than a single notion of "better".
4. **Regression guarding against question-only drift.** Standing non-question cases
   (starting with the Aquinas argument) make it structurally hard for future changes
   to quietly re-specialize ProblemForm to questions — the same role the control
   case plays against advocacy drift.
5. **A measurable "does ProblemForm help on type X?" per type.** With enough cases
   per type, the refined−raw formulation delta becomes a per-type effect size,
   turning a qualitative claim ("we generalize") into a measured one.
6. **Foundation for comparative-formulation evaluation.** Once inputs without
   answers are first-class, the natural head-to-head lens is *raw formulation vs
   refined formulation* (comparative-mode rubrics, deferred from α) rather than
   answer-vs-answer — see Q5/β.3.

---

## Q2 — What generalizes cleanly, and what is still implicitly question-centric?

### Generalizes cleanly (keep as-is)

- **The `target` axis** (`formulation` | `artifact`). The core abstraction already
  separates "score the formulation" from "score the answer". Non-questions simply
  use the `formulation` half.
- **`formulation_quality_v1`** — its criteria were authored input-agnostically and
  H1/H2 confirmed they produce coherent scores on both questions and an argument.
- **`rubric_runner` / `property_runner`** — they operate on `(subject_text,
  subject_label, target)` and are indifferent to input type.
- **The corpus loader** (`load_test_cases`, recursive) and the `raw_formulation`
  field (just renamed from `raw_question`).
- **Three-parallel-lens aggregation** — rubrics and properties aggregate per lens,
  never merged into one score. This discipline is exactly what a multi-type world
  needs (the answer lens can be absent without disturbing the others).

### Still implicitly question-centric (the debt this design must resolve)

1. **The M3A answer comparison always runs and cannot be skipped.**
   `engine._run_one_case` unconditionally generates `raw_answer` / `refined_answer`
   and runs `judge_answers`; `comparative_judge.py` is literally the "Comparative
   **Answer** Judge" deciding "which of two **answers** to a user's **question** is
   better," with a `{question}` placeholder. For a belief or dilemma there is no
   natural answer — H2 showed the verdict is noise (it returned `tie` and we ignored
   it), yet the run still pays for two answer generations + a judge call and records
   a meaningless verdict. **This is the single most question-centric assumption.**
2. **Answer-side defaults load for every run.** Default loading pulls
   `answer_quality_v1` (`target=artifact`) and `artifact_baseline_v1`
   (`target=artifact`), which evaluate the meaningless "answer" for non-answerable
   inputs. (H2 side-stepped this by pointing `--property-suite` at an empty dir.)
3. **The report headline is answer-comparison-primary.** The Markdown headline is
   refined-win / raw-win / tie / material-improvement / degradation — all
   answer-comparison metrics. For a non-question run these are the most prominent
   numbers and they are noise; the formulation-rubric section is secondary.
4. **The disagreement diagnostic keys off the M3A verdict.** It compares the
   answer verdict against the formulation delta — meaningful only when the answer
   verdict is meaningful (questions and other answerable types).
5. **`category` is overloaded.** It is the *formulation type* for new cases
   (`argument`, `decision`, …) but a *topic/domain* for the legacy suite
   (`philosophy`, `technical`, `parenting`, `control`). `benchmarks/README.md` still
   documents it as an advisory "reporting grouping" and describes the input as "the
   user's original **question**." There is no controlled vocabulary — it is a bare
   `str`. Type and topic are two different axes now conflated in one field.
6. **Prompt-centric vocabulary residue.** `TestCaseResult.raw_prompt` /
   `refined_prompt`, and (in the M1/M2 core) `final_prompt` / `prompt_versions`,
   still say "prompt". The `raw_question → raw_formulation` rename was the first step
   of the migration the 2026-06-05 constitution audit recommended; the rest is open.
7. **Corpus docs and the schema example still say "question".** `benchmarks/README.md`
   presents the schema with `raw_formulation: > The user's original question`.

### Out of M3B scope but worth flagging

The refinement agents' prompts (Objective Analysis, Meta-Question Generation, etc.)
may contain "question" wording. H2 shows the pipeline nonetheless produces good
non-question formulations, so this is latent, not blocking. Track it against the
broader vocabulary migration, not β.

---

## Q3 — Should formulation type stay a corpus concept, or become first-class at runtime?

Three positions on a spectrum:

- **(A) Status quo — free-text corpus label.** `category` stays advisory metadata;
  the engine ignores it. *Rejected:* it cannot fix debt #1 (the engine must decide,
  per case, whether the answer lens is meaningful), so it leaves the framework
  producing noise metrics for most of the corpus.
- **(B) Controlled vocabulary, still metadata-only.** A `FormulationType` Literal,
  validated, but the engine still runs every lens. *Insufficient:* validation is
  nice, but without runtime effect the answer-lens problem persists.
- **(C) First-class runtime concept.** Type drives engine behavior (which lenses
  run) and reporting.

**Recommendation: (C), but minimal and data-driven.** Promote formulation type to a
first-class *runtime* concept, expressed as **data/config, not pervasive branching**:

- Add a controlled **`formulation_type`** field (a `Literal` of the 11 types, open
  to extension) on `TestCase`, **distinct from `category`** (see Q7 — `category`
  becomes topic/domain or is retired).
- Introduce a small **type → evaluation-policy registry** (a dict/table, mirroring
  the existing `PHASE_DEFAULT_TEMPERATURES` and `defaults.py` patterns) that answers,
  per type: *(a) does the answer-comparison lens apply?* and *(b) which default
  rubric(s) and property suite(s) apply?*
- The engine consults the registry to gate the answer lens and select defaults; the
  report renders only the lenses that ran. No per-type `if/elif` sprawl — one lookup.

H2 makes this hard to ignore: making non-question runs meaningful requires the
engine to be type-aware at least enough to gate the answer lens. Once we cross that
line, a tiny explicit registry is the honest home for the policy — and it
generalizes to Q4 (per-type defaults) for free.

**Constraint:** type must remain *advisory and overridable*, never a gate that
blocks a run. A user can always force any lens with the existing `--rubric` /
`--property-suite` flags (and a proposed `--[no-]answer-comparison`). The registry
sets *defaults*, not *restrictions* — consistent with the corpus philosophy that the
user owns their content.

---

## Q4 — Should different types eventually use different default rubrics / property suites?

**Yes — but layered, not bespoke-per-type from day one.**

- **Keep `formulation_quality_v1` as the universal baseline.** H1/H2 show its
  criteria (`central_claim_clarity`, `assumption_surfacing`,
  `constraint_articulation`, `alternative_framing_coverage`, `meta_question_presence`)
  carry signal across a question corpus and an argument. It should apply to *every*
  type so cross-type comparison stays on one common instrument.
- **Add optional per-type rubrics/property suites, selected via the registry.** The
  README table already sketches type-specific success conditions that map to
  criteria, e.g.:
  - *Argument* → `premise_explicitness`, `inference_validity_surfaced`,
    `conclusion_clarity`, `position_preserved`.
  - *Decision* → `options_enumerated`, `tradeoffs_surfaced`, `decision_criteria_named`,
    `constraints_identified`.
  - *Dilemma* → `competing_values_named`, `stakeholders_identified`,
    `no_premature_collapse`.
  - *Goal* → `success_criteria`, `constraints_and_priorities`, `dependencies_timeline`.
  - *Specification* → `requirements_vs_implementation_separated`, `edge_cases`,
    `ambiguities_surfaced`.
  These are **additive** — a type gets the universal rubric *plus* its optional
  type rubric. Property suites work the same way (per-type formulation property
  suites under `benchmarks/properties/<type>/`).
- **Answer-side defaults become answerable-only.** `answer_quality_v1` and
  `artifact_baseline_v1` map (in the registry) to types with a natural answer
  (questions, and arguably instructions/prompts/explanations), and are omitted for
  the rest. This directly resolves debt #2.

**Avoid** authoring 11 bespoke rubrics up front. Ship the universal baseline + the
registry hook, then add per-type rubrics incrementally as evidence accrues
(β.4), keeping the universal lens as the comparability backbone.

---

## Q5 — Roadmap for M3B-β (small, α-style phases)

Ordered so each phase is independently reviewable and lands value. Essential vs.
optional is called out per phase (and summarized in Q6).

### β.0 — Naming & debt pre-work · **ESSENTIAL**
Non-behavioral groundwork that everything else builds on. Add the `formulation_type`
controlled vocabulary to `TestCase`; decide `category`'s fate (topic/domain vs
retire); backfill `formulation_type` on all corpus cases; fix the corpus README /
schema "question" wording; dedupe cross-suite case names; decide the scope of the
`prompt → formulation` field migration (`raw_prompt`/`refined_prompt`/`final_prompt`)
and whether to rename the question suite `default/ → questions/` (since done — see §Q7
resolution). Land as data/docs + model-field additions with backward-compatible defaults.

### β.1 — Type-awareness + answer-lens gating · **ESSENTIAL**
Introduce the type → evaluation-policy registry (`eval/policy.py` or extend
`defaults.py`). Gate the M3A answer comparison: skip answer generation + comparative
judgment for non-answerable types (registry-driven), with a `--[no-]answer-comparison`
override. Make the report **degrade gracefully** — when the answer lens didn't run,
suppress/annotate the answer headline instead of showing noise, and lead with the
formulation-rubric section. This is the phase that makes non-question runs honest.

### β.2 — Type-aware default rubric/property selection · **ESSENTIAL**
Registry selects default rubrics/property suites by type: universal
`formulation_quality_v1` for all; answer-side defaults for answerable types only;
optional per-type slots wired but possibly empty. `--rubric` / `--property-suite`
still override. Report groups results by type where a run spans multiple types.

### β.3 — Comparative-mode rubrics + position randomization · **ESSENTIAL (completes the α framework)**
Implement `ComparativeRubricEvaluation` (sketched in the α design doc, explicitly
deferred). Head-to-head *raw formulation vs refined formulation* judging, reusing the
M3A position-randomization pattern. This is the natural comparative lens for inputs
with no answer, and finishes the rubric framework α started.

### β.4 — Type-specific rubrics & property suites · **PARTLY OPTIONAL**
Author type rubrics/property suites incrementally, seeded from the README table
(argument/decision/dilemma/goal/specification first, where the criteria are
clearest). Validate each against its corpus slice before shipping as a default.
Optional in that the universal baseline already produces signal; each type rubric is
an additive refinement, prioritized by evidence.

### β.5 — Calibration & robustness · **OPTIONAL / research**
The reframed #7: rubric calibration (the harsh floor on bare-but-adequate inputs;
disagreement thresholds), K>1 multi-judge aggregation, cross-type meta-analysis
(effect size by type), and dev/held-out splits. Research-grade; pursue once β.1–β.3
give a stable multi-type surface to calibrate against.

### Cross-cutting validation
As each phase lands, run the diversified corpus (per-type) with a cross-family judge
(now possible — the Anthropic provider is fixed) and record findings in
`docs/reports/`, outcome-neutral, as with H1/H2.

---

## Q6 — Essential vs. optional

**Essential (β is not meaningfully "done" without these):**
- **β.0** naming/debt pre-work — unblocks everything and stops `category` conflation.
- **β.1** answer-lens gating + type-awareness — without it, most of the corpus
  produces noise metrics; this is the core correctness fix H2 exposed.
- **β.2** type-aware defaults — makes "run the whole diversified corpus" meaningful.
- **β.3** comparative-mode rubrics — completes the rubric framework α deferred and is
  the natural lens for answer-less inputs.

**Optional / research (valuable, incremental, evidence-gated):**
- **β.4** bespoke per-type rubrics/property suites (beyond the universal baseline).
- **β.5** calibration, K>1, cross-type meta-analysis, held-out splits.
- A dedicated "formulation-comparative judge" prompt variant, if β.3 shows the
  answer-judge wording doesn't transfer.

Principle: essential items make the *existing* lenses honest and complete across
types; optional items add *new* per-type sophistication. Ship honesty before
sophistication.

---

## Q7 — Technical debt / naming to address before β implementation

Ordered by how much they block clean β work:

1. **Answer-lens always-runs (blocking).** Must become gate-able by type (β.1). This
   is both debt and the central β feature.
2. **`category` overload (blocking β.0).** Split the two axes: a controlled
   `formulation_type` (what kind of input) vs an optional `category`/`topic`
   (subject domain). Decide whether the legacy `philosophy`/`technical`/… values
   migrate to `topic` or are dropped. Nothing should infer *type* from the current
   free-text `category`.
3. **Judge-prompt wording.** `comparative_judge.py` is answer/question-specific. Fine
   for answerable types; for β.3's formulation-comparative lens it needs a variant
   that talks about *formulations*, not *answers to a question*.
4. **Prompt→formulation vocabulary residue.** `raw_prompt` / `refined_prompt`
   (eval) and `final_prompt` / `prompt_versions` (core). Decide migration scope in
   β.0. Eval-layer renames are cheap and in-scope; core renames are a larger,
   separate migration (and touch `ProblemState`), so likely deferred with a tracked
   note rather than done inside β.
5. **Report headline assumes an answer.** Needs graceful degradation when the answer
   lens is absent (β.1).
6. **Corpus README / schema still say "question".** Update to type-neutral language
   and document `formulation_type` (β.0).
7. **Question-suite directory naming (`default/` → `questions/`).** Rename for taxonomic
   consistency with the type dirs (deferred cleanup; fits β.0). Touches tests/docs/report refs.
   > **Resolved (2026-07-10):** done as part of the benchmarks reorganization — the
   > canonical corpus now lives under `benchmarks/cases/` (with `default/` → `questions/`),
   > and `rubrics/` / `properties/` are siblings, so `benchmark benchmarks/cases`
   > runs exactly the canonical corpus.
8. **Duplicate case names across suites** (`what_should_i_do_tomorrow`,
   `cosmology_nothingness`). Namespace or rename in β.0 so per-name aggregation is
   unambiguous.

---

## Constitution alignment & non-goals

- **Keep the three lenses parallel; never synthesize one overall score.** Diversity
  increases the temptation to produce a single "formulation quality number" per type;
  the α discipline (separate aggregates) holds — a type simply has fewer applicable
  lenses.
- **Path B does not claim authority prematurely.** The formulation rubric becomes the
  *primary* lens for non-answerable types by necessity, but it remains an early
  measurement instrument; per-type calibration (β.5) precedes any strong claims.
- **The user owns the corpus.** Type drives *defaults*, never restrictions; every
  policy is overridable by flag.
- **No pipeline rewrite in M3B.** Question-centric refinement-prompt wording is
  flagged, not fixed, here.

## Open questions for the implementation pass

1. **Is `formulation_type` a closed `Literal` or an open registry key?** Lean open
   (unknown types fall back to a "generic formulation" policy) so corpus growth
   doesn't require code changes.
2. **Does `category` survive as `topic`, or is it retired?** Affects legacy suite
   metadata and report groupings.
3. **Scope of the prompt→formulation rename** — eval-only in β.0, or include the
   core `ProblemState` fields (larger, cross-cutting)?
4. **Answerable-type boundary.** Questions clearly have answers; do
   instructions/prompts/explanations count as "answerable" (artifact = the executed
   output) for the answer lens and answer-side rubrics? This sets the registry's
   answer-lens column.
   > **Resolved (M3B-β.1, 2026-07-10).** Criterion: a type is *answerable* when the
   > refinement naturally induces a downstream response/artifact **whose quality we
   > care about**. **Answerable:** `question`, `explanation`, `instruction`, `prompt`,
   > **`specification`**. **Formulation-only:** `argument`, `belief`, `decision`,
   > `dilemma`, `goal`, `plan`. `unspecified`/unknown → answerable (legacy);
   > overridable via `--[no-]answer-comparison`. This is the authoritative policy,
   > encoded in `problemform/eval/policy.py` and
   > `docs/plans/m3b_beta_1_plan_by_claude.md`. **Note:** it supersedes the earlier
   > wording in this document (e.g. §Q2/Q4) that grouped `specification` among inputs
   > "without a natural downstream answer" — β.1 intentionally treats a specification
   > as answerable (the induced implementation is the artifact whose quality matters).
5. **Multi-type run reporting.** When one `benchmark` run spans several types, is the
   report per-type-sectioned, or one flat report with a type column? (Leaning
   per-type sections.)
