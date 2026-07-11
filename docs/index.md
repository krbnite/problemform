# Documentation Index

This document is the curated entry point into the ProblemForm documentation.

It intentionally highlights the project's durable documentation structure rather than
listing every document in the repository. Historical plans and reports remain
available in their respective directories but are referenced here only as categories,
not as required reading.

---

# Start here

| Document | Purpose |
|---|---|
| [`../README.md`](../README.md) | User-facing overview of ProblemForm. |
| [`../AGENTS.md`](../AGENTS.md) | Shared operating contract for coding agents working in the repository. |

---

# Core project documentation

These documents define the project itself and should be treated as the primary
authoritative references.

| Document | Purpose |
|---|---|
| [`problemform_constitution.md`](problemform_constitution.md) | Authoritative behavioral specification ("what ProblemForm is"). |
| [`architecture.md`](architecture.md) | Overall architecture and workflow. |
| [`implementation.md`](implementation.md) | Maps the Constitution onto the implementation. |
| [`roadmap.md`](roadmap.md) | Current milestones, priorities, and implementation status. |
| [`cli_commands.md`](cli_commands.md) | CLI semantics and user-facing command reference. |
| [`glossary.md`](glossary.md) | Canonical terminology. |

---

# Reference documentation

Supporting documentation used during development.

| Document | Purpose |
|---|---|
| [`environment.md`](environment.md) | Development environment and setup. |
| [`dependencies.md`](dependencies.md) | Dependency management. |
| [`DOCUMENTS_METADATA.md`](DOCUMENTS_METADATA.md) | Documentation metadata conventions. |
| [`security.md`](security.md) | Security considerations and constraints. |
| [`backlog.md`](backlog.md) | Deferred ideas and future work. |

---

# Design references

Durable architectural and evaluation design documents live under:

- [`designs/`](designs/README.md)

Notable examples include:

- `problemform_scope`
- `milestone_03_evaluation_framework`
- `milestone_03b_rubrics_and_properties`
- `m3b_beta_corpus_diversification`

These documents describe *how the system should work*. They are amended in place as
the design evolves.

---

# Historical record

Implementation plans and validation reports form the project's engineering and
scientific history.

- [`plans/`](plans/README.md) — implementation plans and decision trails.
- [`reports/`](reports/) — validation studies, audits, and other dated findings.

These documents should generally be consulted for historical context, design
rationale, or experimental evidence rather than as the primary source of current
behavior.