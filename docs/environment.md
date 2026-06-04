# Conda
If using conda, I recommend creating a new environment for ProblemForm to avoid dependency conflicts with other projects. You can do this with the following commands.

If you prefer named environments:
```
conda create -n problemform python=3.11
conda activate problemform
```

Or if you prefer path-based environments:
```
conda create -p ./.conda python=3.11
conda activate ./.conda
```

If using MiniConda, first install pip with `conda install pip` before installing the dependencies below.

# Installing ProblemForm

ProblemForm uses optional extras so users can install only the LLM provider SDKs they actually plan to use. From the repo root:

```
pip install -e .[dev]          # runtime deps + both LLM SDKs + pytest
# or pick one:
pip install -e .[all]          # runtime deps + both LLM SDKs (openai + anthropic)
pip install -e .[openai]       # runtime deps + just OpenAI
pip install -e .[anthropic]    # runtime deps + just Anthropic
```

The runtime deps (`pydantic`, `typer`, `rich`, `python-dotenv`) are always installed. The OpenAI and Anthropic SDKs are optional and imported lazily inside their providers, so installing only one provider's SDK does not break import of the other.

# Future milestone extras

Later milestones will introduce additional dependencies. They are not yet wired up; install ad hoc when their milestone work begins:

```
# Milestone 4 (LangGraph workflow)
pip install langgraph
# Milestone 5 (Streamlit UI)
pip install streamlit
# Milestone 6 (MCP server)
pip install mcp
# Milestone 8 (LangSmith observability, optional)
pip install langsmith
```
