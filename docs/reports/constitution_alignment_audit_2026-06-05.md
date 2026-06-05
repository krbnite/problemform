# Constitution Alignment Audit

Date: 2026-06-05

## Scope And Method

This audit treats `docs/problemform_constitution.md` as the authoritative statement of ProblemForm's intended scope and philosophy. I inspected the current workspace version of:

- `CLAUDE.md`
- `README.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/backlog.md`
- `docs/designs/`
- `problemform/agents/`
- `problemform/eval/`
- `benchmarks/`
- relevant tests and M3A reports for context

No tests were run and no implementation changes were made. At audit time, `CLAUDE.md`, `docs/designs/milestone_03b_rubrics_and_properties.md`, and `benchmarks/simple/` were untracked in git status, but they were inspected because they were explicitly in scope or directly relevant.

## Constitution Baseline

### Factual Repository Observations

The Constitution defines ProblemForm as a collaborative human-AI problem-formulation system. Its scope is not limited to questions or prompts. It explicitly names "a problem, objective, decision, request, inquiry, question, or prompt" as valid formulation targets.

The Constitution says the final deliverable is not necessarily an answer. The final deliverable is the highest-quality formulation of the question, prompt, or problem itself.

The Constitution includes several behaviors that are broader than the current code path:

- A visible Question/Prompt Quality Assessment with a quality rating and revision recommendation.
- Problem analysis that asks whether the current question is the best question.
- Information-gathering strategy, including user follow-up, external research, logical inference, or multiple methods.
- Revision and improvement that can produce an improved question, prompt, or problem statement.
- Perspective expansion through expert panel questions, alternative framings, and meta questions.
- Iterative refinement that can incorporate research and human discussion.
- Completion only when both AI and user agree the formulation is sufficiently clear and further refinement is unlikely to materially improve the outcome.

### Interpretive Judgment

The Constitution is a cognitive-methodology document, not merely a prompt-optimization spec. It describes a system for making fuzzy intent, hidden assumptions, missing context, alternative framings, and decision criteria explicit. "Question refinement" is one valid application, but not the whole vision.

### Concrete Recommendation

Treat the Constitution as defining intended scope, and treat the current question/prompt/answer benchmark path as the validated subset. This distinction should be stated repeatedly in docs and issue planning so future work does not accidentally redefine the product around the subset.

## 1. Where The Implementation Has Stayed Aligned

### Factual Repository Observations

`CLAUDE.md` explicitly says ProblemForm is a human-AI collaborative problem-formulation system and names the Constitution as authoritative when implementation decisions are ambiguous.

`README.md` says ProblemForm is not meant to answer the user's question, but to produce a high-quality formulation. It also points readers to the Constitution and architecture docs.

`docs/architecture.md` preserves the broad scope in its opening definition: the goal is to formulate "a problem, objective, decision, inquiry, question, or prompt."

The core data model in `problemform/models.py` preserves the Constitution's main cognitive artifacts:

- stated and inferred objectives
- assumptions
- information gaps
- expert perspectives
- alternative framings
- meta questions
- prompt/formulation versions
- convergence status

The workflow in `problemform/core/workflow.py` maps cleanly to the Constitution's phase structure:

- Objective Analysis
- Assumption Excavation
- Information Gap Detection
- Expert Panel Generation
- Alternative Framing
- Meta Question Generation
- Prompt Refinement
- Convergence Evaluation

Most agent prompts preserve the "do not answer, formulate instead" posture. The assumption, information-gap, expert-panel, alternative-framing, and meta-question prompts all emphasize surfacing considerations that improve formulation rather than solving the problem.

The M3A evaluation framework explicitly tries to prevent advocacy bias. It has a control case, tracks raw wins and degradations, warns on same-family judging, randomizes answer position, and preserves failures rather than hiding them.

### Interpretive Judgment

The implementation is strongly aligned at the level of phase decomposition. It has not lost the core insight that better formulation depends on objectives, assumptions, gaps, perspectives, alternatives, and meta-level questions.

The project is also unusually honest about measurement. The design docs, backlog, and reports repeatedly warn that benchmarks can become advocacy artifacts. That honesty is Constitution-aligned because it keeps the project oriented toward genuine formulation quality rather than self-congratulation.

### Concrete Recommendations

Preserve the current phase decomposition. It is the strongest alignment point between the code and the Constitution.

Keep the benchmark's anti-advocacy design principles. Control cases, degradation reporting, and bias warnings are valuable even as the benchmark expands beyond questions.

When refactoring names later, avoid deleting the existing cognitive artifacts. Add broader terminology around them rather than replacing them with narrower "prompt engineering" concepts.

## 2. Where The Project Has Drifted From The Constitution

### Factual Repository Observations

