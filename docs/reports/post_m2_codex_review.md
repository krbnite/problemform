This review occurred just after completing milestone It is a review of commit hash 
81cf83373645bfca6f587502f737bfc75397443a

-------------------------------

# Codex says...
Plan-only review completed. I did not modify tracked files. I also could not run the test suite because this environment is missing `pytest`, `pydantic`, and `typer`.

**High Priority**
- `pyproject.toml` allows incompatible dependency versions. The code uses Pydantic v2 APIs like `model_validate_json`, `model_dump_json`, and `model_copy`, but the dependency is just `pydantic` with no `>=2` bound: [pyproject.toml](/Users/kevin/github/problemform/pyproject.toml:7), [models.py](/Users/kevin/github/problemform/problemform/models.py:123), [cli.py](/Users/kevin/github/problemform/problemform/cli.py:63). A fresh install could resolve Pydantic v1 and fail at runtime.
- `problemform agent` bypasses phase transition bookkeeping. The normal pipeline calls `transition_to_phase` before each handler, but the `agent` command calls the handler directly, leaving `ProblemState.phase` stale: [workflow.py](/Users/kevin/github/problemform/problemform/core/workflow.py:333), [cli.py](/Users/kevin/github/problemform/problemform/cli.py:226). Existing CLI tests do not assert phase updates.
- CLI error handling is uneven. Only `agent` catches malformed state JSON; `synthesize`, `judge`, `explain`, `export`, and `analyze --state` can surface raw validation/file/provider tracebacks: [cli.py](/Users/kevin/github/problemform/problemform/cli.py:59), [cli.py](/Users/kevin/github/problemform/problemform/cli.py:131), [cli.py](/Users/kevin/github/problemform/problemform/cli.py:221).
- Provider response handling needs hardening. Anthropic responses are joined without checking `stop_reason`, truncation, refusal, or empty content before JSON validation: [language_models.py](/Users/kevin/github/problemform/problemform/core/language_models.py:113), [language_models.py](/Users/kevin/github/problemform/problemform/core/language_models.py:122), [language_models.py](/Users/kevin/github/problemform/problemform/core/language_models.py:146). Anthropic’s docs explicitly recommend checking stop reasons.

**Medium Priority**
- Base install likely surprises CLI users. Provider SDKs are optional extras, but the default provider is OpenAI, so `pip install problemform` plus `problemform run ...` can fail unless users know to install `[openai]`: [pyproject.toml](/Users/kevin/github/problemform/pyproject.toml:14), [language_models.py](/Users/kevin/github/problemform/problemform/core/language_models.py:161).
- `--max-iterations` accepts zero or negative values, which returns an initial state without a final prompt while appearing successful: [cli.py](/Users/kevin/github/problemform/problemform/cli.py:159), [workflow.py](/Users/kevin/github/problemform/problemform/core/workflow.py:381).
- Prompt-injection resilience is limited. System instructions and untrusted `ProblemState`/raw user input are combined into one user prompt, and provider calls usually pass no meaningful `system` message: [workflow.py](/Users/kevin/github/problemform/problemform/core/workflow.py:44), [language_models.py](/Users/kevin/github/problemform/problemform/core/language_models.py:80). This is not tool-dangerous yet, but it matters before MCP/external tools.
- Documentation drift is real. `docs/cli_commands.md` duplicates the `agent` section and includes malformed examples like `bash problemform ...`: [docs/cli_commands.md](/Users/kevin/github/problemform/docs/cli_commands.md:212). `problemform/README.md` references non-existent modules: [problemform/README.md](/Users/kevin/github/problemform/problemform/README.md:7). `docs/roadmap.md` still mentions old command names like `assess/refine`: [docs/roadmap.md](/Users/kevin/github/problemform/docs/roadmap.md:35).
- Packaging metadata is thin: no README, license metadata, authors, classifiers, or dependency lower bounds beyond Python: [pyproject.toml](/Users/kevin/github/problemform/pyproject.toml:1).

**Low-Priority Polish**
- `config.py` reads API keys into module globals that are not used; its main effect is `load_dotenv()`: [config.py](/Users/kevin/github/problemform/problemform/config.py:1).
- `ProblemState.add_prompt_version` mutates in place while the core workflow otherwise uses immutable `model_copy` updates: [models.py](/Users/kevin/github/problemform/problemform/models.py:138), [state.py](/Users/kevin/github/problemform/problemform/core/state.py:15).
- Add repo-level tooling config for formatting/linting/type checks once the package metadata is settled.
- `.env` is ignored and no real committed API keys showed up; only dummy test keys were found: [.gitignore](/Users/kevin/github/problemform/.gitignore:40), [test_language_models.py](/Users/kevin/github/problemform/tests/test_language_models.py:15).

**Questions**
- Should `pip install problemform` be enough for the default OpenAI path, or should the README make extras mandatory?
- Should `agent` update `state.phase`, or is it intentionally a lower-level raw handler?
- Are saved/checkpointed `ProblemState` files considered sensitive user data?
- Which Anthropic model slug should be the direct API default? The current OpenAI default appears valid in current OpenAI model docs, while Anthropic examples commonly use dated direct-API slugs.

**Suggested Next 3 Commits**
1. Fix packaging contract: add dependency lower bounds, project metadata, install docs, and maybe `.env.example`.
2. Fix CLI correctness: validate `max_iterations`, make `agent` transition phases, and add friendly errors plus tests.
3. Harden provider/docs path: handle provider stop/refusal/truncation cases, tighten prompt/context separation, and clean up README/CLI docs.

External docs checked: OpenAI models docs and Anthropic stop-reason guidance.