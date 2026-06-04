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
- commands like assess, refine, run
- JSON/Markdown output



## MVP++: Architecture Realization
Implement the full ProblemForm workflow architecture using graph-based orchestration while preserving the behavior validated during the MVP phase.

### Milestone 3: LangGraph Workflow
Implement the full ProblemForm architecture as an orchestrated graph of specialized agents operating on shared state.

- convert phase functions into graph nodes
- add looping convergence logic



## Platform Expansion
Extend ProblemForm beyond the command line and make it accessible to external users, applications, and agent ecosystems.

### Milestone 4: Streamlit UI
Create an interactive visual interface that makes the ProblemForm workflow accessible to non-technical users.

### Milestone 5: MCP Server
Expose ProblemForm as an MCP-compatible service that can be integrated into agent ecosystems and external applications.

## Productionization
Improve reliability, usability, security, observability, maintainability, and deployment readiness while preparing ProblemForm for real-world use.

### Milestone 6: Polish
Improve reliability, usability, security, observability, maintainability, and deployment readiness.

Particular emphasis should be placed on secure tool execution, sandboxing, least-privilege design, tool allowlists, and protection against prompt injection and unsafe agent behavior.

### Milestone 7: LangSmith / Observability (Optional)
Add tracing, evaluation, analytics, and observability capabilities to better understand and improve system behavior.