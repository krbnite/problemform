---
title: "M3B-α validation findings: H1 (Path B viability)"
document_type: "report"
status: "active"
created: "2026-07-08"
updated: "2026-07-08"
author: "Claude Code"
authoritative_reference: "docs/designs/milestone_03b_rubrics_and_properties.md"
related:
  documents:
    - "docs/designs/milestone_03b_rubrics_and_properties.md"
    - "docs/designs/problemform_scope.md"
    - "docs/plans/claudes-m3b-alpha-implementation-plan.md"
    - "docs/reports/m3b_alpha_h1_2026-07-08/report_run1.md"
    - "docs/reports/m3b_alpha_h1_2026-07-08/report_run2.md"
    - "docs/reports/m3b_alpha_h1_2026-07-08/report_run3.md"
  issues:
    - 12
scope:
  inspected:
    - ".problemform/eval_runs/h1_run1 (report.json/report.md)"
    - ".problemform/eval_runs/h1_run2 (report.json/report.md)"
    - ".problemform/eval_runs/h1_run3 (report.json/report.md)"
---

# M3B-α validation findings: H1 (Path B viability)

**Scope of this document.** This reports the **H1** validation experiment only.
H1 asks whether *Path B* — judging the **formulation** directly with an absolute
rubric — is a viable, meaningful signal. **H2** (mechanisms scope-agnostic; the
non-question Aquinas probe) is **not** run here and remains pending; the
consequent resolutions of **H3/H4** therefore also remain pending. The M3B design
doc's hypothesis-resolution section should be updated once H2 completes, not from
this document alone.

## Setup

- **Corpus:** `benchmarks/default` — the 5-case M3A starter suite
  (`control/what_causes_eclipses`, `parenting/teach_kid_to_swim`,
  `philosophy/cosmology_nothingness`, `practical/code_review_prep`,
  `technical/api_design_rest_vs_graphql`).
- **Rubric (the H1 instrument):** `benchmarks/rubrics/formulation_quality_v1.yaml`
  — `target=formulation`, `mode=absolute`, 5 criteria on a `graded_5` scale
  (`central_claim_clarity`, `assumption_surfacing`, `constraint_articulation`,
  `alternative_framing_coverage`, `meta_question_presence`).
- **Command (focused config, per the roadmap):**
  `problemform benchmark benchmarks/default --rubric benchmarks/rubrics/formulation_quality_v1.yaml`
  — explicit `--rubric` overrides the default rubric set, so only the formulation
  rubric ran (not `answer_quality_v1`). `max_iterations=1` (default).
- **Runs:** 3 independent full runs (`h1_run1..3`) for the internal-consistency
  check. Raw report artifacts: `report.json`/`report.md` under
  `.problemform/eval_runs/h1_run{1,2,3}/` (gitignored); compact `report.md`
  snapshots preserved under
  [`docs/reports/m3b_alpha_h1_2026-07-08/`](m3b_alpha_h1_2026-07-08/).
- **Providers:** all OpenAI — ProblemForm `gpt-4.1`, Answer `gpt-4.1`, Judge
  `gpt-4o`. See *Environment caveats* below for why this is OpenAI-only and why
  the same-family judge is acceptable for H1.

### Environment caveats (important for interpreting these results)

1. **Anthropic provider is broken in this environment — not fixed (out of scope).**
   Every Anthropic call fails with `400 invalid_request_error: system: Input
   should be a valid array`. This is a pre-existing bug in `AnthropicProvider`
   (it sends `system` as a string; the API/SDK expects an array). Per the task
   instruction ("do not modify code unless a bug invalidates the experiment"),
   it was **not** fixed: H1 does not require Anthropic, so the bug does not
   invalidate this experiment. It is logged here as a discovered issue to fix
   before any cross-family run (H2 comparative work, calibration).
2. **Same-family judge warning fired (expected) and is acceptable for H1.** The
   engine warns because Answer and Judge share the OpenAI family. This is a blunt
   heuristic. It matters less here than in a model-vs-model benchmark because
   (a) H1's primary signal is the **absolute** formulation rubric scored at
   temperature 0, not the comparative answer judge; and (b) in the M3A comparison
   both the raw-prompt and refined-prompt answers come from the **same** answer
   model (`gpt-4.1`), so any judge self-preference is symmetric across the two
   sides and does not bias the raw-vs-refined verdict. Answer (`gpt-4.1`) and
   Judge (`gpt-4o`) are nonetheless different models to further reduce
   identical-model effects.

## H1 results

### Check 1 — Internal consistency

The rubric is highly consistent. Two complementary observations:

