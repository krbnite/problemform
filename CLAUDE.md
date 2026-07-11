# CLAUDE.md

> Read **AGENTS.md** first. It is the repository's shared contract for all coding
> agents. This file only documents Claude Code-specific behavior and conventions.

## Working in this repo with Claude Code

- **Planning.** When AGENTS.md calls for an implementation plan, use Claude Code
  Plan Mode to develop it and ExitPlanMode for review before implementation.
  Routine fixes and other work that do not require an implementation plan should
  proceed normally.
- **Reviews.** When available, use Claude Code review skills (e.g. /code-review, /security-review) to support the review workflow described in AGENTS.md.
- **Persistent repository memory.** Use Claude Code memory for durable user preferences and
  workflow preferences—not as a substitute for repository documentation.
  Repository facts, architecture, and project decisions belong in the
  authoritative docs referenced by AGENTS.md.
- **Subagents.** Use subagents when they reduce context usage or naturally separate
  work (e.g. implementation, review, documentation, experiments). Keep the
  authoritative decisions in the repository docs, not in subagent conversations.