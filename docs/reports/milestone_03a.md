# M3 Phase A Sprint Summary — Evaluation Framework

Version: v0.2.0  
Milestone: M3 Phase A — Evaluation Framework  
Date: June 2026

---

# Overview
Milestone 3 Phase A introduced ProblemForm's first end-to-end evaluation framework.

Prior milestones focused on building the refinement system itself:
- M1 established the core architecture and immutable state model.
- M2 delivered the CLI, provider integrations, workflow execution, and reliability improvements.

M3 Phase A shifted the project from:

> "Can ProblemForm refine prompts?"

to:

> "Can ProblemForm demonstrate that it improves downstream answers?"

This milestone establishes the foundation for empirical evaluation and future benchmark-driven development.

---

# What Was Built
## Benchmark Command
A new CLI command was added:

bash problemform benchmark <suite> 

This command executes a benchmark suite composed of YAML test cases and generates evaluation reports.

---

## Evaluation Framework
A dedicated problemform.eval package was introduced containing:

- Benchmark execution engine
- YAML corpus loader
- Comparative answer judge
- Reporting utilities
- Evaluation data models

---

## Three-Role Architecture
The benchmark framework separates responsibilities into three independent model roles:

| Role | Responsibility |
|--------|--------|
| ProblemForm | Refines the original question |
| Answer | Generates answers from raw and refined prompts |
| Judge | Evaluates which answer is better |

This architecture allows future experimentation with cross-provider evaluation and model ablations.

---

## Comparative Answer Evaluation
Phase A evaluates ProblemForm indirectly by comparing answers rather than prompts.

Workflow:

text Raw Question     ↓ Raw Answer  ProblemForm     ↓ Refined Prompt     ↓ Refined Answer  Judge     ↓ Comparative Verdict 

The judge determines:
- Winner (raw / refined / tie)
- Materiality
- Rationale
- Key differences

Prompt-level evaluation was intentionally deferred to later phases.

---

## Bias Mitigations
Several bias mitigations were implemented:

### Position Randomization
Answer order is randomized for every comparison.

The judge only sees:

text Answer A Answer B 

The system later de-anonymizes the result.

### Same-Family Warning
Using the same model family for Answer and Judge is allowed but generates a warning.

This records a known self-preference risk without blocking experimentation.

### Failure Containment
Individual benchmark failures are isolated.

A single failed case does not terminate the benchmark run.

---

## Reporting
Two report formats are generated:

text report.json report.md 

Key metrics include:
- Refined win rate
- Raw win rate
- Tie rate
- Material improvement rate
- Degradation rate

The reporting philosophy intentionally highlights regressions rather than hiding them behind aggregate scores.

---

## Benchmark Corpus
A starter benchmark corpus was created under:

text benchmarks/default/ 

Five initial cases were included:

| Category | Case |
|-----------|-----------|
| Philosophy | Cosmology / Nothingness |
| Practical | Code Review Preparation |
| Technical | REST vs GraphQL |
| Parenting | Teaching a Child to Swim |
| Control | What Causes Eclipses? |

The control case was added specifically to reduce benchmark-selection bias and prevent the corpus from becoming an advocacy artifact.

---

# Major Design Decisions
## Compare Answers, Not Prompts
Phase A evaluates downstream answer quality rather than prompt quality.

The rationale is simple:
> Users ultimately care about answers.

Prompt evaluation remains a future enhancement.

---

## K = 1

Only a single judge evaluation is performed per comparison.

Multi-judge aggregation was intentionally deferred until the framework proves useful.

---

## No Answer Wrapper Prompt
Benchmark answer generation uses:

python provider.generate_text(...) 

directly.

No additional wrapper prompt is inserted by the evaluation framework.

This prevents evaluation results from being confounded by benchmark-specific instructions.

---

## Control Case Requirement
The benchmark corpus must contain at least one question where ProblemForm may not help.

This decision reflects the project's "measurement, not advocacy" philosophy.

---

## Inline Answer Storage
Answer text is stored directly in the benchmark report model while also being written to individual text files.

This keeps reports self-contained and easier to analyze programmatically.

---

# Lessons Learned
## Benchmarks Are Expensive
The first real benchmark run revealed significantly higher runtime and token costs than expected.

A five-case benchmark using GPT-5.4 for all roles required:
- ~15 minutes
- ~$1 in API usage

This immediately surfaced cost-awareness as a future priority.

---

## Progress Feedback Matters
The first benchmark experience exposed a usability gap.

The user had no visibility into:
- Which case was running
- How many cases remained
- Estimated completion time
- Cost accumulation

Future benchmark UX improvements became an obvious priority.

---

## Material Improvements Matter More Than Wins
An early benchmark produced:

text Refined wins: 5/5 Material improvement rate: 0% 

This reinforced an important distinction:
> A win is not necessarily a meaningful win.

Materiality may ultimately become more important than simple win rate.

---

## Evaluation Changes the Project
Before M3:
> ProblemForm was a prompt refinement system.

After M3:
> ProblemForm became a system capable of evaluating its own effectiveness.

This represents a major shift in project maturity.

---

# Open Questions
Several important questions remain unanswered.

## Model Size Requirements
Does ProblemForm actually require frontier models?

Could smaller models deliver similar refinement quality at dramatically lower cost?

---

## Judge Bias
How much self-preference bias exists when answer and judge models come from the same provider family?

Cross-provider experiments are needed.

---

## Prompt Evaluation
Should prompt quality be evaluated directly in addition to answer quality?

This was deferred from Phase A.

---

## Convergence Metrics
Can convergence be measured empirically using semantic-distance metrics?

Potential future signals:
- Prompt-to-prompt distance
- Answer-to-answer distance
- Correlation with judge verdicts

---

# Immediate Follow-Up Backlog
## Benchmark UX
- Progress bars
- Current case display
- Elapsed time
- Estimated time remaining

## Cost Reporting
- Token counts
- Cost breakdown by role
- Cost summaries in reports

## Verdict Explainability
Surface judge rationales and key differences directly in Markdown reports.

## Cross-Family Evaluation
Run OpenAI-vs-Anthropic judge experiments.

## Model Ablation Studies
Determine the quality/cost sweet spot for:

- ProblemForm models
- Answer models
- Judge models

## Corpus Expansion
Grow beyond the initial five-case benchmark suite.

---

# Outcome
M3 Phase A successfully delivered the project's first benchmark framework.

The milestone established a foundation for:

- Measuring answer quality improvements
- Detecting regressions
- Running comparative experiments
- Studying convergence behavior
- Evaluating future architectural changes

The project now has a mechanism for generating evidence rather than relying solely on intuition.