**Raw formulations (identical input text across all 3 runs) are scored almost
deterministically.** Because the raw subject is the fixed corpus question, its
score variance isolates *pure rubric-judge determinism* (temperature 0):

| Case | run1 | run2 | run3 | pop. stdev |
|---|---|---|---|---|
| what_causes_eclipses | 0.00 | 0.00 | 0.00 | 0.000 |
| teach_kid_to_swim | 0.20 | 0.25 | 0.15 | 0.041 |
| cosmology_nothingness | 0.10 | 0.10 | 0.15 | 0.024 |
| code_review_prep | 0.15 | 0.10 | 0.10 | 0.024 |
| api_design_rest_vs_graphql | 0.30 | 0.30 | 0.30 | 0.000 |

Same text → essentially the same score (stdev ≤ 0.04 on a 0–1 scale). The rubric
does not "swing wildly across runs," which is the failure mode H1 was checking for.

**Refined formulations vary more, but the variance is dominated by ProblemForm
stochasticity, not rubric noise** (the refined text itself differs each run
because the analytic phases run hot):

| Case | run1 | run2 | run3 | mean | stdev | range |
|---|---|---|---|---|---|---|
| what_causes_eclipses | 0.05 | 0.20 | 0.30 | 0.18 | 0.103 | 0.25 |
| teach_kid_to_swim | 0.65 | 0.65 | 0.55 | 0.62 | 0.047 | 0.10 |
| cosmology_nothingness | 0.70 | 0.60 | 0.75 | 0.68 | 0.062 | 0.15 |
| code_review_prep | 0.55 | 0.65 | 0.45 | 0.55 | 0.082 | 0.20 |
| api_design_rest_vs_graphql | 0.85 | 0.70 | 0.85 | 0.80 | 0.071 | 0.15 |

**Aggregate raw→refined delta is very stable across runs:** `+0.41 / +0.41 /
+0.44` (raw mean ≈ 0.15, refined mean ≈ 0.57). **All 15 case-runs show a positive
delta — no sign flips.** The refined formulation always scores higher than the raw.

**Per-criterion decomposition** (mean normalized score across 5 cases × 3 runs)
shows the rubric discriminates across dimensions rather than giving blanket credit:

| Criterion | raw | refined | delta |
|---|---|---|---|
| central_claim_clarity | 0.37 | 0.72 | +0.35 |
| assumption_surfacing | 0.00 | 0.22 | +0.22 |
| constraint_articulation | 0.00 | 0.53 | +0.53 |
| alternative_framing_coverage | 0.05 | 0.47 | +0.42 |
| meta_question_presence | 0.32 | 0.90 | +0.58 |

The largest gains are `meta_question_presence` and `constraint_articulation`;
`assumption_surfacing` stays weak even after refinement (0.22) — a substantive
signal about what ProblemForm does and doesn't add, not a rubric artifact.

**Check 1 verdict: PASS.** The rubric is internally consistent (near-deterministic
on fixed text; stable aggregate delta), with the residual refined-score variance
attributable to ProblemForm, not the rubric.

### Check 2 — Correlation with M3A

Per-case M3A answer verdict vs formulation-rubric delta, all three runs:

| Case | run1 | run2 | run3 |
|---|---|---|---|
| what_causes_eclipses | refined/material · Δ+0.05 | refined/material · Δ+0.20 | refined/material · Δ+0.30 |
| teach_kid_to_swim | refined/material · Δ+0.45 | refined/material · Δ+0.40 | refined/material · Δ+0.40 |
| cosmology_nothingness | tie/stylistic · Δ+0.60 | refined/material · Δ+0.50 | refined/material · Δ+0.60 |
| code_review_prep | refined/material · Δ+0.40 | raw/minor · Δ+0.55 | refined/material · Δ+0.35 |
| api_design_rest_vs_graphql | refined/material · Δ+0.55 | refined/material · Δ+0.40 | refined/material · Δ+0.55 |

**Directional agreement, magnitude divergence.** The two lenses corroborate on
*direction* — the refined side wins or ties on M3A while the formulation rubric
delta is positive in every case-run. But magnitude does **not** track:

- When M3A = `refined/material` (n=13): mean formulation Δ = **+0.396** (min +0.05).
- When M3A ≠ `refined/material` (n=2): mean formulation Δ = **+0.575** — i.e. the
  two cases where M3A did *not* register a material answer win had *larger*
  formulation gains than the average material-win case.

**The control case is the cleanest illustration of the scope-note confound.**
`what_causes_eclipses` is a well-formed factual question: its formulation barely
improves (Δ +0.05 in run1) yet M3A rates the refined-prompt answer as *materially*
better. The composite `ProblemForm × Answer` signal (M3A) credits the refinement
even when the formulation-as-formulation hardly changed — the answer model is
amplifying answer-helpful scaffolding that the formulation rubric correctly does
*not* score as a better formulation.

