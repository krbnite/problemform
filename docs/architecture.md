# Architecture Overview
The architecture of ProblemForm is designed to facilitate an iterative problem formulation and refinement process.

Its goal is not primarily to generate answers, but to develop the highest-quality formulation of a problem, objective, decision, inquiry, question, or prompt.

The core components include:

## Conceptual Workflow

```
Input
↓
Objective Analysis
↓
Assumption Excavation
↓
Information Gaps
↓
Expert Panel Perspectives
↓
Alternative Framings
↓
Meta Questions
↓
Refinement/Synthesis
↓
Convergence Assessment -> Objective Analysis (if not converged)
↓
Final Prompt (if converged)
```

## Shared State: ProblemState
Each phase corresponds to a node in a directed graph, where the `ProblemState` is passed along and updated at each step. The process continues iteratively until convergence is achieved, at which point a final prompt is generated.

For more details, see [problem_state.md](problem_state.md).


## Agent Roles & Responsibilities
Each phase is implemented by a specialized agent with a specific responsibility:

```text
User input
  ↓
Orchestrator Agent (The Conductor)
  ↓
Objective Analyst (The Detective - deciphers true objectives and intentions)
  ↓
Assumption Excavator (The Archaeologist - uncovers hidden assumptions)
  ↓
Information-Gap Detector (The Researcher - finds missing information)
  ↓
Expert-Panel Generator (The Consultant Group - identifies relevant experts and perspectives)
  ↓
Alternative-Framing Generator (The Lensmaker - changes the way the problem is viewed)
  ↓
Meta Question Generator (The Philosopher - questions the questions)
  ↓
Prompt/Question Synthesizer (The Writer - crafts the refined prompt)
  ↓
Convergence Evaluator (The Judge - assesses convergence) -> (if not converged, loop back to Objective Analyst)
  ↓
Final optimized prompt (if converged)
```