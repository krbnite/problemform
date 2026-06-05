---
title: "Synthesis review: Codex constitution alignment audit"
document_type: "report"
status: "active"
created: "2026-06-05"
updated: "2026-06-05"
author: "Claude Code"
authoritative_reference: "docs/problemform_constitution.md"
related:
  documents:
    - "docs/reports/constitution_alignment_audit_2026-06-05.md"
    - "docs/designs/problemform_scope.md"
    - "docs/designs/milestone_03b_rubrics_and_properties.md"
    - "docs/backlog.md"
scope:
  inspected:
    - "docs/reports/constitution_alignment_audit_2026-06-05.md"
    - "docs/problemform_constitution.md"
    - "CLAUDE.md"
    - "docs/designs/problemform_scope.md"
    - "docs/designs/milestone_03b_rubrics_and_properties.md"
    - "docs/backlog.md"
    - "problemform/models.py"
    - "problemform/agents/"
    - "problemform/eval/"
---

# Synthesis review: Codex constitution alignment audit

## Purpose

This is a synthesis review of [`constitution_alignment_audit_2026-06-05.md`](constitution_alignment_audit_2026-06-05.md) (Codex), conducted to determine whether the audit changes the project's understanding of itself. It is not a critique of the audit's writing or completeness; it asks only whether the audit surfaces material new findings against the existing tracked artifacts.

Comparison authorities:

- `docs/problemform_constitution.md` — authoritative scope.
- `CLAUDE.md` — operational implementation summary.
- `docs/designs/problemform_scope.md` — working hypothesis on validated subset vs intended scope, the `ProblemForm × Answer Model` measurement confound, and M3B's potential role as bridge.
- `docs/designs/milestone_03b_rubrics_and_properties.md` — M3B design pass adopting the target axis as first-class.
- `docs/backlog.md` — tracked working hypotheses and design references.
- GitHub issues #1–#12, particularly #12 (M3B-α implementation).

Each Codex finding is classified using the four categories the user specified.

## Headline assessment

Codex's audit substantively agrees with the project's recent self-understanding. Roughly 70% of its observations and recommendations reproduce — sometimes in different vocabulary — what `problemform_scope.md`, the M3B design doc, and the backlog working-hypothesis entry already state. The audit functions well as a third-party corroboration of those artifacts.

It does, however, surface **three materially new findings** that are Constitution-grounded gaps the existing tracked artifacts do not address. Two of those warrant a future GitHub issue. One is real but premature to act on.

The audit also recommends substantial documentation propagation (README / CLAUDE.md / architecture.md / roadmap.md / cli_commands.md updates). The user has previously indicated README updates are off-limits until M3B-α actually exists. These propagations are classified as **Revisit later** rather than acted on now, consistent with the user's stated "minimize roadmap churn" principle.

## Materially new findings

### Finding 1 — The Constitution's visible Quality Assessment artifact has no implementation home

**Classification: Deserves a future issue.**

The Constitution's Phase 1 ("Question/Prompt Quality Assessment") explicitly requires the system to produce a visible assessment containing:

- A **Quality Rating** (Excellent / Good / Fair / Poor).
- A **Revision Recommendation** (Not Needed / Helpful / Strongly Recommended / Required).
- Explicit lists of important ambiguities or missing context, potentially flawed assumptions, unstated premises, framing effects, and missing alternatives.

`ProblemState` carries assumptions, information gaps, alternative framings, and meta-questions, but it has no `QualityRating`, no `RevisionRecommendation`, and no top-level "ambiguities" or "framing effects" fields. The `Objective Analysis` phase produces `objective_alignment` and `rationale` but does not summarize quality or recommend a revision class.

This is not captured in `problemform_scope.md` (which focuses on the eval-framework confound) or in `milestone_03b_rubrics_and_properties.md` (which focuses on the target axis for rubrics and properties). It is also not in any open backlog entry.

The gap is concrete, scoped, and Constitution-direct. It is a candidate for a focused implementation patch (add `QualityAssessment` model, extend objective analysis to populate it, render in `cli_render.py` and `report.md`).

Why future issue rather than now: the project's current priority is M3B-α. Opening this as a separate tracked issue avoids losing the finding while not interrupting M3B-α work. Sequencing is open — the quality assessment is orthogonal to M3B-α and could land at any time before or after.

### Finding 2 — The Constitution describes a human-in-the-loop process; the CLI is autonomous

**Classification: Revisit later.**

