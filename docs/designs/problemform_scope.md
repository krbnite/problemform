# ProblemForm scope: validated subset, intended scope, and the role of M3B

**Status: working hypothesis / design reference / discussion artifact. Not a project decision record. Future M3B design work may confirm, modify, or reject parts of this hypothesis.**

## Why this note exists

Over the course of milestones M1 through M3A, ProblemForm has begun to feel narrower than its original vision. The Constitution still describes a system for formulating problems, objectives, decisions, requests, inquiries, questions, and prompts. The implementation, the benchmark corpus, the phase prompts, and the evaluation framework increasingly look like a question-refinement tool. This document asks why that has happened, whether it is fine, and what bridge — if any — might close the gap.

The note is descriptive and exploratory. It does not declare a decision. It surfaces a structural question (what is ProblemForm optimizing for, and what is the evaluation framework measuring?) and proposes a working hypothesis about how M3B might address it. The hypothesis is meant to be designed against in the M3B planning work, not adopted as a settled position.

## Validated subset vs intended scope

The Constitution is the authoritative statement of what ProblemForm is for. Per `docs/problemform_constitution.md`:

> Your role is to collaborate with the user to identify, formulate, investigate, refine, and optimize the best possible version of **a problem, objective, decision, request, inquiry, question, or prompt**.

Seven input types are explicitly named. The Constitution then emphasizes that the deliverable is the *formulation*, not the answer, and that the formulation may be used by any audience — human or AI.

The current implementation, in its M1–M3A state, is **narrower than** the Constitution. This is not in conflict with the Constitution. It represents the **validated subset**: the part of the intended scope where the system has been built, exercised, and measured so far.

Specifically:

- The benchmark corpus at `benchmarks/default/` contains five cases, all questions (`cosmology_nothingness`, `code_review_prep`, `api_design_rest_vs_graphql`, `teach_kid_to_swim`, `what_causes_eclipses`).
- The phase prompts in `problemform/agents/` and the comparative judge in `problemform/eval/prompts/comparative_judge.py` use "question" and "answer" vocabulary throughout.
- The M3A benchmark framework compares `raw_answer` to `refined_answer`. Its headline metric is shaped around questions.

CLAUDE.md describes this state — a problem-formulation system whose current examples are prompts and questions. CLAUDE.md is a working document about the current implementation; it does not amend the Constitution. The validated subset is what the system has been measured on; the Constitution remains what the system is *for*.

The question worth asking is not which artifact is correct — all three are correct, each at its appropriate altitude. The Constitution states intended scope; CLAUDE.md describes the current implementation truthfully; the corpus is the slice of the intended scope where we have evidence. The structural question is: **how does the validated subset expand toward the intended scope, and what mechanism in the planned roadmap does that expansion?**

## A non-question input: the Aquinas case

Most input types named in the Constitution do not look like the corpus's five cases. To make the gap concrete, consider an input like this:

> My friend seems to think Thomas Aquinas proves the existence of God without a doubt. I argued that he's obviously creative and intelligent, but he's more like a narrative designer than anything. His stuff is more poetic and metaphorical than some people would like to accept. No disrespect to poetic, metaphorical language: I myself am being somewhat fuzzy in my language. It's just that I think another "Aquinas" type could fluff out their own details and those details would likely diverge at parts, but in a way that still fits the available evidence.

This is not a question. It is several things at once:

- An **argument** the user is making (Aquinas is more "narrative designer" than rigorous prover).
- A response to a friend's **argument** (the friend claims Aquinas proves God's existence).
- A partial **critique** (the "another Aquinas" thought experiment, which is implicitly an underdetermination argument).
- A **belief cluster** the user is in the middle of articulating ("I think... It's just that I think...").
- An **invitation to formulation** — the user is, implicitly, asking to think this through more clearly.

What ProblemForm's phases could do with this input:

