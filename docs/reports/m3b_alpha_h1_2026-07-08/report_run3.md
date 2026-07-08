# Benchmark Report

**Run ID:** `2026-07-08T19-33-04_2fa0e8`
**Started:** 2026-07-08T19:33:04+00:00
**Finished:** 2026-07-08T19:44:23+00:00

## Headline

| Metric | Value |
|---|---|
| Refined wins | **100%** (5/5) |
| Raw wins | **0%** (0/5) |
| Ties | **0%** (0/5) |
| Material improvement rate | **100%** |
| Degradation rate | **0%** |

**Sample:** n=5 (completed: 5, errored: 0).
**Caveats:** K=1; sample size likely below any statistical significance threshold.

## Configuration

| Role | Provider | Model |
|---|---|---|
| ProblemForm | OpenAIProvider | gpt-4.1 |
| Answer | OpenAIProvider | gpt-4.1 |
| Judge | OpenAIProvider | gpt-4o |

**max_iterations:** 1
**Position randomized:** yes
**Judgments per pair (K):** 1

**Bias warnings:**
- answer and judge use the same provider (openai); self-preference bias is likely. Consider using a different provider family for the judge.

## Runtime

| Role | Total |
|---|---|
| ProblemForm refinement | 5m 16s |
| Answer generation | 1m 55s |
| Comparative judge | 17.2s |
| Rubric evaluation | 1m 25s |
| Property checks | 2m 27s |
| **Total** | **11m 19s** |

## Rubric evaluations

| Rubric | Target | Raw mean | Refined mean | Δ (refined − raw) | n |
|---|---|---|---|---|---|
| formulation_quality_v1 | formulation | 0.14 | 0.58 | +0.44 | 5 |

## Property checks

| Property | Target | Raw pass | Refined pass | n |
|---|---|---|---|---|
| addresses_stated_request | artifact | 0% | 0% | 5 |
| no_unnecessary_refusal | artifact | 100% | 100% | 5 |
| no_obvious_unsupported_facts | artifact | 100% | 80% | 5 |
| respectful_tone | artifact | 100% | 100% | 5 |
| remains_scientifically_accurate_0 | formulation | 0% | 0% | 1 |
| does_not_lose_substantive_content_compar_1 | formulation | 0% | 0% | 1 |
| does_not_bloat_the_prompt_with_unnecessa_2 | formulation | 100% | 0% | 1 |
| distinguishes_solar_from_lunar_eclipses_3 | formulation | 0% | 0% | 1 |
| elicits_the_child_s_age_0 | formulation | 0% | 0% | 1 |
| elicits_the_child_s_prior_exposure_to_wa_1 | formulation | 0% | 0% | 1 |
| elicits_whether_the_parent_can_swim_2 | formulation | 0% | 0% | 1 |
| avoids_one_size_fits_all_advice_that_ign_3 | formulation | 100% | 100% | 1 |
| disambiguates_the_multiple_meanings_of_n_0 | formulation | 0% | 0% | 1 |
| separates_semantic_from_metaphysical_cla_1 | formulation | 0% | 0% | 1 |
| identifies_hidden_assumptions_in_the_pro_2 | formulation | 100% | 100% | 1 |
| avoids_assuming_the_conclusion_3 | formulation | 100% | 100% | 1 |
| elicits_the_kind_of_code_under_review_la_0 | formulation | 0% | 0% | 1 |
| elicits_the_reviewer_s_seniority_and_the_1 | formulation | 0% | 0% | 1 |
| elicits_the_user_s_role_author_or_review_2 | formulation | 0% | 100% | 1 |
| avoids_generic_checklist_advice_that_ign_3 | formulation | 100% | 100% | 1 |
| surfaces_latent_constraints_scale_team_s_0 | formulation | 0% | 0% | 1 |
| identifies_the_relevant_decision_criteri_1 | formulation | 0% | 100% | 1 |
| resists_giving_a_generic_recommendation_2 | formulation | 100% | 100% | 1 |
| acknowledges_that_the_answer_depends_on_3 | formulation | 0% | 100% | 1 |

## Disagreement diagnostic

_Cases where the M3A answer verdict and the formulation-rubric delta point in different directions. Worth human review; the two lenses are shown side by side, never merged._

_No disagreements flagged in this run._

## Per-case results

| Case | Category | Winner | Materiality |
|---|---|---|---|
| what_causes_eclipses | control | refined | material |
| teach_kid_to_swim | parenting | refined | material |
| cosmology_nothingness | philosophy | refined | material |
| code_review_prep | practical | refined | material |
| api_design_rest_vs_graphql | technical | refined | material |

## Cases where refined was worse than raw

_None in this run._

## Errors

_None._
