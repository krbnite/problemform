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

# AI Dependencies

## OpenAI SDK

### Purpose
Provides access to OpenAI language models.

### Why We Use It
The MVP uses a single language model operating under the ProblemForm Constitution.

### Common Usage

```python
from openai import OpenAI
```

### Important Features

- model invocation
- structured outputs
- tool calling

### Documentation

https://platform.openai.com/docs

---

# Workflow Dependencies

## LangGraph

### Purpose
Graph-based orchestration framework for AI workflows.

### Why We Use It
MVP++ implements the ProblemForm architecture as a graph of specialized workflow nodes operating on a shared ProblemState.

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

# User Interface Dependencies

## Streamlit

### Purpose
Rapid development framework for interactive web applications.

### Why We Use It
Provides a lightweight user interface for exploring ProblemForm workflows.

### Important Features

- interactive widgets
- session state
- rapid prototyping

### Documentation

https://docs.streamlit.io/

---

# Integration Dependencies

## MCP (Model Context Protocol)

### Purpose
Standardized protocol for connecting AI systems to tools, services, and external resources.

### Why We Use It
Allows ProblemForm to be exposed as a reusable capability within broader agent ecosystems.

### Documentation

https://modelcontextprotocol.io/

---

# Observability Dependencies

## LangSmith

### Purpose
Tracing, evaluation, debugging, and observability platform for LLM applications.

### Why We Use It
Provides visibility into workflow execution and supports evaluation of ProblemForm behavior.

### Important Features

- traces
- evaluations
- debugging
- analytics

### Documentation

https://docs.smith.langchain.com/