---
title: "docs/designs — purpose"
document_type: "guide"
status: "active"
created: "2026-07-09"
updated: "2026-07-09"
author: "Claude Code"
---

# `docs/designs/`

**Durable, authoritative design references.** These documents encode *design
intent* — how a part of the system is meant to behave and why — and are meant to
be consulted going forward. They are living documents: when a decision changes or
a hypothesis resolves, the relevant design doc is **updated in place** (with a
dated amendment), not replaced. `CLAUDE.md` points here for the reasoning that is
not captured in the code itself.

**What belongs here:** `document_type: design` (occasionally `reference`), normally
`status: active`. Architecture references, milestone design references, scope
notes.

**What does *not* belong here:**

- Time-bound implementation roadmaps and decision trails → [`../plans/`](../plans/).
- Empirical findings, validation results, and audits → [`../reports/`](../reports/).

Rule of thumb: if you'd re-read it to answer *"how is this supposed to work?"*, it's
a design. If it's a snapshot of *"what we decided to do at time T,"* it's a plan.
