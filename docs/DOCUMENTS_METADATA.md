# Document Metadata Convention

## Purpose

This document defines the metadata standard for durable project documentation.

The goal is:

1. Consistent document lifecycle tracking.
2. Easier navigation between related artifacts.
3. Reduced ambiguity about whether a document is current, historical, superseded, or still under development.
4. Consistent behavior from AI contributors (Claude Code, Codex, ChatGPT, etc.).

This convention applies to durable Markdown documents stored under docs/.

It does not apply to:

- Temporary notes
- Scratch files
- External reference material copied into the repository
- Generated artifacts unless they are intended to become durable project documents

---

# Metadata Location

Metadata should be stored as YAML front matter at the top of the document.

Example:

yaml --- title: "ProblemForm Scope" document_type: "design" status: "active" created: "2026-06-05" updated: "2026-06-05" author: "Claude Code"  related:   documents:     - "docs/problemform_constitution.md"     - "docs/designs/milestone_03b_rubrics_and_properties.md"    issues:     - 12 --- 

---

# Required Fields

All durable documents should contain the following fields.

## title

Human-readable document title.

yaml title: "ProblemForm Scope" 

## document_type

One of:

yaml document_type: "reference" document_type: "design" document_type: "audit" document_type: "report" document_type: "plan" document_type: "decision" document_type: "guide" 

Choose the closest match.

## status

One of:

yaml status: "draft" status: "active" status: "superseded" status: "shelved" status: "archival" 

Definitions:

| Status | Meaning |
|----------|----------|
| draft | Work in progress. Not yet accepted as a project reference. |
| active | Current and relevant. |
| superseded | Replaced by a newer document. |
| shelved | Intentionally paused. May return later. |
| archival | Historical record only. |

## created

Date document was first created.

yaml created: "2026-06-05" 

## updated

Date document was last materially updated.

yaml updated: "2026-06-05" 

Minor typo fixes do not require updating this field.

## author

Document creator.

Examples:

yaml author: "Kevin" author: "Claude Code" author: "Codex" author: "ChatGPT" 

---

# Optional Fields

## authoritative_reference

Used when the document is grounded in a higher-level source.

Example:

yaml authoritative_reference: "docs/problemform_constitution.md" 

Common for audits, design reviews, and analyses.

## related

Used to connect the document to other artifacts.

Example:

yaml related:   documents:     - "docs/problemform_constitution.md"     - "docs/backlog.md"    issues:     - 12     - 15 

Only include direct relationships.

## scope

Used when the document examines a subset of the repository.

Example:

yaml scope:   inspected:     - "README.md"     - "CLAUDE.md"     - "problemform/eval/" 

Most useful for audits and reviews.

---

# Fields To Avoid

Do not add fields that duplicate information already represented elsewhere.

Avoid:

yaml active_document: shelved: files_created: implementation_changes: 

Reasons:

- Redundant with status
- Duplicates git history
- Encourages metadata drift

---

# AI Contributor Rules

When creating a new durable document:

1. Add YAML front matter.
2. Populate all required fields.
3. Add optional fields only when useful.

When materially editing an existing durable document:

1. Preserve existing metadata.
2. Update updated if the document meaningfully changes.
3. Update status if lifecycle changes.
4. Update related only if relationships actually change.

Do not invent metadata solely to satisfy the schema.

Metadata exists to improve project understanding, not to maximize metadata coverage.