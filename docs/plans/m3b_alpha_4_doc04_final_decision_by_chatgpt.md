---
title: "M3B-α.4 implementation plan: final approval comments and decisions by ChatGPT"
document_type: "plan"
status: "proposed"
created: "2026-07-08"
updated: "2026-07-08"
author: 
    - Kevin Urban
    - ChatGPT
related:
  documents:
    - "docs/plans/m3b_alpha_4_doc01_plan_by_claude.md"
    - "docs/plans/m3b_alpha_4_doc02_plan_approval_comments_and_decisions_by_chatgpt.md"
    - "docs/plans/m3b_alpha_4_doc03_review_of_chatgpt_decision_by_codex55.md"
    - "docs/designs/milestone_03b_rubrics_and_properties.md"
    - "docs/designs/problemform_scope.md"
    - "docs/designs/milestone_03_evaluation_framework.md"
    - "claudes-m3b-alpha-implementation-plan.md"
  issues:
    - 12
comments:
    - "This is ChatGPT's final approval comments and decisions on Claude's implementation plan for M3B-α.4, including agreement with Codex's review."
---

Approved: use option B.

Activate existing `TestCase.expected_properties` as `target=formulation`, expected=True.

Please phrase the design-doc amendment carefully: the current corpus properties are predominantly formulation-shaped, though a few are mixed or answer-readable. For α.4, formulation-target activation is the cleaner default because it produces coherent signal on the current corpus and aligns with the M3B bridge goal.

Also note that artifact-target coverage is not lost because `artifact_baseline_v1` provides true artifact checks.

Please update the later cleanup queue to include:
- the M3B design doc amendment
- the stale `benchmarks/properties/README.md` language
- any backlog/property README wording that still implies `expected_properties` are artifact-target by default

Proceed with α.4 as planned.
