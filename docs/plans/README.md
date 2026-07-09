---
title: "docs/plans — purpose"
document_type: "guide"
status: "active"
created: "2026-07-09"
updated: "2026-07-09"
author: "Claude Code"
---

# `docs/plans/`

**Time-bound planning and decision-trail artifacts.** These documents capture
*"what we decided to do at time T"* — implementation roadmaps, phased plans, and
approval/review chains (including external-model reviews). They are provenance:
once the work lands, a plan is usually **frozen**, and `status: superseded` is the
normal end state, not a problem. Superseded plans **stay here** — the `status`
field marks them; there is no separate archive folder.

**What belongs here:** `document_type: plan`, with `status` typically `proposed`,
`approved`, or `superseded`.

**What does *not* belong here:**

- Durable "how the system should behave" design intent → [`../designs/`](../designs/).
  When a plan's decisions become the standing design, fold them into the relevant
  design doc rather than treating the plan as authoritative.
- Empirical findings, validation results, and audits → [`../reports/`](../reports/).

Rule of thumb: if it's a snapshot of *"what we decided to do at time T,"* it's a
plan. If you'd re-read it to answer *"how is this supposed to work?"*, it's a design.
