# ProblemForm Milestone 1-2 Sprint Summary

## Overview

This sprint began after the core agent prompts had largely stabilized and shifted focus from prompt engineering into architecture, workflow design, convergence behavior, performance, and usability.

The major outcome of the sprint was transforming ProblemForm from a collection of refinement agents into a functioning iterative refinement system that:

- Supports multiple LLM providers through a common abstraction
- Tracks prompt history across refinement iterations
- Converges reliably
- Runs dramatically faster than earlier versions
- Produces more stable refinement behavior
- Provides a foundation for future experimentation and evaluation

---

# 1. Agent Prompt Stabilization

The first phase of the sprint focused on refining several agent prompts.

## Expert Panel Generator

The Expert Panel Generator evolved toward a clear role:

- Generate perspectives, not answers
- Generate perspectives, not alternative framings
- Generate perspectives, not information gaps

Several iterations clarified distinctions between:

- experts
- stakeholders
- adversarial perspectives
- contrarian perspectives
- end users
- decision makers

The final version emphasized:

- information gain
- diversity of perspectives
- non-redundancy
- valuable dissent

and introduced:

json {   "perspective_type": "...",   "perspective_name": "...",   ... } 

to separate general category from specific perspective.

---

## Alternative Framing Generator

The Alternative Framing Generator required significant refinement.

The central challenge was preventing it from merely generating:

> "What would another expert ask?"

instead of:

> "How might the problem itself be reformulated?"

The final version focused on:

- alternative objectives
- alternative constraints
- alternative success criteria
- broader/narrower formulations
- contrarian formulations
- causal assumptions
- decision criteria

while explicitly prohibiting:

- solutions
- expert perspectives
- restatements

This became one of the strongest agents in the system.

---

## Meta Question Generator

The Meta Question Generator was refined repeatedly to distinguish it from:

- assumption excavation
- information gap detection
- expert panel generation

The major conceptual breakthrough was recognizing that:

> Information gaps ask for missing facts.

while

> Meta questions ask whether the inquiry itself is structured correctly.

This led to additions such as:

- whether the question needs to be asked at all
- whether the decision needs to be made now
- whether inaction is a viable alternative
- whether hidden assumptions about the inquiry itself remain unexamined

---

## Convergence Judge

Initially:

python You are the Convergence Judge.  Determine: - Not Yet Converged - Near Convergence - Converged 

The judge was effectively unusable because it lacked operational criteria.

It evolved into a full convergence-evaluation framework based on:

- assumptions
- gaps
- perspectives
- framings
- meta questions
- ambiguity
- success criteria

This was later replaced by an even better approach (see below).

---

# 2. LLM Provider Architecture

The project moved from provider-specific code toward a provider abstraction.

## Initial Goal

Support:

- OpenAI
- Anthropic

through a common interface.

The resulting design centered on:

python class LLMProvider(Protocol): 

with:

python generate_text(...) generate_structured(...) 

implemented by:

python OpenAIProvider AnthropicProvider 

This provided:

- provider independence
- dependency inversion
- easier testing
- future extensibility

The project also gained:

python make_provider(...) 

allowing selection through configuration.

---

# 3. CLI Design

A substantial amount of time was spent refining command semantics.

Several designs were considered.

Eventually the following model emerged:

text problemform analyze problemform synthesize problemform judge problemform run 

with optional:

text problemform explain problemform export problemform agent <agent_name> 

The most important insight was that:

text analyze 

represents the analytical phases,

while

text synthesize 

creates the refined prompt,

and

text judge 

evaluates convergence.

This maps naturally onto the actual architecture.

---

# 4. Prompt History

One major realization was:

> The refined prompt is the primary artifact produced by ProblemForm.

Originally only the final prompt was retained.

The project evolved to store:

python PromptVersion 

history inside:

python ProblemState 

This enabled:

- auditing
- comparison
- future evaluation
- convergence analysis

Prompt history later became central to solving convergence.

---

# 5. The Convergence Crisis

This was probably the most important problem encountered during the sprint.

## Symptom

With:

text max_iterations = 5 

the system often produced:

text NEAR_CONVERGENCE NEAR_CONVERGENCE NEAR_CONVERGENCE NEAR_CONVERGENCE NEAR_CONVERGENCE 

and simply ran until the iteration cap.

The judge continually found:

> more things that could theoretically be refined.

which is almost always true.

---

## Root Cause

The convergence judge was evaluating:

> Are there remaining opportunities?

instead of:

> Would the user actually receive a meaningfully different answer?

This caused endless refinement.

---

## Breakthrough

A discussion with Claude Code led to a new convergence philosophy:

### Old criterion

text Can additional refinement be imagined? 

### New criterion

text Would a competent answerer respond meaningfully differently to the previous prompt versus the current prompt? 

This reframed convergence around user value rather than refinement completeness.

---

## New Convergence Model

The judge now compares:

text v[n-1] vs v[n] 

and asks:

text Material difference? 

Status mapping became:

text Large material improvement → NOT_CONVERGED  Small real improvement → NEAR_CONVERGENCE  Immaterial improvement → CONVERGED 

Remaining opportunities became:

text informational only 

instead of the primary signal.

---

## Results

Previously:

text 5 loops still NEAR_CONVERGENCE 

After the redesign:

text 1–2 loops CONVERGED 

for many realistic prompts.

---

# 6. Prompt Refinement Performance Crisis

After convergence was fixed, a new issue emerged.

A real run showed:

text PROMPT_REFINEMENT ≈ 10 minutes 

despite all other phases finishing quickly.

---

## Investigation

The synthesizer was receiving:

python _problem_context(state) 

which serialized:

python state.model_dump_json(...) 

for the entire ProblemState.

This included:

- objectives
- assumptions
- gaps
- expert panel
- framings
- meta questions
- prompt history
- convergence output
- bookkeeping fields
- previous prompt versions

everything.

---

## Discovery

The synthesizer only actually needed:

- objectives
- artifacts
- latest prompt

Most of the remaining information was noise.

---

## Solution

A new:

python _synthesis_context(...) 

was created.

It includes:

- raw_input
- objectives
- assumptions
- gaps
- expert questions
- framings
- meta questions
- latest prompt only

and excludes:

- prompt history
- convergence output
- bookkeeping
- artifact rationales

---

## Results

Context size dropped from:

text 47,311 chars 

to:

text 6,176 chars 

or:

text 13.1% 

of its previous size.

---

## Performance Improvement

Before:

text PROMPT_REFINEMENT ≈ 10 minutes 

After:

text PROMPT_REFINEMENT ≈ 7 seconds 

roughly an 85× improvement.

This effectively eliminated the primary performance bottleneck.

---

# 7. Architectural Evolution

The system naturally evolved toward different context sizes for different tasks.

## Large Context

Analytical phases:

- objective analysis
- assumption excavation
- information gaps
- expert panel
- alternative framing
- meta questions

benefit from rich context.

---

## Small Context

Prompt synthesis only needs:

- distilled insights
- latest prompt

---

## Tiny Context

Convergence only needs:

- previous prompt
- current prompt
- minimal supporting context

This specialization dramatically improved:

- cost
- speed
- convergence behavior

without reducing output quality.

---

# 8. Current State

At the end of the sprint:

## Working

- Multi-provider architecture
- Structured outputs
- Prompt history
- Analytical pipeline
- Prompt synthesis
- Prompt-delta convergence
- Checkpointing
- CLI commands
- Fast synthesis
- Stable convergence

## Major Problems Solved

### Solved

- Endless NEAR_CONVERGENCE loops
- Full-state synthesis bloat
- Massive prompt refinement latency
- Lack of prompt history
- Weak convergence criteria

### Observed

The system now frequently converges after:

text 1–2 iterations 

instead of running to the iteration cap.

---

# Recommended Next Phase

Shift from architecture work to evaluation.

Run large numbers of real prompts through ProblemForm and study:

- when refinements help
- when refinements hurt
- when refinements overcomplicate
- whether users prefer v0, v1, or v2

The next major advances are likely to come from empirical evaluation rather than additional architectural changes.