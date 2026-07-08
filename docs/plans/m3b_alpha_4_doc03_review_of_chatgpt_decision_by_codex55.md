---
title: "M3B-α.4 implementation plan: codex review of ChatGPT approval decision"
document_type: "plan"
status: "proposed"
created: "2026-07-08"
updated: "2026-07-08"
author: 
    - Kevin Urban
    - Codex GPT-5.5
related:
  documents:
    - "docs/plans/m3b_alpha_4_doc01_plan_by_claude.md"
    - "docs/plans/m3b_alpha_4_doc02_plan_approval_comments_and_decisions_by_chatgpt.md"
    - "docs/designs/milestone_03b_rubrics_and_properties.md"
    - "docs/designs/problemform_scope.md"
    - "docs/designs/milestone_03_evaluation_framework.md"
    - "claudes-m3b-alpha-implementation-plan.md"
  issues:
    - 12
comments:
    - "This is Codex's review of ChatGPT's approval decision on Claude's implementation plan for M3B-α.4, including agreement and caveats."
---

I agree with the approval decision: α.4 should use option B and activate `TestCase.expected_properties` as `target=formulation`, `expected=True`.

The design doc is literal about `target=artifact` for these fields ([milestone_03b_rubrics_and_properties.md](docs/designs/milestone_03b_rubrics_and_properties.md#L199)), but the corpus itself is mostly about what the refined formulation should surface or preserve: “elicits the child’s age” ([teach_kid_to_swim.yaml](benchmarks/default/parenting/teach_kid_to_swim.yaml#L11)), “disambiguates the multiple meanings of ‘nothing’” ([cosmology_nothingness.yaml](benchmarks/default/philosophy/cosmology_nothingness.yaml#L12)), and “surfaces latent constraints” ([api_design_rest_vs_graphql.yaml](benchmarks/default/technical/api_design_rest_vs_graphql.yaml#L11)). Given the runner prompt changes its subject wording based on `target`, this is not cosmetic; artifact targeting would ask the judge about answer behavior, while formulation targeting asks about the prompt/formulation itself.

My one caveat: I’d phrase the deviation slightly less absolutely than “they are formulation properties.” A few strings are mixed or answer-readable, especially in the control case ([what_causes_eclipses.yaml](benchmarks/default/control/what_causes_eclipses.yaml#L11)). But as an α.4 integration decision, formulation is still the better default because it produces the cleaner signal and aligns with the M3B bridge goal of first-class formulation evaluation.

I also agree with documenting this as an explicit design-doc amendment/deviation, and I’d include the property README/backlog in that cleanup later since they repeat the old artifact-default language. Artifact-target coverage is not lost because `artifact_baseline_v1` already provides true artifact checks ([artifact_baseline_v1.yaml](benchmarks/properties/artifact_baseline_v1.yaml#L1)).