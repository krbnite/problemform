# Changelog

All notable changes to this project will be documented in this file.


## [0.1.1] - Post-MVP Hardening 

### Added
- Provider response hardening for OpenAI and Anthropic.
- More comprehensive provider failure-mode tests.

### Changed
- Added dependency lower bounds for core packages.
- Agent command now updates ProblemState phase consistently with the main workflow.
- Added validation requiring --max-iterations >= 1.
- Updated installation documentation to use optional dependency extras.
- Refreshed CLI, environment, dependency, roadmap, and README documentation.

### Fixed
- Improved handling of truncated, refused, filtered, and empty provider responses.
- Removed duplicate agent documentation.
- Corrected outdated command references and module mappings.


## [v0.1.0] - MVP

### Added
- Multi-agent ProblemForm workflow
- Structured ProblemState implementation
- OpenAI provider support
- Anthropic provider support
- Workflow checkpointing and persistence
- Prompt synthesis engine
- Prompt history tracking
- Provider abstraction layer
- Agent-level CLI execution
- Workflow and CLI test suites

### Changed
- Redesigned convergence evaluation around prompt-delta materiality
- Reduced synthesis context size to lower token usage and latency

### Notes
First working end-to-end implementation of the ProblemForm architecture.

The MVP demonstrates:
- Multi-agent prompt refinement
- Iterative synthesis
- State persistence
- Convergence detection
- Provider abstraction

Future releases will focus on evaluation frameworks, benchmarking, workflow customization, and LangGraph integration.

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