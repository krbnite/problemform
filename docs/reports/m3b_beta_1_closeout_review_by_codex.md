---
title: "M3B-β.1 Close-out Review by Codex"
document_type: "report"
status: "active"
created: "2026-07-10"
updated: "2026-07-10"
author: "Codex"
authoritative_reference: "docs/plans/m3b_beta_1_plan_by_claude.md"
related:
  documents:
    - "docs/designs/m3b_beta_corpus_diversification.md"
    - "docs/plans/m3b_beta_0_plan_by_claude.md"
    - "docs/plans/m3b_beta_1_plan_by_claude.md"
    - "docs/backlog.md"
scope:
  inspected:
    - "problemform/eval/policy.py"
    - "problemform/eval/models.py"
    - "problemform/eval/engine.py"
    - "problemform/eval/report.py"
    - "problemform/cli.py"
    - "tests/test_eval_policy.py"
    - "tests/test_eval_models.py"
    - "tests/test_eval_engine.py"
    - "tests/test_eval_report.py"
    - "tests/test_eval_cli.py"
    - "docs/designs/m3b_beta_corpus_diversification.md"
    - "docs/plans/m3b_beta_1_plan_by_claude.md"
    - "README.md"
    - "docs/cli_commands.md"
    - "benchmarks/README.md"
    - "benchmarks/"
---

# M3B-β.1 Close-out Review by Codex

## Executive Summary

The M3B-β.1 implementation is architecturally sound and matches the approved plan in the core code paths. The new `FormulationPolicy` registry is the right abstraction for β.1 and future β.2 extension. The engine gates the M3A answer-comparison lens by formulation type, preserves answerable and `unspecified` legacy behavior, keeps skipped cases distinct from answer-lens errors, and preserves the M3B-α.4 aggregate contract that rubric/property errors do not invalidate a completed M3A verdict.

I found no correctness bug in the implementation that should block the code from being accepted. The main closure blocker is documentation consistency: current user-facing benchmark docs and CLI help still describe the answer lens as if it always runs and answer artifacts always exist. That contradicts β.1 behavior and should be reconciled before formally closing the milestone.

## Must Fix Before β.1 Closure

1. **User-facing benchmark docs/help still describe the pre-β.1 always-answer workflow.**

   The implemented behavior is now conditional: formulation-only cases and `--no-answer-comparison` skip answer generation, skip comparative judging, may build no answer provider, and do not write `raw_answer.txt` / `refined_answer.txt`. The approved plan requires this behavior, and the code implements it.

   The public docs and help still say otherwise:

   - `docs/cli_commands.md` describes `benchmark` as comparing answers from the raw question and refined prompt, omits `--answer-comparison/--no-answer-comparison`, lists answer generation as unconditional steps 2-4, and lists answer text artifacts as unconditional outputs.
   - `README.md` still describes the comparative lens and answer provider as if every benchmark run uses them, and the output example always includes answer artifacts.
   - The `problemform benchmark --help` text is generated from the CLI docstring, which still says the Answer provider generates raw/refined answers and the Judge compares them, without noting policy-based skipping.
   - `benchmarks/README.md` still says `expected_properties` are "stored but not evaluated" in Phase A, even though M3B-α.4 activates them as formulation-target property checks in every run.

   These are documentation/help inconsistencies, not implementation failures, but they are current-facing contracts. They should be fixed before β.1 is declared closed.

## Should Fix

1. **Add automated CLI coverage for `--answer-comparison` force-on and per-type all-skipped runs.**

   Engine tests cover force-on/force-off, and CLI tests cover `--no-answer-comparison` over the default suite. I manually verified `--answer-comparison` over `benchmarks/decisions` with stubs: it built the answer provider, made four answer calls, completed both cases, and recorded `answer_comparison = forced_on`. I also manually verified omitted override over `benchmarks/decisions`: it built no answer provider and recorded `not_used`. These should be permanent CLI tests.

2. **Refine the all-`n_completed == 0` report wording for all-error runs.**

   `report.py` currently prints the "No answer-comparison verdicts... See the Rubric evaluations section" note whenever `n_completed == 0`. That is ideal for all-skipped formulation-only runs, but less precise when all answer-applicable cases failed. The Errors section still preserves the truth, so this is not a closure blocker. A small conditional could distinguish "all skipped" from "all answer comparisons failed."

