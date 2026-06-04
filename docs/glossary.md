# Processes
## Objective Analysis
The process of analyzing the user's stated objective, inferring their true objective, and identifying any discrepancies between the two.

## Assumption Excavation
The process of uncovering and examining the underlying assumptions that inform the problem statement.


# Concepts
## Information Gap
Missing information, context, constraints, requirements, or success criteria that materially limit the quality of the problem formulation or the ability to evaluate potential solutions.

## Expert Panel
A collection of viewpoints, questions, concerns, and recommendations originating from multiple experts, stakeholders, disciplines, or perspectives.

Expert panels are used to broaden analysis, reveal blind spots, and identify considerations that may be overlooked by a single viewpoint.

## Alternative Framing
A different way of conceptualizing, interpreting, or presenting a problem. Alternative framings may reveal new objectives, assumptions, constraints, tradeoffs, or solution spaces that were not apparent in the original formulation.

## Meta Question
A question about the formulation, framing, assumptions, objectives, or context of the problem itself. Meta questions are intended to reveal what has not yet been asked and may significantly alter the direction of the refinement process.

## Convergence
The point at which the iterative refinement process reaches a stable formulation where further iterations are unlikely to materially improve the clarity, usefulness, completeness, or framing of the question, prompt, or problem statement.


# State
## Convergence Status
An assessment of whether additional refinement is likely to materially improve the formulation.

Possible values:
- Not Yet Converged
- Near Convergence
- Converged

These values represent the system's assessment of whether further refinement is likely to materially improve the formulation.


# Artifacts
## Prompt Version
A saved version of the evolving question, prompt, or problem formulation at a specific stage of refinement.

## Revision
A description of what changed between prompt versions and why the change was made.

## ProblemState
The shared state object that accumulates information throughout the iterative refinement process.

ProblemState serves as the system's working memory and is passed between phases as the problem formulation evolves.

Contains:
- objectives
- assumptions
- information gaps
- expert panel perspectives
- alternative framings
- meta questions
- revisions
- convergence status
- prompt versions

The exact structure may evolve as the implementation matures.