# Benchmark Report

**Run ID:** `2026-07-10T19-42-22_9b1139`
**Started:** 2026-07-10T19:42:22+00:00
**Finished:** 2026-07-10T20:48:32+00:00

## Headline

| Metric | Value |
|---|---|
| Refined wins | **33%** (4/12) |
| Raw wins | **25%** (3/12) |
| Ties | **42%** (5/12) |
| Material improvement rate | **0%** |
| Degradation rate | **0%** |

**Answer comparison skipped:** 11 of 24 cases (formulation-only by policy, or forced off).

**Sample:** n=24 (completed: 12, errored: 1, answer-skipped: 11).
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
| ProblemForm refinement | 19m 38s |
| Answer generation | 3m 14s |
| Comparative judge | 1m 45s |
| Rubric evaluation | 27m 54s |
| Property checks | 8m 32s |
| **Total** | **61m 03s** |

## Rubric evaluations

| Rubric | Target | Raw mean | Refined mean | Δ (refined − raw) | n |
|---|---|---|---|---|---|
| formulation_quality_v1 | formulation | 0.22 | 0.68 | +0.46 | 24 |
| answer_quality_v1 | artifact | 0.82 | 0.76 | -0.06 | 13 |

## Property checks

| Property | Target | Raw pass | Refined pass | n |
|---|---|---|---|---|
| addresses_stated_request | artifact | 100% | 92% | 13 |
| no_unnecessary_refusal | artifact | 100% | 100% | 13 |
| no_obvious_unsupported_facts | artifact | 92% | 100% | 13 |
| respectful_tone | artifact | 100% | 100% | 13 |
| remains_scientifically_accurate_0 | formulation | 100% | 100% | 1 |
| does_not_lose_substantive_content_compar_1 | formulation | 0% | 0% | 1 |
| does_not_bloat_the_prompt_with_unnecessa_2 | formulation | 100% | 0% | 1 |
| distinguishes_solar_from_lunar_eclipses_3 | formulation | 0% | 0% | 1 |
| elicits_the_child_s_age_0 | formulation | 0% | 0% | 1 |
| elicits_the_child_s_prior_exposure_to_wa_1 | formulation | 0% | 0% | 1 |
| elicits_whether_the_parent_can_swim_2 | formulation | 0% | 0% | 1 |
| avoids_one_size_fits_all_advice_that_ign_3 | formulation | 100% | 100% | 1 |
| disambiguates_the_multiple_meanings_of_n_0 | formulation | 0% | 100% | 1 |
| separates_semantic_from_metaphysical_cla_1 | formulation | 0% | 0% | 1 |
| identifies_hidden_assumptions_in_the_pro_2 | formulation | 0% | 100% | 1 |
| avoids_assuming_the_conclusion_3 | formulation | 100% | 100% | 1 |
| elicits_the_kind_of_code_under_review_la_0 | formulation | 0% | 0% | 1 |
| elicits_the_reviewer_s_seniority_and_the_1 | formulation | 0% | 0% | 1 |
| elicits_the_user_s_role_author_or_review_2 | formulation | 0% | 0% | 1 |
| avoids_generic_checklist_advice_that_ign_3 | formulation | 100% | 0% | 1 |
| surfaces_latent_constraints_scale_team_s_0 | formulation | 0% | 0% | 1 |
| identifies_the_relevant_decision_criteri_1 | formulation | 0% | 0% | 1 |
| resists_giving_a_generic_recommendation_2 | formulation | 0% | 100% | 1 |
| acknowledges_that_the_answer_depends_on_3 | formulation | 0% | 100% | 1 |

## Disagreement diagnostic

_Cases where the M3A answer verdict and the formulation-rubric delta point in different directions. Worth human review; the two lenses are shown side by side, never merged._

| Case | Rubric | M3A verdict | Formulation Δ | Pattern |
|---|---|---|---|---|
| curved_space_no_bending | formulation_quality_v1 | tie / stylistic_only | +0.45 | P3 · answer tie, large formulation gain |
| web_app_money | formulation_quality_v1 | tie / stylistic_only | +0.60 | P3 · answer tie, large formulation gain |
| cosmology_nothingness | formulation_quality_v1 | tie / stylistic_only | +0.50 | P3 · answer tie, large formulation gain |
| api_design_rest_vs_graphql | formulation_quality_v1 | tie / stylistic_only | +0.35 | P3 · answer tie, large formulation gain |
| payment_api | formulation_quality_v1 | tie / stylistic_only | +0.50 | P3 · answer tie, large formulation gain |

## Per-case results

