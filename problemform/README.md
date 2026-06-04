models.py
    Pydantic data structures: ProblemState, per-phase artifact and result envelope models, Phase / ConvergenceStatus literals.

config.py
    Loads .env (OPENAI_API_KEY, ANTHROPIC_API_KEY).

core/state.py
    Immutable state helpers: initialize_state (seeds v0), transition_to_phase.

core/workflow.py
    Phase functions, pipeline tables (ANALYSIS_PHASES / SYNTHESIS_PHASES / JUDGMENT_PHASES / FULL_PIPELINE),
    run_pipeline runner, and the entry points analyze / synthesize / judge / run.

core/language_models.py
    LLMProvider Protocol, OpenAIProvider and AnthropicProvider (lazy SDK imports),
    make_provider factory.

agents/<phase>.py
    One PROMPT constant per phase. agents/__init__.py re-exports each prompt
    under the uniform name <PHASE>_PROMPT.

cli.py
    Typer commands: analyze, synthesize, judge, run, agent, explain, export.

cli_render.py
    Markdown rendering of ProblemState (delta-primary Convergence section).