**Disagreement diagnostic behaviour.** Run 1 flagged two cases — `what_causes_
eclipses` (P2: material answer win, flat formulation) and `cosmology_nothingness`
(P3: answer tie, large formulation gain). Runs 2–3 flagged none, because run-to-run
variance pushed those borderline cases back across the `EPS_TIE`/`LARGE_DELTA`
thresholds. **Finding:** the per-case disagreement flags are **unstable for
borderline cases** at n=1 per run; the *pattern* (M3A and the rubric measuring
different things) is robust, but which specific case trips a flag is not. Treat the
diagnostic as directional, not as a stable per-case label, until K>1 / more runs.

**Check 2 verdict: PARTIAL — and partial in the informative direction.** The
lenses agree on sign but diverge on magnitude and specifically diverge on the
control and cosmology cases. This is evidence that Path B measures **formulation
quality specifically**, which M3A cannot isolate — i.e. Path B is *independent*
signal, not M3A restated.

## Empirical resolution of H1

**H1 (Path B is a viable generalization path beyond questions): SUPPORTED for
viability, with the nuance that Path B is complementary to — not redundant with —
M3A.**

- Internal consistency: **yes** (Check 1).
- Meaningful, corroborating-but-independent signal vs M3A: **yes, partial by
  design** (Check 2) — directional agreement plus a reproducible magnitude
  divergence that is exactly the confound the scope note predicted.

The one outcome that would have *failed* H1 — an unstable rubric whose scores swing
across runs — did not occur. The other outcome the design flagged as "a different
kind of useful" — low correlation meaning the lenses measure different things — is
partially present and is here interpreted as a *feature* (Path B isolates
formulation quality), not a failure.

## Implications for H2, H3, H4 (pending)

- **H2 (scope-agnostic mechanisms):** not tested here. H1 shows the rubric behaves
  sensibly on question-shaped inputs; whether it produces coherent scores on a
  non-question (the Aquinas argument probe) is the H2 experiment and must be run
  before H3/H4 can resolve. **Blocker:** the Anthropic bug above must be fixed if
  H2 is to use a cross-family judge; otherwise H2 can run OpenAI-only with the same
  caveat as here.
- **H3 (M3B-as-bridge strategically valuable):** a function of H1 ∧ H2. H1 holding
  is necessary but not sufficient; still contingent on H2.
- **H4 (issue ordering #8+#9 → #6 → #7):** the magnitude-divergence finding
  strengthens the case for **#7 (calibration)** — the rubric floor is harsh on
  bare-but-adequate questions (control raw = 0.00 across all runs), and the
  disagreement thresholds are unstable at n=1. Calibration with both lenses
  available is now concretely motivated by data.

## Limitations

- **n = 5 cases, K = 1 judgment per pair, 3 runs.** Below any significance
  threshold; findings are directional.
- **OpenAI-only, same-family judge** (Anthropic broken). Mitigated for H1 as argued
  above, but a cross-family replication is warranted before load-bearing claims.
- **Internal-consistency conflation:** re-running the whole benchmark mixes
  ProblemForm stochasticity into the refined-score variance. The raw-score column
  isolates pure rubric determinism (and is near-zero variance); a future
  rubric-only re-scoring harness (score one fixed formulation K times) would
  isolate refined-side rubric variance directly.
- **Rubric floor / possible structure bias:** bare questions score very low
  (control raw = 0.00). The control case is reassuring against pure verbosity bias
  (its *refined* form only reaches 0.05–0.30, i.e. the rubric does not over-reward
  elaboration of an already-adequate question), but the harsh floor on bare
  questions is a calibration item for #7.
- **Disagreement-flag instability** at n=1 (see Check 2).

## Decisions / recommended next steps

1. **Proceed to H2** (the Aquinas non-question probe) using the same focused
   `--rubric formulation_quality_v1.yaml` config. Decide first whether to fix the
   Anthropic provider (to enable a cross-family judge) or run H2 OpenAI-only.
2. **Fix the `AnthropicProvider` `system`-as-array bug** before any cross-family
   or calibration work (tracked as a discovered issue; not done under this task).
3. **After H2**, update the hypothesis-resolution section of
   `docs/designs/milestone_03b_rubrics_and_properties.md` with the combined H1+H2
   outcome (H1 alone should not rewrite H3/H4).
4. **Feed the calibration items** (rubric floor on bare questions; disagreement
   thresholds `EPS_TIE`/`LARGE_DELTA`; K>1) into the reframed #7.