| Case | Category | Winner | Materiality |
|---|---|---|---|
| aquinas_narrative_designer | argument | skipped | — |
| jesus_is_the_son_of_god | belief | skipped | — |
| universe_is_toroidal_and_finite | belief | skipped | — |
| make_dinner_or_order_takeout | decision | skipped | — |
| what_should_i_do_tomorrow | decision | skipped | — |
| grandmother_alzheimers_identity | dilemma | skipped | — |
| manager_friend_fudging_numbers | dilemma | skipped | — |
| airplanes_stay_up | explanation | refined | minor |
| curved_space_no_bending | explanation | tie | stylistic_only |
| be_a_better_person | goal | skipped | — |
| lose_30_pounds | goal | skipped | — |
| clean_my_bedroom | instruction | raw | minor |
| web_app_money | instruction | tie | stylistic_only |
| ml_career_transition | plan | skipped | — |
| web_app_money_roadmap | plan | skipped | — |
| clint_eastwood_memoir_rewrite | prompt | raw | minor |
| dragon_story | prompt | refined | minor |
| what_causes_eclipses | control | refined | minor |
| teach_kid_to_swim | parenting | refined | minor |
| cosmology_nothingness | philosophy | tie | stylistic_only |
| code_review_prep | practical | raw | minor |
| api_design_rest_vs_graphql | technical | tie | stylistic_only |
| online_bookstore_database | specification | — | errored |
| payment_api | specification | tie | stylistic_only |

## Cases where refined was worse than raw

### `clean_my_bedroom` (instruction)

- **Winner:** raw  |  **Materiality:** minor
- **Judge rationale:** The user asked to 'clean my bedroom,' which is a simple, actionable request. Answer B provides a concise, practical step-by-step guide that directly addresses the request. Answer A, while thorough, is bloated with meta-questions, clarifying prompts, and framework-building that don't actually help the user clean their bedroom — they delay action. A competent reader wanting to clean their bedroom would find B more immediately useful. A's additional length is largely procedural overhead rather than substantive cleaning guidance.

**Key differences:**
- Answer B provides immediately actionable steps without requiring the user to answer clarifying questions first; Answer A gates the actual guidance behind a lengthy intake process.
- Answer A includes sections on 'success criteria,' 'obstacles & risks,' and 'preferences & constraints' that add length but don't materially improve the cleaning guidance over B.
- Answer B is concise and scannable, making it easier to follow while actually cleaning; Answer A's length and structure would be cumbersome to reference mid-task.
- Both answers cover the same core cleaning steps (declutter, dust/wipe, make bed, floors, finishing touches), so the substantive cleaning content is equivalent.

### `clint_eastwood_memoir_rewrite` (prompt)

- **Winner:** raw  |  **Materiality:** minor
- **Judge rationale:** Both answers confirm they understand the task and ask the user to provide the text. Answer A, however, immediately demonstrates the requested style by adopting a Clint Eastwood-esque voice ('partner,' 'make my day,' 'gritty, reflective style'), which gives the user confidence that the assistant understands the tone and can execute it. Answer B is a plain, generic acknowledgment that does nothing to preview the requested style.

**Key differences:**
- Answer A demonstrates the Clint Eastwood voice in its own reply ('partner,' 'make my day,' 'quiet wisdom, hard-earned lessons'), previewing the style the user asked for; Answer B uses generic assistant language with no stylistic demonstration.
- Answer A specifies concrete stylistic elements (gritty, reflective, quiet wisdom, signature squint) that signal understanding of the task; Answer B only vaguely references 'signature voice and style' without elaboration.

### `code_review_prep` (practical)

- **Winner:** raw  |  **Materiality:** minor
- **Judge rationale:** Both answers cover the same core preparation steps for a code review: self-review, testing, documentation, PR description, tooling, small commits, and mindset. Answer B adds a checklist, a summary table, external resource links, and compliance/regulatory considerations, but most of this additional content is padding or marginally useful extras rather than substantively different advice. The checklist in B is genuinely useful and slightly more actionable than A's equivalent content, but the summary table and many of the 'Best Practice' labels add length without adding substance. Answer A is more concise and equally complete for the practical question asked, making it the slightly better answer for a typical user who wants actionable guidance without wading through filler.

**Key differences:**
- Answer B includes a concrete checklist that a developer could use directly before submitting a PR; Answer A does not have a checklist.
- Answer B references external resources (Google Engineering Practices, OWASP, etc.); Answer A does not, which may or may not be useful depending on the user.
- Answer B adds compliance/regulatory considerations (GDPR, HIPAA, PCI DSS) that are irrelevant for most code reviews and add noise.
- Answer B's summary table and repeated 'Best Practice' labels add significant length without adding new information.
- Answer A is more concise and easier to scan quickly, making it more immediately actionable for the average developer.


## Errors

### `online_bookstore_database`

- refined answer generation failed: TruncatedResponseError: OpenAI response was truncated at max_output_tokens; increase the limit or shorten the input.

