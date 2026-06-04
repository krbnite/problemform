# Roadmap

## Minimum Viable Product (MVP)
Demonstrate that a single agent operating under the
ProblemForm Constitution can improve the formulation
of a user question through iterative refinement.

Components
- ProblemState
- Constitution Prompt
- Single LLM
- Convergence Check
- CLI Interface

Excluded
- Multi-agent orchestration
- LangGraph
- MCP
- Streamlit
- LangSmith
- External tools

### Milestone 1: Pure Python Core
Establish the foundational data structures, abstractions, and workflow logic required to support the ProblemForm methodology.

- ProblemState
- phase functions
- prompt templates
- provider abstraction
- one working end-to-end Python function

### Milestone 2: CLI
Provide a practical command-line interface that exposes ProblemForm functionality to users and developers.

- expose core workflow through Typer
- commands like analyze, synthesize, judge, run, agent
- JSON/Markdown output

### Milestone 3: Prompt Evaluation
Establish a rigorous evaluation framework for measuring whether ProblemForm actually improves question quality, prompt quality, and answer quality.

The goal of this milestone is to move beyond subjective impressions and create repeatable benchmarks that can quantify the value provided by the ProblemForm workflow.

Components:
* rubric-based prompt and answer evaluation
* comparative evaluation between raw and refined prompts
* curated golden test sets covering multiple domains
* expected properties and behavioral assertions
* answer-level quality comparisons
* evaluation CLI commands
* benchmark reporting and score aggregation

Example commands:
* problemform eval
* problemform benchmark

Success Criteria:
* ProblemForm can evaluate its own outputs against defined rubrics.
* Prompt refinements can be compared against baseline prompts.
* Answer quality improvements can be measured rather than assumed.
* Changes to prompts, agents, and workflow logic can be regression tested.
* Future architectural work (LangGraph, MCP, UI, etc.) can be evaluated against a stable benchmark suite.

-----------

## MVP++: Architecture Realization
Implement the full ProblemForm workflow architecture using graph-based orchestration while preserving the behavior validated during the MVP phase.

### Milestone 4: LangGraph Workflow
Implement the full ProblemForm architecture as an orchestrated graph of specialized agents operating on shared state.

- convert phase functions into graph nodes
- add looping convergence logic

-----------


## Platform Expansion
Extend ProblemForm beyond the command line and make it accessible to external users, applications, and agent ecosystems.

### Milestone 5: Streamlit UI
Create an interactive visual interface that makes the ProblemForm workflow accessible to non-technical users.

### Milestone 6: MCP Server
Expose ProblemForm as an MCP-compatible service that can be integrated into agent ecosystems and external applications.

## Productionization
Improve reliability, usability, security, observability, maintainability, and deployment readiness while preparing ProblemForm for real-world use.

### Milestone 7: Polish
Improve reliability, usability, security, observability, maintainability, and deployment readiness.

Particular emphasis should be placed on secure tool execution, sandboxing, least-privilege design, tool allowlists, and protection against prompt injection and unsafe agent behavior.

### Milestone 8: LangSmith / Observability (Optional)
Add tracing, evaluation, analytics, and observability capabilities to better understand and improve system behavior.