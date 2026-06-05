# Backlog

This file is the canonical record of ideas, design speculation, and tracked-but-not-committed work for ProblemForm. It exists to capture reasoning that doesn't belong in `docs/roadmap.md` (which is intentionally high-level and milestone-shaped) and isn't yet active work (which would warrant a GitHub issue).

Conventions:

- One section per idea. Two sub-sections: **Problem** (one-line framing of what's being asked) and **Discussion** (tradeoffs, prior reasoning, recommended direction if any).
- Entries are not commitments. Anything that moves from speculation to planned work should be cut as a GitHub issue (and optionally promoted to `docs/roadmap.md` or a `docs/designs/` document if the scope justifies it).
- When an entry's question is answered — by a decision, an implementation, or by being rejected — move it to the **Resolved** section at the bottom with a one-line note and link to the deciding artifact (commit, issue, design doc).
- Keep entries concise. If an entry grows past a few paragraphs of substance, that's a signal it should graduate to a `docs/designs/` document.

---

## Benchmark Progress & Runtime Visibility

### Problem

Benchmark runs can take many minutes and incur non-trivial API costs, but currently provide almost no runtime visibility. Users see only a start message and then wait for final results.

### Discussion

The first real benchmark run exposed a usability problem: it is difficult to distinguish a healthy long-running benchmark from a hung process.

Potential improvements:

- Progress bar (N of M cases completed)
- Current case name
- Elapsed runtime
- Per-case timing breakdown
- Optional token/cost estimates
- Rich live status updates

The value is operational rather than analytical. Better visibility reduces uncertainty during long benchmark runs and makes future benchmarking work easier.

Recommended direction: implement before substantial corpus expansion or large-scale benchmarking. Visibility will become more important as evaluation suites grow.

---

## Benchmark Cost, Runtime, and Model Ablation Studies

### Problem

The first benchmark run (~5 cases) consumed approximately 15 minutes and roughly $1 of API usage when using GPT-5.4 for all roles. The project currently has little visibility into the tradeoff between model quality, runtime, and evaluation stability.

### Discussion

The evaluation framework introduces three independent model roles:

- ProblemForm
- Answer Generator
- Comparative Judge

These roles may not require identical model capability.

Potential experiments:

- Hold Judge constant while reducing Answer model size.
- Hold Answer constant while reducing Judge size.
- Reduce ProblemForm model size.
- Evaluate mixed-family configurations.

The goal is to identify a "sweet spot" where benchmark outcomes remain stable while cost and latency decrease substantially.

Future tooling may include benchmark sweeps or matrix experiments.

Recommended direction: gather baseline data before implementing automation.

---

## Prompt-Distance and Answer-Distance Instrumentation

### Problem

The system currently evaluates prompt refinement through comparative judgments, but does not directly measure how much prompts or answers change between iterations.

### Discussion

Potential measurements include:

- Prompt₀ ↔ Prompt₁ distance
- Prompt₀ ↔ Promptₙ distance
- Promptₙ₋₁ ↔ Promptₙ distance
- Raw answer ↔ refined answer distance

Possible uses:

- Detect over-refinement
- Detect near-convergence
- Identify large prompt changes that produce negligible answer changes
- Identify small prompt changes that produce large answer changes
- Generate future convergence heuristics

The measurements are intended initially as instrumentation rather than decision-making inputs.

Open question: whether distance should be semantic, embedding-based, judge-based, or derived from multiple signals.

Recommended direction: collect metrics first, interpret later.

---

## Benchmark Corpus Expansion and Benchmark Validity

### Problem

The current benchmark corpus contains only five cases. Early benchmark results showed 100% refined wins and 0% raw wins or ties, raising questions about corpus representativeness and evaluation validity.

### Discussion

Possible explanations:

- The corpus genuinely favors refinement.
- The judge is too permissive.
- Same-family judging influences results.
- Tie criteria are under-specified.
- The corpus lacks sufficient control cases.

Future corpus goals:

- Increase size substantially (20-30+ cases).
- Add additional control cases.
- Add cases where refinement is expected to have little effect.
- Add cases where refinement may plausibly make results worse.
- Improve domain diversity.

The benchmark should remain a measurement tool rather than an advocacy artifact.

Recommended direction: expand the corpus before drawing strong conclusions from aggregate win rates.

---

## Benchmark Outcome Calibration (100% Refined Wins)

### Problem

The first benchmark run produced 100% refined wins, 0% raw wins, 0% ties, and 0% degradations.

### Discussion

This result is encouraging but difficult to interpret.

Possible explanations include:

* ProblemForm genuinely improved all five cases.
* The corpus naturally favors refinement.
* The judge underuses ties.
* Same-family judge bias.
* Materiality thresholds are too strict or too weak.
* The control case is insufficiently adversarial.

Questions worth investigating:

* Do results hold with cross-family judges?
* Do results hold with multiple judges?
* Do humans agree with the benchmark outcomes?
* Does the tie rate remain near zero as the corpus grows?
* Can deliberately poor refinements produce expected degradations?

Recommended direction: treat early benchmark results as framework validation rather than evidence of ProblemForm effectiveness.

⸻

## Rubric Framework Design (M3B)

### Problem

Phase A evaluates answer quality using comparative judgments only. Phase B introduces rubric-based evaluation, but important design decisions remain unresolved.

### Discussion

Open questions include:

* Rubric schema design.
* Criterion weighting.
* Criterion aggregation.
* Whether rubric scores should ever be aggregated into a single number.
* Judge prompts for criterion scoring.
* Reporting format.
* Handling disagreements between rubric outcomes and comparative judgments.

The design document establishes the architectural direction, but implementation details remain open.

Recommended direction: create a dedicated design document before implementation begins.

⸻

## Property Check Framework Design (M3B)

### Problem

Phase B introduces expected-property evaluation, but the implementation strategy remains intentionally deferred.

### Discussion

Property checks are intended to answer questions such as:

* Did the answer address the requested audience?
* Did the answer remain technically accurate?
* Did the answer provide actionable next steps?
* Did the answer avoid known failure modes?

Open questions include:

* Property specification format.
* Judge prompts.
* Binary vs graded scoring.
* Relationship to rubric evaluation.
* Reporting and aggregation.
* Whether properties are corpus-wide or test-case-specific.

The architecture already assumes LLM-based evaluation rather than code-based checks, but significant design work remains.

Recommended direction: treat property checks as a separate subsystem rather than a small extension of comparative judging.

---

## Per-role provider/model overrides for the workflow's Convergence Judge

### Problem

Should the workflow's Convergence Judge (the `convergence_evaluation` phase in `run` and the standalone `problemform judge` command) accept its own provider/model, analogous to the `PROBLEMFORM_EVAL_JUDGE_*` variables that the benchmark's Comparative Answer Judge already supports?

### Discussion

The mild case for: a model judging the materiality of its own prompt synthesis is a soft form of self-preference, and cross-family judging would mitigate it. A user might also want to run analytical phases on a cheap/fast model and reserve a smarter model for convergence decisions.

The case against is stronger:

- The capability already exists manually. `problemform run --save state.json && problemform judge --state state.json --provider anthropic` gets a second-opinion convergence verdict from a different family today. The unmet need is *automation inside the loop*, not the underlying capability.
- Splitting providers mid-pipeline introduces a new failure surface — a misconfigured judge provider can fail seven phases into a run instead of immediately.
- Once the convergence judge gets its own provider, the natural next question is "why not synthesis? why not the divergent phases?" Per-phase provider overrides is a real feature with real surface area; introducing it via one env var is worse than not introducing it at all.
- The self-preference concern is qualitatively weaker than in the comparative answer judge. The convergence judge compares two of the *user's* prompts; the comparative answer judge picks between two outputs of competing models. The bias geometry is different.

Recommended direction: defer. Make the existing manual `problemform judge --provider …` escape hatch more visible in docs. Revisit if multiple users ask for in-loop split.

---

## Augment Convergence Judge with answer-quality measurement (additive, not replacement)

### Problem

The Convergence Judge today reads prompt v_{n-1} and v_n and predicts whether a competent answerer would respond meaningfully differently. The prompt-delta signal is fast, structural, and cheap (one LLM call). Should the convergence decision *also* consult an answer-quality measurement — actually generating answers to both prompts and comparing them — alongside the existing prompt-delta judgment, so the loop has both a structural signal ("did the formulation change?") and an outcome signal ("did the change help?")?

### Discussion

The intent is additive, not a replacement. Prompt-delta stays as the always-on primary signal; answer-quality is added as a complementary outcome signal that the loop can consult to detect degradation and to confirm that meaningful prompt changes are actually producing better answers.

Case for adding the answer-quality signal:

- Catches degradation. Today's loop can return NOT_CONVERGED on a meaningfully changed prompt that actually produces a *worse* downstream answer; the loop then iterates further on a regression. With answer-quality in the mix, the loop can flag this and either stop or revert.
- Closes the gap with the eval framework. The workflow's convergence decision and the benchmark framework end up looking at the same outcome dimension, reducing the risk that "converged" and "improved" diverge.
- Sequential layering keeps cost contained. Prompt-delta first; answer-quality runs only on borderline (NEAR_CONVERGENCE) or first-pass verdicts. Default cost profile of `run` only changes when the user opts in.
- The conceptual conflation that worried the earlier replacement framing largely dissolves under the additive framing. Prompt-delta still answers "did the formulation change?"; answer-quality answers "did the change help?". Both are independently surfaced.

Design questions to resolve before implementing:

1. **Combination rule.** How do the two signals jointly produce a convergence verdict? Candidates:
   - **AND-style:** CONVERGED only when prompt delta is small *and* the new prompt's answer is not materially better than the previous one's. Tightest stop criterion.
   - **Prompt-delta-primary with degradation override:** today's prompt-delta verdict drives the status, but a `degradation` flag from the answer-quality check forces NOT_CONVERGED + a revert recommendation. Cheapest to bolt on.
   - **Two independent verdicts persisted on `ProblemState`:** keep both signals visible and let downstream tooling (and humans inspecting `explain`) decide. Most flexible; pushes decision logic out of the judge.
2. **When to run.** Every iteration, or only on borderline prompt-delta verdicts? The latter is cheaper and may be sufficient.
3. **Determinism.** Answer generation adds variance. Should we fix temperature=0 for the answer generation in this context, or accept that the augmented signal is noisier than the current one?

Costs that remain regardless of framing:

- Each iteration that runs the answer-quality check adds two answer generations + one comparative judgment (~3 extra LLM calls), possibly across three providers.
- The opt-in flag interface (`problemform run --measure-answer-quality`) is the sensible default; making the check unconditional would noticeably change the cost profile of every `run`.

Recommended direction: keep prompt-delta as the always-on, primary convergence signal. Add answer-quality as an opt-in *augmenting* signal behind `--measure-answer-quality`, with the combination rule scoped before implementation. Gated on M3 reaching a stable benchmark suite so the in-loop measurement can be validated against the external one.

---

## Resolved

_None yet._
