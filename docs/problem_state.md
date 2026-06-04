# ProblemState
ProblemState serves as the system's working memory and accumulates information throughout the iterative refinement process.

It contains:
```
raw_input
stated_objective
inferred_objective
assumptions
information_gaps
expert_panel_perspectives
alternative_framings
meta_questions
revisions
prompt_versions
convergence_status
final_prompt
```

ProblemState tracks both prompt versions and revisions so that the evolution of a formulation can be inspected, audited, and replayed.

Each phase receives a ProblemState, contributes new information, and returns an updated ProblemState.

In graph-based implementations, phases may be represented as workflow nodes.

```
ProblemState in
↓
Phase 
↓
ProblemState out
```