# M3B-alpha Close-out Review by Codex

## Findings

### Must Fix Before Closing M3B-alpha

1. **H2 validation report misstates the experiment setup.**  
   [m3b_alpha_validation_2026-07-08.md](/Users/kevin/github/problemform/docs/reports/m3b_alpha_validation_2026-07-08.md:215) says the M3A answer comparison was “suppressed,” but the preserved H2 reports show answer generation, comparative judge time, and M3A tie verdicts ([report_run1.md](/Users/kevin/github/problemform/docs/reports/m3b_alpha_h2_2026-07-09/report_run1.md:32), [report_run1.md](/Users/kevin/github/problemform/docs/reports/m3b_alpha_h2_2026-07-09/report_run1.md:61)). The H2 conclusion still rests on the formulation rubric, but the historical setup description should be corrected before closure.

2. **User-facing docs still describe M3 as Phase-A-only.**  
   The README evaluation section describes only answer-comparison evaluation ([README.md](/Users/kevin/github/problemform/README.md:47)), and its roadmap still lists rubric/property evaluation as planned ([README.md](/Users/kevin/github/problemform/README.md:296)). `docs/cli_commands.md` also omits `--rubric` and `--property-suite` from the benchmark invocation and workflow ([cli_commands.md](/Users/kevin/github/problemform/docs/cli_commands.md:221)). This conflicts with the implemented M3B-alpha surface.

## Answers To Close-out Questions

1. **Is the implementation internally consistent?**  
   Yes. The model, runner, engine, CLI, and report layers consistently preserve the three lenses: M3A comparative answer judgment, rubric evaluations, and property checks. Runtime accounting now includes rubric/property time, and expected properties activate as `target=formulation`.

2. **Do implementation, docs, corpus, validation reports, and design docs agree?**  
   Mostly, but not fully. The design doc, benchmark corpus, property README, backlog, implementation, and validation conclusions are broadly aligned. The remaining disagreements are the H2 setup wording and stale README/CLI docs above.

3. **Did H1 and H2 test the intended hypotheses?**  
   Yes, within alpha scope. H1 tested formulation-rubric consistency and relationship to M3A on the five question cases. H2 tested whether the same formulation rubric produced coherent, discriminating scores on the Aquinas argument case.

4. **Anything materially weakening confidence in H1/H2?**  
   Nothing that invalidates the conclusions, but confidence is appropriately limited. H1 used same-family OpenAI answer/judge setup; H2 covers only one non-question type; all runs are K=1 and small sample. These limitations are explicitly documented. The H2 setup misstatement weakens the historical record, not the rubric evidence itself.

5. **Remaining correctness bugs, documentation inconsistencies, or architecture issues?**  
   No visible implementation blocker. Documentation needs the two fixes above. Architecturally, separate M3A-vs-lens error accounting is already documented as future work, and the current asymmetry is acceptable for alpha closure.

## Appropriate Future Work For M3B-beta

- Diversify beyond the single Aquinas argument into decisions, beliefs, dilemmas, and additional non-question types.
- Calibrate rubric floors, disagreement thresholds, and K > 1 / multi-judge behavior.
- Add comparative-mode rubrics and formulation-only benchmark mode if future validation needs them.
- Harden Anthropic JSON structured output if used at larger scale.

## Optional Observations

- The implementation comments claim activated expected-property names are case-unique, but slugs are based on text plus index only. Current corpus does not appear affected; future corpus expansion may want case-qualified names or explicit property IDs.
- The design doc still has one broad sentence saying both rubrics and property checks carry target and mode, while property checks are actually target-only and absolute-mode. Nearby sections clarify this, so it is not a blocker.

## Verification Note

I attempted to run the suite with `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider`, but this environment lacks `pytest`.

## Conclusion

**Approve closure with minor reservations**


----------------------
----------------------
----------------------


# Feedback to Claude
Codex approves M3B-α closure with minor reservations. Please fix the two must-fix documentation issues before we formally close the milestone:

1. In `docs/reports/m3b_alpha_validation_2026-07-08.md`, correct the H2 setup wording. The M3A answer comparison was not suppressed; answer generation and comparative judging still ran. The correct statement is that M3A was ignored / treated as non-authoritative for H2, while the formulation rubric was the instrument under evaluation.

2. Update the user-facing docs so they reflect the implemented M3B-α surface:
   - README evaluation section should no longer describe M3 as only answer-comparison evaluation.
   - README roadmap should not describe rubric/property evaluation as merely planned.
   - `docs/cli_commands.md` should include the benchmark `--rubric` and `--property-suite` flags and explain default loading / explicit override behavior.

Do not make code changes. Keep this as a documentation closure patch only. After this, I’m comfortable declaring M3B-α complete.