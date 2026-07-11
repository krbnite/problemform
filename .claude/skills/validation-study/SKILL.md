---
name: validation-study
description: Conduct an outcome-neutral benchmark-based validation study of an existing ProblemForm implementation and produce a permanent report under docs/reports/.
---

# Validation Study

Use this skill when conducting a benchmark-based validation study (e.g. H1, H2, H3) of an existing implementation.

This skill is for **evaluating** behavior, not changing it.

## Principles

- The implementation is the subject of study, not the object of modification.
- Validation is outcome-neutral.
- Benchmark artifacts are the ground truth for what the run produced.
- Distinguish observations from interpretations from conclusions.
- Conclusions should be proportional to the evidence.

## Procedure

### 1. Understand the study

Identify:

- hypothesis
- implementation being evaluated
- benchmark corpus
- evaluation configuration
- success criteria
- expected deliverable

Review the relevant design documents before running anything.

If the study builds on earlier validation work, also review the relevant prior reports to understand the existing evidence and avoid overstating new conclusions.

---

### 2. Verify the experiment

Confirm:

- benchmark corpus
- providers/models
- evaluation configuration
- output directory
- run command

Do not silently change the experimental design.

---

### 3. Execute exactly as specified

Run the benchmark using the approved configuration.

Do not introduce additional benchmark overrides unless explicitly requested.

Preserve all generated artifacts.

---

### 4. If a genuine implementation defect is discovered

Pause and assess.

Determine whether the defect:

- does **not** materially affect the stated hypothesis (continue and document it),
- partially affects the study (qualify the conclusions), or
- invalidates the study (stop and report).

Document:

- what failed,
- why it does or does not affect the hypothesis,
- any impact on interpretation.

Do **not** fix implementation bugs during the validation study unless explicitly instructed.

---

### 5. Analyze the results

Treat the benchmark artifacts as authoritative for what the benchmark produced.

Verify important quantitative claims directly from the structured artifacts before drafting conclusions, including counts, rates, deltas, and aggregate metrics.

Distinguish clearly between:

- observations
- interpretations
- conclusions

Avoid overstating findings.

---

### 6. Write the report

Create a dated report under:

```
docs/reports/
```

Follow the repository documentation conventions in:

```
docs/DOCUMENTS_METADATA.md
```

The report should typically include:

- Objective / hypothesis
- Experimental setup
- Results
- Analysis
- Threats to validity
- Conclusions
- Recommendations (only if justified by the evidence)

Report both positive and negative findings.

---

### 7. Preserve reproducibility

Record enough information that another engineer can reproduce the study:

- implementation revision (commit or tag)
- whether the worktree was clean or contained local modifications
- benchmark corpus
- providers/models
- command/configuration
- run artifact location

---

## Out of Scope

This skill does not:

- modify implementation code
- redesign architecture
- tune prompts
- rewrite benchmarks
- silently fix discovered defects

Those belong to separate implementation work after the validation study.

---

## Success Criteria

A successful validation study:

- answers the stated hypothesis
- is reproducible
- is evidence-driven
- is outcome-neutral
- clearly separates facts from interpretation
- becomes a permanent project record