The Constitution treats problem formulation as a "collaborative effort between human intelligence (HI) and artificial intelligence (AI)." Several phases assume human participation:

- Phase 3 ("Information-Gathering Strategy") includes "follow-up questions to the user" as an explicit acquisition method.
- Phase 6 ("Iterative Refinement") names "human discussion" as an input.
- The Completion Criteria section says the process is complete when "both the AI and the user agree" — i.e., agreement is a precondition, not a unilateral AI judgment.

The current implementation is fully autonomous. `problemform run` loops the pipeline until the Convergence Judge declares CONVERGED or `--max-iterations` is hit, with no user-interaction surface mid-loop. No follow-up question is asked. No user agreement is solicited at completion.

This is a real Constitution gap. It is not currently captured in any tracked artifact.

Why revisit later rather than future issue: the autonomous design was an intentional MVP simplification. Acting on this would touch core orchestration (the `run_pipeline` loop), add new failure modes (paused state, resume semantics, partial-state persistence), and intersect with the planned Streamlit (M5) and MCP (M6) milestones where the natural surface for human-in-the-loop already lives. Opening a tracked issue now invites scope discussion before the framework can support it cleanly. Better to record the finding and let it inform M5 / M6 planning when those milestones arrive.

The note belongs somewhere durable, but not yet on the active queue.

### Finding 3 — Expert-directed rewrite fields are missing from AlternativeFraming and MetaQuestion

**Classification: Deserves a future issue.**

The Constitution's Phase 5 ("Perspective Expansion") gives parallel guidance for three artifact types — expert panel questions, alternative framings, and meta questions. For each, it says to:

1. Explain why it matters.
2. **Identify the expert, specialist, stakeholder, personality type, or perspective best suited to explore it.**
3. **Rewrite the question as if directed specifically to that expert.**

`ExpertPerspective` implements both: it has `perspective_name` and `question` fields, capturing the expert and the directed rewrite.

`AlternativeFraming` has `framing`, `rationale`, `difference_from_original`, `potential_value`. **No expert field, no directed rewrite.**

`MetaQuestion` has `question`, `rationale`, `potential_impact`. **No expert field, no directed rewrite.**

This is an implementation asymmetry. The Constitution gives all three artifact types the same field structure; the code gives only one of them the full structure. The asymmetry is not documented anywhere in the existing tracked artifacts.

The fix is scoped: extend `AlternativeFraming` and `MetaQuestion` with `perspective_name` and `directed_question` fields (or equivalent), update the corresponding agent prompts to populate them, update the dedup keys in `core/workflow.py`, update render and report. Backward-compatible if the new fields are optional.

Why future issue rather than now: this is genuinely orthogonal to M3B-α and to M3B-β. It's a Constitution-fidelity patch that can land any time. Worth tracking explicitly so it isn't lost.

## New but no action needed

These are real observations from Codex that don't constitute gaps requiring tracked work:

- **Naming refinement: "M3A answer-improvement rate" instead of unqualified "ProblemForm win rate."** Codex recommends not using the M3A win rate as the global "ProblemForm works" metric. Internally the project already treats the M3A signal as one lens among several (M3B will produce others). The renaming would be a minor cosmetic touch in future reports — easy to apply when those reports get written, not worth opening an issue.
- **"Plan a future ProblemState or eval schema migration from `raw_question` / `final_prompt` toward broader aliases such as `raw_input` / `final_formulation`."** The current `ProblemState` already has `raw_input` (not `raw_question`) at the top level. The `TestCase.raw_question` field is M3A-eval-specific. The recommendation is partially based on a misreading of where the vocabulary actually lives. The remaining drift is `final_prompt` — which is genuinely prompt-vocabulary — and is already noted in `problemform_scope.md` as part of the broader vocabulary migration. No new tracked work needed.

## Revisit later

These are real, but acting on them now would either churn the roadmap or precede the empirical evidence needed to act sensibly. They are noted here so they aren't lost.

### Documentation propagation pending M3B-α

Codex recommends:

- A "Validated subset vs intended scope" section in `README.md`.
- Describing the default benchmark as answer-outcome evaluation for question-shaped inputs in `README.md`.
- Changing "Final Prompt" language in `docs/architecture.md`.
- Splitting M3 into M3A and M3B in `docs/roadmap.md`.
- Adding M3B-as-bridge guidance to `CLAUDE.md`.
- Marking `benchmark` as a question-shaped evaluator in `docs/cli_commands.md`.

