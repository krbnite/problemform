---
title: "M3B-α.4 implementation plan: approval comments and decisions"
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
    - "docs/designs/milestone_03b_rubrics_and_properties.md"
    - "docs/designs/problemform_scope.md"
    - "docs/designs/milestone_03_evaluation_framework.md"
    - "claudes-m3b-alpha-implementation-plan.md"
  issues:
    - 12
comments:
    - "This is ChatGPT's direction on Claude's implementation plan for M3B-α.4, including approval comments and decisions."
---

Approve α.4 plan with option B.

Activate existing `TestCase.expected_properties` as `target=formulation`, expected=True.

Rationale: the current corpus properties are formulation-shaped, not artifact-shaped. Activating them as artifact checks would produce incoherent property results. This is an implementation correction based on corpus reality, not a redesign.

Please document this as a small design-doc amendment/deviation:
- original plan said expected_properties activate as artifact checks
- corpus review showed they are formulation properties
- α.4 therefore activates them as formulation-target checks
- artifact-target property checks remain covered by `artifact_baseline_v1`

Proceed with the two-commit α.4 split:

1. α.4a engine + aggregation
2. α.4b report + CLI + defaults

Keep all other recommendations as written.