The current implementation does not model the Constitution's visible quality assessment. There is no `QualityRating`, no `RevisionRecommendation`, and no explicit field for "important ambiguities or missing context" as a first-class assessment artifact.

The current CLI and workflow are largely autonomous. They identify information gaps and acquisition methods, but they do not ask follow-up questions, pause for user input, conduct external research, or require user agreement before completion.

The Constitution's perspective-expansion phase asks for expert-directed rewrites of questions or framings. The current expert-panel model stores a perspective and a question. The alternative-framing and meta-question models do not store "expert best suited to explore it" or "rewritten as directed to that expert" fields.

The synthesizer returns a field named `prompt`, and `ProblemState` stores `final_prompt`. The architecture diagram ends at "Final Prompt." This is functional, but narrower than the Constitution's "question, prompt, or problem formulation."

The convergence judge is prompt-delta and answerer-response primary. It asks whether a competent answerer would produce a meaningfully different response to the previous prompt versus the current prompt. That is a good heuristic for question/prompt inputs, but it narrows convergence around downstream answer behavior.

The M3A evaluation data model uses `raw_question`. `ComparativeJudgment.target` is locked to `"answer"`. The engine runs `raw_answer = answer_provider.generate_text(raw_question)` and `refined_answer = answer_provider.generate_text(refined_prompt)`. The comparative judge prompt is explicitly about a user's question and two answers.

The shipped benchmark corpus is all questions. Even the control case is a well-formed factual question.

`README.md` frames the value proposition partly as "LLM output quality is bounded by prompt quality." That is true for the validated subset, but it is narrower than the Constitution's wider problem-formulation frame.

### Interpretive Judgment

The deepest drift is not in the analytical phases. The drift is at the output and evaluation boundaries. Internally, the system still thinks in terms of objectives, assumptions, gaps, and framings. Externally, it increasingly proves its value by producing better prompts that produce better answers.

That is a reasonable MVP path, but it can become dangerous if the benchmark becomes the project's self-definition. If the project only measures answer improvement, it will naturally optimize toward answerable questions and prompt-shaped outputs, even though the Constitution explicitly includes decisions, arguments, inquiries, requests, and ambiguous problem situations.

### Concrete Recommendations

Add an explicit "validated subset" note to `README.md`, `CLAUDE.md`, and `docs/roadmap.md`: current empirical support is strongest for question/prompt inputs that have downstream answer artifacts.

Plan a future `ProblemState` or eval schema migration from `raw_question` / `final_prompt` toward broader aliases such as `raw_input` / `final_formulation`, while preserving backward compatibility.

Create a backlog issue for the missing visible quality-assessment artifact: quality rating, ambiguities, flawed assumptions, unstated premises, framing effects, missing alternatives, and revision recommendation.

Create a backlog issue for "expert-directed rewrite fields" or explicitly document why that Constitution detail is deferred.

## 3. Acceptable Validated-Subset Limitations

### Factual Repository Observations

`docs/designs/problemform_scope.md` already names the distinction between intended scope and validated subset. It says the Constitution remains authoritative while M1-M3A have matured faster along the question dimension.

`docs/backlog.md` has a dedicated entry called "M3B as the bridge from question refinement to general problem formulation." It correctly identifies the question-only corpus, question/answer vocabulary, and M3A's composite measurement as the gap to close.

The M3A design doc explicitly labels Phase A as answer-quality-first and defers prompt/formulation-level evaluation to later phases.

The default benchmark suite has only five cases, including one control. The suite is clearly a starter corpus, not a definitive proof of the whole methodology.

The one-iteration default is documented as a cost and over-refinement control, not as a claim that one iteration completes the Constitution's full collaborative process.

### Interpretive Judgment

These are acceptable limitations if they remain framed as limitations. A validated subset is not drift by itself. It becomes drift only if the docs, naming, benchmarks, and future issues stop pointing back to the broader Constitution.

The current project is mostly self-aware about this. The scope note and backlog entry are exactly the right corrective artifacts.

### Concrete Recommendations

Keep "validated subset" as formal vocabulary in the project docs.

Treat the question-only corpus as an M3A corpus, not "the ProblemForm corpus."

Keep the one-iteration default, but describe it as an operational default for prompt-shaped CLI runs, not as a general claim about all problem-formulation work.

Do not require M3A to solve non-question evaluation. It cannot. Let M3B carry that responsibility.

## 4. Drifts That Risk Narrowing ProblemForm Incorrectly

### Factual Repository Observations

The strongest narrowing signals are:

- `TestCase.raw_question` as the central benchmark input field.
- `ComparativeJudgment.target == "answer"` in Phase A.
- `raw_answer` and `refined_answer` as headline artifacts.
- The comparative judge prompt's "Question" and "Answer A/B" framing.
- `final_prompt` as the top-level user-facing output.
- Convergence driven by whether an answerer would respond differently.
- README language that makes downstream LLM answer quality the main explanatory frame.