- **Objective Analysis** — what is the user actually trying to do? Sharpen the critique? Understand Aquinas better? Find a way to talk to the friend? Settle their own position? The stated and inferred objectives may differ substantially.
- **Assumption Excavation** — assumptions in both the friend's claim ("proves without a doubt") and the user's response ("narrative designer," implicit standards for what counts as proof, the assumed contrast between rigorous and poetic).
- **Information Gap Detection** — what about Aquinas's actual arguments hasn't been engaged with? What does the user need to know to sustain this case?
- **Expert Panel** — a philosopher of religion, a logician, a historian of medieval thought, an analytic philosopher: each would phrase the question differently.
- **Alternative Framing** — the user has framed Aquinas as "narrative designer." Alternative framings: "Aquinas as systematic theologian," "the underdetermination of metaphysical claims by evidence," "the role of cumulative-case reasoning in natural theology."
- **Meta-Questions** — is the real issue about Aquinas, or about how the user and the friend disagree on what counts as evidence?
- **Synthesis** — a refined formulation of the user's argument that names what they're actually claiming, what they'd need to show, and what would change their mind.

There is no "answer" here in any natural sense. There is a *formulation*. The user is not asking "what should I think about Aquinas?" — they are working out what they already think, and want to do it more rigorously.

This is exactly the input shape the Constitution names ("problem," "inquiry," and implicitly "argument"). It is exactly the input shape the current benchmark cannot evaluate. M3A's contract — generate an answer and compare it to another answer — has no leverage on the Aquinas input.

The Aquinas case is one example of a much broader set: arguments, debate positions, research ideas, ambiguous situations, strategic decisions, belief critiques, personal dilemmas. None of them have a natural downstream "answer." All of them have a natural downstream *formulation*.

## The confound: what is the benchmark actually measuring?

This is, on reflection, the foundational observation.

M3A asks: *did the refined formulation lead to a better downstream answer?* It calls `raw_answer = answer_provider.generate_text(raw_question)` and `refined_answer = answer_provider.generate_text(refined_prompt)`, then asks a judge which is better.

But that comparison is the result of *two* things, not one:

1. **The formulation step.** Did ProblemForm produce a better-formulated input?
2. **The answerer step.** Did the answer model do a better job with the better-formulated input?

The judge compares the *answers*. The signal the judge produces is a product:

> M3A measures ≈ formulation_quality × answerer_response_to_formulation

This is a composite measurement, not a direct measurement of formulation quality. M3A measures **ProblemForm × Answer Model**, not ProblemForm.

The composite is *useful*: when it improves, something useful improved. But it is *confounded*: an improvement could come from formulation quality (good — that's what we want to measure), from the answer model happening to respond better to longer or more structured prompts regardless of substance (less good — that's verbosity bias surfacing differently), or from both.

For questions, the composite is reasonable. We care about the eventual answer; the composite signal is close to what we want.

For the Aquinas case — and for arguments, beliefs, decisions, dilemmas generally — the composite does not even compute. The answerer step has no natural completion. What does "answer" the Aquinas input mean? Without a natural downstream artifact, M3A cannot operate.

This is the deepest version of the gap between validated subset and intended scope. The validated subset is the set of inputs where the composite signal is well-defined and reasonable. The intended scope includes inputs where it is not.

What would change if we measured the formulation directly?

- We would get an **unconfounded signal for ProblemForm's actual output**. The formulation is what ProblemForm produces; judging it directly measures ProblemForm, not ProblemForm × Answer Model.
- We would **separate formulation quality from answerer quality**. For questions, this gives us a complementary lens to M3A. Disagreements between the two lenses would themselves be a signal worth investigating.
- For non-questions, **we would have an evaluation contract at all.** Today there is none.

This confound observation is, in some ways, more fundamental than the Path A vs Path B framing in the next section. Path A vs Path B is one specific design response to it. Other responses are conceivable. The confound is the structural fact the responses are responding to.

## Path B as a candidate generalization

Two evaluation paths are available for any extension of the framework beyond the current question-only setup:

- **Path A — judge the downstream artifact.** What M3A does today. Each input type would get a category-specific downstream artifact (question → answer, argument → steelman or critique, decision → recommendation under constraints). The judge compares raw-artifact to refined-artifact within each category. Signal is confounded with the artifact-generator's quality, as above.
- **Path B — judge the formulation directly.** No downstream artifact. The judge looks at the formulation itself and scores it against category-agnostic criteria: clarity, completeness, surfacing of hidden assumptions, naming of central claim, identification of what would change minds, articulation of relevant constraints. This is the "prompt-target" judgment listed as deferred Phase B work in `docs/designs/milestone_03_evaluation_framework.md`.

Path B is **promising** as a generalization path because:

- It produces an unconfounded signal: formulation quality, not formulation × answerer.
- It applies to input types where Path A is undefined (Aquinas, arguments, beliefs, decisions, dilemmas).
- It honors the Constitution's framing that "the deliverable is the formulation, not the answer."

Path B is **not obviously the right answer** because:

- For questions, where Path A is well-defined and the downstream answer is real signal, Path B may discard useful information about whether the refined formulation actually leads anywhere useful.
- "Judge the formulation directly" is more abstract than "judge the answer." Rubric criteria for formulation quality need to be specified carefully or judgments become subjective.
- Whether human judges agree with LLM judges on formulation quality, the way they roughly do on answer quality, is unknown territory.
- Path B may have its own calibration problems — judges may over-prefer verbose or structured formulations independent of whether they're actually better.

A hybrid is possible and arguably attractive: Path A as the primary lens for questions (where the downstream answer is a real signal); Path B as the primary lens for non-questions (where Path A is undefined); both available for any case, and disagreements between them treated as signal worth investigating.

The hypothesis worth investigating is: **Path B is a plausible generalization mechanism beyond questions, and M3B is the natural milestone in which to introduce it.** It is not a settled fact.

## Is M3B the bridge?

M3B is currently planned as rubric evaluation and property checks. Whether these mechanisms are an implementation of Path B depends on a design choice in M3B itself: what is the evaluation target?

Two readings of M3B remain available:

- **M3B-as-continuation.** Target is the answer, as in M3A. Rubrics and property checks score answers more sophisticatedly than the current single-judge comparison. M3A's confounded signal becomes a richer confounded signal.
- **M3B-as-bridge.** Target is the formulation (and possibly the answer too, as a secondary). Rubrics score formulations on criteria that make sense for non-questions. Property checks verify formulations satisfy expected properties (e.g., "the refined formulation names its central claim," "makes the assumption-set explicit"). The framework becomes capable of evaluating inputs M3A cannot reach.

These readings are not mutually exclusive at the framework level. A sufficiently general M3B design treats `target` as a first-class parameter — each rubric and property check names its target, and the engine handles either or both.

Reasons to consider M3B-as-bridge as a working hypothesis:

- It produces a measurement instrument for the parts of the Constitution M3A can't reach.
- It separates formulation quality from answerer quality.
- Designing for `target ∈ {formulation, artifact}` from the start is a single design parameter — cheap to include initially and expensive to retrofit later.
- It honors the Constitution's framing more directly than M3A does.

Reasons to be cautious:

- Path B's calibration is unknown territory.
- It is conceivable that the validated subset (questions, with the M3A composite signal) is actually the part of the intended scope the project most cares about, and the broader scope is aspirational rather than operative.
- It is conceivable that ProblemForm-for-questions is a more useful and shippable product than ProblemForm-for-arguments-and-beliefs, even if the Constitution describes the broader scope.

This note proposes adopting **M3B-as-bridge as a working hypothesis** — a frame to design against in the M3B planning work — without committing the project to it. The M3B design pass should be the milestone that confirms, modifies, or rejects the hypothesis.

## Observations

These are stated as observations only — not as recommendations, conclusions, or decisions.

1. The benchmark corpus is 100% questions.
2. The Constitution names seven input types; questions are one.
3. The phase architecture generalizes naturally to non-question inputs (the Aquinas case walks through what each phase would do); the evaluation framework does not.
4. M3A measures a composite of formulation quality and answerer quality. Its signal is `ProblemForm × Answer Model`, not ProblemForm.
5. For non-question inputs, M3A's contract has no natural completion. The framework cannot operate on them at all.
6. M3B's planned mechanisms (rubrics, property checks) are scope-agnostic. Their evaluation target is a design choice not yet made.
7. The original vision in the Constitution remains the authoritative statement of scope. The implementation has, over the course of M1–M3A, matured more rapidly along the question dimension than along the other Constitution-named dimensions.

