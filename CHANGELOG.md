# Changelog

All notable changes to this project will be documented in this file.

## [v0.2.0] — M3 Phase A: Evaluation Framework

### Added
- New `problemform benchmark` CLI command.
- New `problemform.eval` package.
- YAML benchmark corpus loader.
- Comparative answer-judging framework.
- Three-role evaluation architecture (ProblemForm / Answer / Judge).
- Position-randomized answer comparison.
- Materiality classification (`material`, `minor`, `stylistic_only`, `degradation`).
- JSON and Markdown benchmark reports.
- Starter benchmark corpus with five test cases.
- Control case (`what_causes_eclipses`) to reduce benchmark-selection bias.
- Design reference document for the evaluation framework.

### Changed
- Added PyYAML as a runtime dependency.
- Updated README with benchmark framework documentation.
- Added benchmark documentation to CLI docs.

### Reliability
- Failure containment during benchmark execution.
- Same-family judge bias warnings.
- Benchmark runs stored under `.problemform/eval_runs/`.

---

## [v0.1.2] — Reliability & Error Handling Improvements
### Added
- Structured provider error hierarchy:
  - StructuredOutputError
  - TruncatedResponseError
  - RefusalError
  - EmptyResponseError
  - ContentFilterError
- Friendly CLI handling for provider initialization failures.
- Friendly CLI handling for structured-output failures.
- Friendly CLI handling for file I/O and state-loading errors.
- Security documentation and deployment notes.
- Additional package metadata and project polish.

### Changed
- Hardened OpenAI and Anthropic provider response handling.
- Improved validation of structured LLM responses.
- Improved CLI error reporting and user-facing diagnostics.
- Improved state-file parsing and validation.
- Improved save, export, and checkpoint failure handling.
- Improved agent phase tracking and workflow diagnostics.
- Refined packaging configuration and distribution metadata.

### Documentation
- Expanded security and project documentation.
- Updated release and changelog documentation.

### Testing
- Added extensive CLI reliability tests covering:
  - malformed state files
  - unknown providers
  - missing SDKs
  - structured-output failures
  - file read/write failures
  - checkpoint failures
- Expanded provider and validation-path test coverage.

---

## [v0.1.1] - Post-MVP Hardening 
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