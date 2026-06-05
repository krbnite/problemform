# Dependencies

This document describes the major third-party dependencies used by ProblemForm, their purpose, and how they fit into the overall architecture.

---

# Core Dependencies

## Pydantic

### Purpose
Provides structured data models, validation, serialization, and type safety.

### Why We Use It
ProblemForm relies heavily on structured state (ProblemState) that evolves throughout the workflow. Pydantic provides a reliable way to define, validate, serialize, and persist this state.

### Common Usage

```python
from pydantic import BaseModel, Field

class ProblemState(BaseModel):
    raw_input: str
    assumptions: list[str] = Field(default_factory=list)
```

### Important Features

- BaseModel
- Field
- model_dump()
- model_validate()
- model_copy()

### Documentation

https://docs.pydantic.dev/

---

## Typer

### Purpose
Provides a modern framework for building command-line interfaces.

### Why We Use It
The MVP exposes ProblemForm functionality through a CLI.

### Common Usage

```python
import typer

app = typer.Typer()

@app.command()
def analyze(prompt: str):
    ...
```

### Important Features

- Typer()
- @app.command
- automatic help generation
- argument parsing

### Documentation

https://typer.tiangolo.com/

---

## Rich

### Purpose
Provides beautiful terminal output.

### Why We Use It
ProblemForm generates structured analysis that benefits from improved readability in the terminal.

### Common Usage

```python
from rich.console import Console

console = Console()
console.print(...)
```

### Important Features

- Console
- Panel
- Table
- Markdown

### Documentation

https://rich.readthedocs.io/

---

## python-dotenv

### Purpose
Loads environment variables from a `.env` file into the process environment.

### Why We Use It
API keys for the OpenAI and Anthropic providers are kept out of source by being loaded from a `.env` file at the repo root. `python-dotenv` performs that load at import time via `problemform/config.py`, so any module that imports the CLI or the providers sees `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` automatically.

### Common Usage

```python
from dotenv import load_dotenv

load_dotenv()
```

### Important Features

- .env file loading
- non-destructive: existing environment variables are not overwritten

### Documentation

https://saurabh-kumar.com/python-dotenv/

---

## PyYAML

### Purpose
Parses YAML documents into Python objects.

### Why We Use It
The Phase A evaluation framework loads benchmark test cases from YAML files under `benchmarks/<suite>/<category>/`. PyYAML's `safe_load` powers `problemform/eval/corpus.py:load_test_cases`, which walks a suite directory recursively and validates each file against the `TestCase` Pydantic model.

### Common Usage

```python
import yaml

data = yaml.safe_load(path.read_text())
```

### Important Features

- safe_load (no arbitrary-Python object construction)
- mapping/sequence/scalar coverage
- streaming and multi-document parsing

### Documentation

https://pyyaml.org/wiki/PyYAMLDocumentation

---

# Development Dependencies

## Pytest

### Purpose
Testing framework.

### Why We Use It
Ensures ProblemForm behavior remains stable as the system evolves.

### Common Usage

```python
def test_problem_state():
    ...
```

### Important Features

- test discovery
- fixtures
- assertions

### Documentation

https://docs.pytest.org/

---

# LLM Provider Dependencies

The OpenAI and Anthropic SDKs are **optional extras**. The provider layer (`problemform/core/language_models.py`) imports each SDK lazily inside the corresponding provider's `__init__`, so installing only one provider's SDK does not break import of the module or of the other provider.

## OpenAI SDK

### Purpose
Provides access to OpenAI language models.

### Why We Use It
ProblemForm exposes a provider-neutral `LLMProvider` Protocol; the OpenAI SDK powers `OpenAIProvider`, which uses the structured-output `responses.parse` API to validate Pydantic-typed phase results and the `responses.create` API for free-text generation in the evaluation framework.

### Installation
Optional extra: `pip install -e .[openai]` (or `.[all]` / `.[dev]`).

### Common Usage

```python
from openai import OpenAI

client = OpenAI()
response = client.responses.parse(
    model=model,
    input=[...],
    text_format=PydanticModel,
)
```

### Important Features

- structured-output parsing (`responses.parse`)
- refusal and content-filter signaling on the response object
- lazy import inside `OpenAIProvider.__init__`

### Documentation

https://platform.openai.com/docs

---

## Anthropic SDK

### Purpose
Provides access to Anthropic's Claude models.

### Why We Use It
The Anthropic SDK powers `AnthropicProvider`, the second concrete implementation of the `LLMProvider` Protocol. Structured output is obtained via JSON-via-text on the Messages API plus Pydantic validation; free-text generation is used by the evaluation framework's Answer and Judge roles.

### Installation
Optional extra: `pip install -e .[anthropic]` (or `.[all]` / `.[dev]`).

### Common Usage

```python
from anthropic import Anthropic

client = Anthropic()
message = client.messages.create(
    model=model,
    max_tokens=8000,
    messages=[{"role": "user", "content": prompt}],
)
```

### Important Features

- `stop_reason` inspection for truncation and refusal handling
- text-block extraction from multi-block `content`
- lazy import inside `AnthropicProvider.__init__`

### Documentation

https://docs.anthropic.com/

---

# Planned (Future Milestones)

These packages are tracked here for forward visibility. None of them are installed by any extra in `pyproject.toml`, and none are imported anywhere in the current codebase. They will be added to the dependency set when their respective milestones begin. See `docs/roadmap.md` for milestone scope and ordering.

## LangGraph

### Purpose
Graph-based orchestration framework for AI workflows.

### Why We Will Use It
Milestone 4 reimplements the ProblemForm pipeline as an orchestrated graph of phase nodes operating on a shared `ProblemState`, replacing the current procedural `run_pipeline` runner with explicit edges and conditional routing.

### Common Usage

```python
StateGraph(...)
```

### Important Features

- graph nodes
- graph edges
- shared state
- conditional routing
- workflow loops

### Documentation

https://langchain-ai.github.io/langgraph/

---

## Streamlit

### Purpose
Rapid development framework for interactive web applications.

### Why We Will Use It
Milestone 5 provides a lightweight, browser-based interface for exploring ProblemForm workflows without the CLI — primarily targeted at non-technical users.

### Important Features

- interactive widgets
- session state
- rapid prototyping

### Documentation

https://docs.streamlit.io/

---

## MCP (Model Context Protocol)

### Purpose
Standardized protocol for connecting AI systems to tools, services, and external resources.

### Why We Will Use It
Milestone 6 exposes ProblemForm as an MCP-compatible service so it can be invoked as a reusable capability inside broader agent ecosystems.

### Documentation

https://modelcontextprotocol.io/

---

## LangSmith

### Purpose
Tracing, evaluation, debugging, and observability platform for LLM applications.

### Why We Will Use It
Milestone 8 (optional) adds tracing, run analytics, and evaluation tooling to make workflow execution and provider behavior easier to inspect and improve.

### Important Features

- traces
- evaluations
- debugging
- analytics

### Documentation

https://docs.smith.langchain.com/