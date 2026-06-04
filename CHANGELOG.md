# Changelog

All notable changes to this project will be documented in this file.

## [v0.1.0] - MVP

### Added
- Complete multi-agent ProblemForm workflow
- Structured ProblemState implementation
- OpenAI provider support
- Anthropic provider support
- CLI commands:
  - analyze
  - assess
  - refine
  - run
  - explain
  - export
  - agent
- Workflow checkpointing and persistence
- Prompt synthesis engine
- Prompt history tracking
- Provider abstraction layer
- Workflow and CLI test suites

### Changed
- Redesigned convergence evaluation around prompt-delta materiality rather than refinement opportunities
- Reduced synthesis context size to significantly lower token usage and latency
- Improved CLI rendering of convergence results

### Notes
This is the first usable end-to-end release of ProblemForm.

---

## [v0.0.1-alpha] - Architecture Complete

### Added
- ProblemForm architecture specification
- Core terminology definitions
- Shared ProblemState design
- Agent definitions:
  - Objective Analyst
  - Assumption Excavator
  - Information-Gap Detector
  - Expert Panel Generator
  - Alternative Framing Generator
  - Meta-Question Generator
  - Convergence Judge
- Implementation roadmap
- Workflow design documentation

### Notes
This release captures the conceptual architecture and project design prior to full implementation.