The corpus does include an architecture-decision case, but it is phrased as "Should I use REST or GraphQL for my new API?", still a question with an answer.

### Interpretive Judgment

The risk is a feedback loop:

1. Benchmarks contain only answerable questions.
2. Evaluation rewards better downstream answers.
3. Prompts and docs optimize around answer improvement.
4. Future issues prioritize what improves the benchmark.
5. ProblemForm quietly becomes a prompt optimizer for answerable questions.

This would narrow the project away from the Constitution. The Constitution's most interesting scope includes inputs that are not naturally answerable: arguments, belief clusters, ambiguous situations, strategic decisions, research directions, interpersonal dilemmas, and requests whose real objective is unclear.

### Concrete Recommendations

Avoid using M3A win rate as the global "ProblemForm works" metric. Call it "M3A answer-improvement rate" or equivalent.

Add non-question examples to the README before implementation supports full evaluation for them. Clearly mark them as intended-scope examples.

When designing new prompts, prefer "input", "formulation", "problem statement", and "intended audience" over "question", "prompt", and "answerer" unless a phase truly requires question vocabulary.

Track at least one future issue that explicitly says: "ProblemForm must handle non-question inputs named by the Constitution."

## 5. How The Benchmark Corpus And M3A Framework Shape Self-Understanding

### Factual Repository Observations

The default corpus tests five question-shaped cases:

- metaphysical disambiguation
- code-review preparation
- REST vs GraphQL API choice
- teaching a child to swim
- a factual eclipse control question

The expected properties often point at context elicitation, disambiguation, avoiding generic answers, and maintaining factual accuracy.

M3A measures a three-role pipeline:

- ProblemForm provider refines the raw question.
- Answer provider answers both raw and refined prompts.
- Judge provider compares the two answers.

The report headlines refined wins, raw wins, ties, material-improvement rate, and degradation rate. It also includes a diagnostic section for cases where refined was worse than raw.

The M3A report says the milestone shifted the project from "Can ProblemForm refine prompts?" to "Can ProblemForm demonstrate that it improves downstream answers?"

### Interpretive Judgment

The corpus is well chosen for testing whether ProblemForm improves underspecified questions. It is especially good at testing context elicitation and disambiguation.

But it constrains self-understanding in two ways:

1. It makes answerability a precondition for evaluation.
2. It makes downstream answer quality the headline signal.

That is useful for M3A, but it is not a direct measure of the Constitution's deliverable. M3A measures a composite: ProblemForm times the answer model's responsiveness to the refined formulation. This is valuable but confounded.

### Concrete Recommendations

Keep M3A as the answer-outcome lens for question-shaped cases.

Add a separate formulation-quality lens before drawing project-wide conclusions.

Split future benchmark properties into target-aware categories, such as `formulation_properties` and `artifact_properties`.

Add corpus categories that are not naturally answerable: argument, belief critique, strategic decision, inquiry design, request clarification, research-program formulation, and ambiguous personal or organizational problem.

## 6. Does M3B-As-Bridge Seem Right?

### Factual Repository Observations

`docs/designs/problemform_scope.md` proposes Path B: judge the formulation directly rather than judging a downstream artifact.

`docs/designs/milestone_03b_rubrics_and_properties.md` adopts the `target` axis explicitly:

- `target=formulation`
- `target=artifact`

It also adopts a `mode` axis:

- `mode=absolute`
- `mode=comparative`

The M3B design treats M3A's comparative-answer judgment as one quadrant: `target=artifact, mode=comparative`.

The M3B design defines `target=formulation` as the bridge to broader Constitution scope and proposes a `formulation_quality_v1` rubric with criteria such as central-claim clarity, assumption surfacing, constraint articulation, alternative-framing coverage, and meta-question presence.

The M3B design explicitly says empirical validation is still pending. M3B-alpha would test the bridge on the existing question corpus and on a non-question Aquinas-style argument case. M3B-beta would diversify the corpus.

### Interpretive Judgment

Yes. M3B-as-bridge is the right architectural direction.

It reconnects the evaluation framework to the Constitution's central claim: the deliverable is the formulation itself. It also decouples ProblemForm quality from answer-model behavior. That is exactly the bridge needed for non-question inputs.

The design is appropriately cautious. It does not simply declare formulation judging solved. It makes the bridge testable: first against existing questions, then against a non-question input where M3A has no natural answer artifact.

### Concrete Recommendations

Proceed with M3B-alpha before broad corpus expansion. The formulation target should be operational before non-question cases become load-bearing.

Keep M3B's three metrics visually separate:

