---
title: "M3B-beta H3 Validation Report Review by Codex"
document_type: "report"
status: "active"
created: "2026-07-11"
updated: "2026-07-11"
author: "Codex"
authoritative_reference: "docs/reports/m3b_beta_h3_2026-07-10.md"
related:
  documents:
    - "docs/reports/m3b_beta_h3_2026-07-10.md"
    - "docs/reports/m3b_beta_h3_2026-07-10/report.md"
    - "docs/designs/m3b_beta_corpus_diversification.md"
    - "docs/reports/m3b_alpha_validation_2026-07-08.md"
    - "docs/problemform_constitution.md"
scope:
  inspected:
    - "docs/reports/m3b_beta_h3_2026-07-10.md"
    - "docs/reports/m3b_beta_h3_2026-07-10/report.md"
    - ".problemform/eval_runs/h3/report.json"
    - ".problemform/eval_runs/h3/cases/"
    - "benchmarks/cases/"
    - "README.md"
    - "benchmarks/README.md"
    - "docs/designs/m3b_beta_corpus_diversification.md"
    - "docs/reports/m3b_alpha_validation_2026-07-08.md"
---

# M3B-beta H3 Validation Report Review by Codex

## Review Summary

I reviewed the H3 draft against `.problemform/eval_runs/h3/report.json`, the
generated `report.md`, the benchmark corpus, README/benchmark docs, beta design
doc, Constitution, and H1/H2 reports. This review evaluates the validation report
as a research/engineering artifact, not as an implementation close-out review.

The H3 result is substantively valid, but I would not accept the current draft
unchanged. The core result holds: the default evaluation lenses produced coherent,
discriminating, interpretable formulation-rubric results across all 11 formulation
types, and beta.1 answer-lens gating behaved correctly. The report needs a few
wording and data corrections before becoming permanent record.

## Must Fix Before Accepting H3

1. **The answer-quality contrast uses mixed denominators and is phrased too
   strongly.**

   `answer_quality_v1` in `report.json` has 13 raw answer evaluations but only
   12 refined answer evaluations because `online_bookstore_database` failed during
   refined-answer generation. The published aggregate is therefore unpaired:
   raw `0.815`, refined `0.758`, delta `-0.057`.

   On the 12 cases with both raw and refined answer scores, the paired
   answer-quality delta is still negative, but slightly smaller: raw `0.804`,
   refined `0.758`, delta `-0.046`.

   The central finding survives, but the report should say this explicitly. Also,
   "M3A answer comparison (13 answerable cases)" should be corrected to "13
   answer-applicable cases, 12 completed comparisons, 1 errored."

2. **The report should distinguish answer-rubric declines from M3A answer
   regressions.**

   The generated report shows 4 refined wins, 3 raw wins, 5 ties over 12 completed
   comparisons, with `0%` material improvement and `0%` degradation. The raw wins
   are minor. Phrases like "answer-side regressions" should be clarified as
   "answer-quality rubric declines" or "minor raw wins," not comparative
   degradations.

3. **"Close to a direct empirical validation" is overstated.**

   H3 supports the Constitution-aligned claim that the framework now measures
   formulation quality directly and that answer quality is not a sufficient proxy.
   It does not directly prove that ProblemForm "is optimizing formulation" in the
   strong empirical sense, nor that the rubric matches expert human judgment. That
   paragraph should be softened.

## Should Fix

- The beta.2/beta.4 recommendations are directionally right but slightly blurred.
  The evidence clearly supports a property-coverage gap. But per the beta design,
  beta.2 is mainly type-aware default selection/plumbing; authoring type-specific
  formulation property suites is beta.4 unless intentionally pulled forward.

- The report should acknowledge an alternative interpretation: the universal
  rubric may reward explicit scaffolding and constraint-listing that can
  over-formulate simple answerable tasks. `clean_my_bedroom`, `dragon_story`, and
  `code_review_prep` are useful evidence here. This does not invalidate H3, but it
  qualifies "generalizes" as "generalizes under this rubric."

- "Default configuration" should probably be "default evaluation configuration,"
  "default lenses," or "default policy." The run used explicit provider/model
  flags, even though it did not override rubrics, property suites, or
  answer-comparison policy.

## Nice Improvements

- The quantitative formulation tables, per-type deltas, per-criterion deltas,
  skipped-case counts, property-coverage claim, and representative examples all
  check out against the JSON.

- The Anthropic reliability claim is basically correct: I count 505
  rubric/property structured evaluations, or 517 including comparative judgments,
  with zero JSON-mode failures.

- The Secondary Findings section could be tightened; "answer quality is a weak
  proxy" and "answer-lens gating is justified" currently repeat similar evidence.

## Explicit Answers

1. **Does H3 successfully validate its stated hypothesis?**

   Yes, directionally. It validates coherent, discriminating, interpretable
   formulation evaluation across the full 24-case, 11-type corpus. It does not
   validate human-ground-truth correctness.

2. **Are the conclusions proportional to the evidence?**

   Mostly, but the central answer-quality and direct-validation language needs
   tempering.

3. **Does H3 represent a meaningful milestone beyond H1 and H2?**

   Yes. H1 tested questions, H2 tested one argument, and H3 tests the mixed
   canonical corpus plus beta.1 gating in one run.

4. **Would I approve this report as part of the project's permanent research
   record?**

   Yes, after the must-fix corrections above. As drafted, I approve the H3 result,
   but not freezing the current wording unchanged.

