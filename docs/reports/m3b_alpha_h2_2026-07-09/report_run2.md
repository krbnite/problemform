# Benchmark Report

**Run ID:** `2026-07-09T17-16-19_1cb3a1`
**Started:** 2026-07-09T17:16:19+00:00
**Finished:** 2026-07-09T17:18:59+00:00

## Headline

| Metric | Value |
|---|---|
| Refined wins | **0%** (0/1) |
| Raw wins | **0%** (0/1) |
| Ties | **100%** (1/1) |
| Material improvement rate | **0%** |
| Degradation rate | **0%** |

**Sample:** n=1 (completed: 1, errored: 0).
**Caveats:** K=1; sample size likely below any statistical significance threshold.

## Configuration

| Role | Provider | Model |
|---|---|---|
| ProblemForm | OpenAIProvider | gpt-4.1 |
| Answer | OpenAIProvider | gpt-4.1 |
| Judge | AnthropicProvider | claude-sonnet-4-6 |

**max_iterations:** 1
**Position randomized:** yes
**Judgments per pair (K):** 1

## Runtime

| Role | Total |
|---|---|
| ProblemForm refinement | 1m 16s |
| Answer generation | 22.8s |
| Comparative judge | 7.5s |
| Rubric evaluation | 53.6s |
| Property checks | 0.0s |
| **Total** | **2m 40s** |

## Rubric evaluations

| Rubric | Target | Raw mean | Refined mean | Δ (refined − raw) | n |
|---|---|---|---|---|---|
| formulation_quality_v1 | formulation | 0.45 | 0.75 | +0.30 | 1 |

## Property checks

_No property checks applied in this run._

## Disagreement diagnostic

_Cases where the M3A answer verdict and the formulation-rubric delta point in different directions. Worth human review; the two lenses are shown side by side, never merged._

| Case | Rubric | M3A verdict | Formulation Δ | Pattern |
|---|---|---|---|---|
| aquinas_narrative_designer | formulation_quality_v1 | tie / stylistic_only | +0.30 | P3 · answer tie, large formulation gain |

## Per-case results

| Case | Category | Winner | Materiality |
|---|---|---|---|
| aquinas_narrative_designer | argument | tie | stylistic_only |

## Cases where refined was worse than raw

_None in this run._

## Errors

_None._