These are all reasonable and substantively correct. The user has explicitly said README updates are off-limits until M3B-α actually exists. Applying the same principle to the other most-read docs is consistent and avoids documentation churn before the working hypothesis is empirically validated. The right time for this propagation is **after M3B-α lands and its validation experiments produce evidence one way or another**. At that point a single documentation-propagation patch can update all five docs coherently with knowledge of what M3B-α actually found.

### Synthesizer / convergence vocabulary refactor

Codex recommends renaming "Prompt/Question Synthesizer" toward "Formulation Synthesizer" and revising convergence language so it judges the formulation's suitability for an intended audience rather than only whether an answerer would respond differently.

The vocabulary refactor is captured in `problemform_scope.md` as an open question for the broader scope decision. The convergence-revision proposal is more substantive — it would tie convergence to formulation quality (Path B) rather than to answer-distinguishability (current). This is exactly what the M3B-as-bridge hypothesis enables: once Path B exists and is validated, the convergence judge could consume it.

Why revisit later: the convergence-language change depends on M3B-α empirical results. If H1 (Path B viability) is confirmed and `formulation_quality_v1` rubric scores are stable, the convergence judge can plausibly consume them. If not, the convergence judge stays as-is. The decision is downstream of M3B-α validation.

### Architectural observations about input-type routing

Codex recommends adding `input_type` to test cases once non-question cases enter the corpus. The M3B design doc identifies the related question (Q5: does the framework need explicit input-type routing?) as deferred to M3B-β with diversified-corpus data informing the answer. No new action needed; the question is on the roadmap.

## Already substantively captured

Findings where Codex's observation reaches the same conclusion as an existing tracked artifact (these are listed for completeness; no per-finding action is needed):

- Validated subset vs intended scope as the central framing — `problemform_scope.md` and the backlog working-hypothesis entry already state this exactly.
- M3A measures `ProblemForm × Answer Model` (composite signal) — `problemform_scope.md` § "The confound: what is the benchmark actually measuring?" elevates this to a top-level section.
- The shipped corpus is all questions, including the control case — `problemform_scope.md` lists the five cases in a table.
- Non-question input types (arguments, beliefs, decisions, dilemmas, research ideas, ambiguous situations) — `problemform_scope.md` enumerates these in the Aquinas section.
- M3B-as-bridge as the right architectural direction — entirety of `milestone_03b_rubrics_and_properties.md` is designed around this.
- Target axis (`target=formulation` vs `target=artifact`) as first-class — M3B design doc adopts this in the "Target axis" section as a Decision.
- Three lenses kept visually separate, not synthesized into one score — M3B design doc explicitly says this in the composition section.
- Disagreement between M3A and formulation rubric is a diagnostic, not an error — M3B design doc has a dedicated "When rubric verdicts disagree with M3A verdicts" section that names exactly this.
- M3B-α before corpus diversification — M3B design doc's two-phase split.
- Preserve M3A's anti-advocacy mitigations (controls, degradation reporting, bias warnings) — already operative in M3A and called out in `docs/glossary.md`.
- Preserve the existing phase decomposition when adding broader terminology — already implicit in the M3B design doc's approach (no phase reorganization proposed).

## Recommendation summary

Materially new tracked work (Constitution gaps not currently captured):

| # | Finding | Classification |
|---|---|---|
| 1 | Visible Quality Assessment artifact missing | Deserves a future issue |
| 2 | Human-in-the-loop / collaborative-process gap | Revisit later (depends on M5 / M6) |
| 3 | Expert-directed rewrite fields missing from AlternativeFraming + MetaQuestion | Deserves a future issue |

Documentation propagation (deferred until M3B-α validation):

- A single coordinated docs-update patch covering README, CLAUDE.md, architecture.md, roadmap.md, and cli_commands.md, applied after M3B-α empirical results inform what should change and how. Doing this before M3B-α validates would churn the docs around a still-untested hypothesis.

No action required on most other Codex findings — Codex's audit substantively corroborates the existing scope and M3B design references rather than identifying new gaps.

## Process notes

- This review did not modify any tracked file. No GitHub issues were created or modified. No code was changed.
- The two findings flagged "Deserves a future issue" are recorded here but not opened. The user explicitly instructed no issue activity in this exercise.
- If at any point the user wants Findings 1 or 3 cut as issues, they can be opened with `gh issue create` against this document as the rationale source.
- Finding 2 should remain on the radar but not be opened as an issue until the Streamlit / MCP milestones (M5 / M6) are imminent or until a concrete user need emerges that the current autonomous design fails.