3. **Consider making the direct `_run_one_case` optional-answer invariant explicit.**

   `run_benchmark` correctly raises early if `answer_provider is None` while any case is answer-applicable. `_run_one_case` relies on that caller guard. This is acceptable because `_run_one_case` is internal, but an explicit local assertion or error would make the invariant self-documenting.

## Future Work (β.2+)

- Type-aware default rubric/property selection belongs in β.2. β.1 intentionally leaves default answer-side rubrics/properties loaded; artifact-target lenses naturally skip empty answer subjects when the answer lens is off.
- Comparative formulation rubrics remain β.3 work.
- Full per-lens error accounting remains deferred. β.1 correctly preserves the current answer-lens aggregate contract while keeping errors visible in `errors[]`, progress, and the report's Errors section.
- Multi-type report sectioning and richer type-level summaries remain later reporting work.
- Broader prompt/question vocabulary cleanup remains outside β.1.

## Optional Observations

- The `FormulationPolicy` registry is compact and extensible. Sharing `_ANSWERABLE` and `_FORMULATION_ONLY` policy instances is fine because `FormulationPolicy` is frozen.
- The import-time registry coverage assertion in `policy.py` is useful, and tests also enforce it. If the project ever runs Python with optimized assertions disabled, the test remains the durable guard.
- The duplicate `cosmology_nothingness` case under `benchmarks/default` and `benchmarks/simple` remains present, but the β.0 plan explicitly allowed that because `simple/` is a scratch suite unlikely to be co-run. It is not a β.1 issue.

## Verification

Commands and checks performed:

- `git status --short` before review: clean worktree.
- Inspected recent commits:
  - `6aec584 feat(eval): add formulation-type policy registry + answer-lens fields (M3B-β.1.1)`
  - `94fce93 feat(eval): gate the M3A answer-comparison lens by formulation type (M3B-β.1.2)`
  - `1cc0959 Fix Benchmark: fix additional errors in manager dilemma file`
- `.conda/bin/python -m pytest -q -p no:cacheprovider`
  - Result: `258 passed in 2.23s`.
- Loaded the benchmark case corpus across `default`, `simple`, and the 10 non-default type directories:
  - 25 cases loaded.
  - All case `formulation_type` values are canonical.
  - The 11 canonical formulation types are represented.
  - The only duplicate case name is the known `cosmology_nothingness` default/simple duplicate allowed by the β.0 plan.
- Manually exercised CLI β.1 paths with deterministic stubs:
  - `--answer-comparison` over `benchmarks/decisions`: exit 0, answer provider built, 4 answer calls, `n_completed = 2`, `n_answer_skipped = 0`, config `answer_comparison = forced_on`.
  - Omitted override over `benchmarks/decisions`: exit 0, no answer provider built, `n_answer_skipped = 2`, config `answer_provider = not_used`, `answer_comparison = per_type_policy`.
- Inspected report rendering for skipped-case matrix and aggregate headline behavior.

## Close-out Questions

1. **Is the implementation internally consistent?**

   Yes. The policy registry, model defaults, engine gating, aggregate buckets, report rendering, and CLI provider construction all agree on the β.1 contract.

2. **Does the implementation match the approved β.1 design and plan?**

   Yes for implementation. The code implements the approved type split, fallback behavior, tri-state override, lazy answer-provider construction, `not_used` config, direct API guard, skipped-case report rendering, and α.4 aggregate preservation.

3. **Are skipped answer comparisons distinct from errors?**

   Yes. `answer_comparison_applicable=False` marks an intentional lens skip. Skipped cases remain in `n_answer_skipped`, even if they carry PF/rubric/property errors. Those errors remain visible through `errors[]`, progress, and report rendering.

4. **Are aggregation semantics internally consistent and α.4-compatible?**

   Yes. `n_cases == n_completed + n_errored + n_answer_skipped`, with buckets decided by answer-lens status only. An answer-applicable case with a completed comparative judgment remains completed even if a rubric/property lens fails.

5. **Do answer-lens assumptions remain elsewhere?**

   Not in the core implementation. Remaining assumptions are in user-facing documentation/help text, listed above as the closure blocker.

## Conclusion

The β.1 implementation is approved architecturally and behaviorally, but I recommend **not formally closing M3B-β.1 until the user-facing benchmark docs/help are updated** to describe conditional answer-lens execution.

**Approve implementation; defer formal closure pending documentation reconciliation.**