- comparative answer outcomes
- formulation rubric outcomes
- property-check compliance

Do not combine them into one overall score.

Use disagreement between M3A and formulation rubrics as a diagnostic, not as an error. Disagreement is where the project will learn what its benchmark is actually measuring.

Make corpus diversification M3B-beta, not a random M3A expansion. Non-question cases need formulation evaluation to be meaningful.

## 7. What Should Be Updated To Preserve The Broader Vision

### Factual Repository Observations

The repo already has the right planning artifacts: the scope note, the M3B design reference, and the backlog bridge entry. What is missing is propagation into the most-read docs and future issue structure.

### Interpretive Judgment

The project is at a healthy but delicate point. It has built a concrete, measurable subset. That subset is good enough to generate momentum, but also strong enough to pull the project toward itself. The next few docs, prompts, and benchmark schema choices will decide whether "validated subset" remains a subset or becomes the product definition.

### Concrete Recommendations

Documentation updates:

- In `README.md`, add a short "Validated subset vs intended scope" section.
- In `README.md`, describe the default benchmark as answer-outcome evaluation for question-shaped inputs.
- In `docs/architecture.md`, change "Final Prompt" language to "Final Formulation / Prompt" or explain that the current implementation stores formulations in prompt-shaped fields.
- In `docs/roadmap.md`, split M3 into M3A answer-outcome evaluation and M3B formulation-target evaluation.
- In `CLAUDE.md`, add M3B-as-bridge guidance once the design is accepted as active direction.
- In `docs/cli_commands.md`, make clear that `benchmark` currently evaluates question-shaped YAML cases.

Prompt updates:

- Change generic agent wording from "question" to "input" where it does not need to be question-specific.
- Change the synthesizer from "Prompt/Question Synthesizer" toward "Formulation Synthesizer", while keeping prompt compatibility.
- Revise convergence language so it can evaluate the formulation's suitability for an intended audience, not only whether an answerer would produce a different answer.
- Add or defer explicit Constitution fields for expert-directed rewrites in expert-panel, alternative-framing, and meta-question outputs.

Benchmark updates:

- Keep `raw_question` for M3A compatibility, but introduce a future-compatible alias or schema path toward `raw_input`.
- Add `input_type` to test cases once non-question cases enter the corpus.
- Split expected properties by target: formulation properties versus artifact properties.
- Add non-question cases only after formulation-target evaluation is available.
- Add controls for non-question inputs, such as a well-formed decision brief or clear argument where ProblemForm should not over-process.

Future issue planning:

- M3B-alpha: formulation rubrics and property checks with target/mode axes.
- M3B-alpha validation: existing five questions plus one non-question prototype.
- M3B-beta: diversified corpus across Constitution-named input types.
- Quality-assessment artifact: model and render the Constitution's visible quality rating and revision recommendation.
- Human-in-loop design: follow-up question flow, user agreement, and checkpoint/resume semantics.
- External research/tooling design: only after security constraints are explicit, because the Constitution permits external research but future tool execution must preserve least privilege, user confirmation, and prompt-injection resistance.

## Overall Finding

### Factual Repository Observations

The repository is not Constitution-complete. It is a working implementation of a validated subset: question/prompt-shaped inputs, autonomous CLI refinement, prompt-shaped output, and answer-outcome benchmarking.

The repository is also not Constitution-hostile. The core phase structure and many agent prompts remain deeply aligned with the Constitution's problem-formulation methodology.

### Interpretive Judgment

The project has drifted operationally, not philosophically. The code and benchmark have narrowed faster than the stated vision, but the docs now recognize the narrowing and have a plausible bridge plan.

The highest-risk move would be to keep expanding M3A as if answer-outcome evaluation were the whole project. The highest-value move is to make M3B's formulation target real and then diversify the corpus.

### Concrete Recommendation

Proceed with M3B-as-bridge as the next major alignment-preserving step. Treat it as an empirical test of whether ProblemForm can evaluate formulations directly, not as a foregone conclusion. If it works, it becomes the bridge from question refinement back to the Constitution's full problem-formulation vision.

## Metadata

```yaml
date_created: "2026-06-05"
document_type: "constitution_alignment_audit"
status: "active"
scope:
  authoritative_reference: "docs/problemform_constitution.md"
  inspected:
    - "CLAUDE.md"
    - "README.md"
    - "docs/architecture.md"
    - "docs/roadmap.md"
    - "docs/backlog.md"
    - "docs/designs/"
    - "problemform/agents/"
    - "problemform/eval/"
    - "benchmarks/"
created_by: "Codex"
implementation_changes: "none"
files_created:
  - "docs/reports/constitution_alignment_audit_2026-06-05.md"
active_document: true
shelved: false
```
