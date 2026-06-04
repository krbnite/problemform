# Implementation Details
This document describes how the concepts defined in the Constitution and Architecture documents map to software components and runtime behavior.

The implementation should remain faithful to the ProblemForm methodology while allowing flexibility in the choice of models, providers, tools, and orchestration frameworks.


## Core Concepts
ProblemForm is implemented as a stateful workflow.

Each stage receives a ProblemState object, contributes new information, and returns an updated ProblemState.

A stage may be implemented as a function, agent, workflow node, or other executable unit depending on the implementation architecture.

The workflow continues iteratively until the Convergence Evaluator determines that additional refinement is unlikely to materially improve the formulation.


## Conceptual Workflow
```
User Input
↓
ProblemState
↓
ProblemForm Phase Node
↓
Updated ProblemState
↓
ProblemForm Phase Node
↓
Updated ProblemState
↓
Convergence Evaluation
↓
Repeat or Complete
```


## Architecture Mapping

| Architecture Concept | Implementation |
|----------------------|----------------|
| Objective Analysis | Objective Analyst Node |
| Assumption Excavation | Assumption Excavator Node |
| Information Gaps | Information-Gap Detector Node |
| Expert Perspectives | Expert-Perspective Generator Node |
| Alternative Framings | Alternative-Framing Generator Node |
| Meta Questions | Meta-Question Generator Node |
| Refinement | Prompt/Question Synthesizer Node |
| Convergence Assessment | Convergence Evaluator Node |
| Shared State | ProblemState |

See [architecture.md](architecture.md) for more details on the architecture and agent roles.


## MVP Implementation

The MVP uses a single language model operating under the ProblemForm Constitution.

The architecture is simulated through structured prompting rather than true workflow orchestration.

Components:

- ProblemState
- Constitution Prompt
- Single LLM
- Convergence Check
- CLI Interface

See [roadmap.md](roadmap.md) for more details on the MVP and future milestones.


## Future Implementation
After MVP validation, ProblemForm can be evolved into a LangGraph-based implementation.

In this design:
- each phase becomes a workflow node
- ProblemState becomes the graph state
- convergence controls graph iteration
- specialized prompts may be assigned to individual nodes

See [roadmap.md](roadmap.md) for more details on the MVP and future milestones.