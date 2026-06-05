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


# Evaluation
## Comparative Judgment
A verdict by an independent judge model comparing two answers to the same question and deciding which one is better. Each judgment carries a winner (`raw`, `refined`, or `tie`) and a materiality rating.

## Materiality
The size and nature of the gap between two compared answers. Four-level scale used by the judge:

- **material** — the winning answer is meaningfully better in substance.
- **minor** — small but real improvement.
- **stylistic_only** — same substance, different presentation. Required when the verdict is a tie.
- **degradation** — the losing answer is substantively worse, not merely less polished. Reserved for cases where one answer would actively mislead or harm the reader relative to the other.

## Material-Improvement Rate
The fraction of completed benchmark cases where the refined-prompt answer won and the win was rated `material`. The headline "ProblemForm helped" signal. Denominator: completed cases only (errored cases are excluded).

## Degradation Rate
The fraction of completed benchmark cases where the judge marked the verdict `degradation`. In practice, this pairs with `winner_actual == "raw"` — the refined prompt produced an answer that is actively worse than the answer to the raw question. The headline regression signal. Denominator: completed cases only.

## Position Bias
A bias in pairwise judgment where the judge systematically prefers whichever answer is presented in a particular slot (e.g. "Answer A"). Mitigated by randomizing presentation order per comparison and recording which side was actually shown first.

## Self-Preference Bias
A bias in pairwise judgment where a judge model systematically prefers answers produced by a model from its own family. Mitigated by warning when the answer and judge providers share a family, and by recommending a different family for the judge.

## Control Case
A test case in a benchmark corpus where the system being measured is *not* expected to help — and may hurt. A well-formed factual question (`what_causes_eclipses`) is the shipped example: there is little room for ProblemForm to improve the prompt, and a real risk of bloating it with unnecessary clarification.

Control cases function as a structural guard: they prevent the corpus from drifting into a self-serving collection of cases the system is guaranteed to win. Any new benchmark suite should include at least one.

## Advocacy Artifact
A benchmark that exists to *promote* the system being benchmarked rather than to *measure* it. The failure mode is usually unintentional: when the people building the system also build its evaluation corpus, they tend to pick cases where the system is likely to look good, and the headline numbers end up describing the corpus selection more than the system's actual behavior. Control cases, three-way reporting (refined wins / raw wins / ties), and an explicit degradation rate exist to make this failure mode harder to slip into.

## Failure Containment
The benchmark-engine policy of capturing any exception during a case's pipeline (refinement, answer generation, or judging) into that case's `errors[]` and continuing the run, rather than aborting. Aggregate rates are computed over completed cases (`n_completed`), not attempted cases (`n_cases`), so a few intermittent failures cannot silently depress the win rate.