## Working hypotheses (to be tested in the M3B design pass)

These are hypotheses to design against, not decisions:

- **H1.** Path B is a viable generalization path beyond questions. (Plausibly true based on the confound argument; unknown until exercised.)
- **H2.** M3B's mechanisms (rubrics, property checks) are scope-agnostic enough to implement Path B if designed with `target ∈ {formulation, artifact}` as a first-class axis. (Likely true; design needs to confirm.)
- **H3.** Adopting M3B-as-bridge as the working framing — rather than M3B-as-continuation — is the more strategically valuable choice. (The recommendation of this note; the M3B design pass should test it.)
- **H4.** If H1–H3 hold, the implied ordering for downstream issues is #8+#9 (M3B design, together) → #6 (corpus expansion, rescoped to category diversity) → #7 (calibration, with both Path A and Path B available). If they don't, the previous ordering may stand.

The M3B design pass is the natural venue for testing all four. The point of this note is to bring the hypotheses into focus *before* that design work begins, so they can be addressed deliberately rather than by default.

## Implications for #6, #7, #8, #9 (as one possible ordering)

If the M3B-as-bridge hypothesis survives the M3B design pass, the implied dependency ordering on the four open issues is:

1. **#8 + #9 (M3B design, together).** Rubric and property-check design share questions about target, schema, scoring, aggregation. Designed in isolation, they risk inconsistency. Designed with Path B in mind, they become the bridge.
2. **#6 (corpus expansion), rescoped.** Once Path B is supported, expansion has a clear shape: category diversity, not raw count. Suggested first tranche: arguments, decisions, belief critiques (the Aquinas case is a natural prototype for the "argument / belief critique" category). Target: ~12–15 cases across 4–5 input types.
3. **#7 (calibration).** The 100% refined-win rate is more interpretable in a world with Path B and a diversified corpus. If formulation-judging corroborates the answer-comparison signal on questions, the original number is reinforced. If it doesn't, we have a real finding. Either way, the answer is more reachable after #8+#9 and the rescoped #6.

If the hypothesis is rejected during the M3B design pass, the previous implicit ordering (#7 or #6 before #8+#9) is reasonable. The point of separating the M3B design pass from the rest is to give the hypothesis a place to live or die before downstream work commits to it.

## Open questions for the M3B design pass

- **Q1.** Is `target ∈ {formulation, artifact}` a clean first-class axis for rubrics and property checks, or does it complicate the design enough that splitting M3B into two parallel frameworks (one per target) is better?
- **Q2.** What criteria does a "formulation-quality rubric" use? Path B's value depends on whether such criteria can be specified precisely enough for reliable judgment.
- **Q3.** How does Path B handle position bias, verbosity bias, and self-preference bias? The M3A mitigations (position randomization, label-agnostic prompts, same-family warnings) may or may not transfer.
- **Q4.** What is the natural unit of comparison in Path B? Raw-formulation vs refined-formulation (analogous to M3A's raw vs refined)? Single-formulation absolute score? Relative score across alternative framings? The choice affects what calibration looks like.
- **Q5.** For inputs where the user's intent is *partially* a question and *partially* something else — including most real-world inputs — does the framework need to detect input type and route to Path A or Path B, or does Path B subsume Path A as a useful generalization?

These questions are the agenda for the M3B design pass. They do not need answers in this document.

## What this document does not do

- It does not declare M3B-as-bridge as the final design intent.
- It does not commit to a corpus expansion shape.
- It does not propose any code change.
- It does not amend the Constitution. The Constitution remains the authoritative statement of intended scope.

It surfaces a structural question, proposes a working hypothesis, and identifies what the M3B design pass would need to settle. The substantive design work follows.
