# Planning Notes
This is the brainstorming document I first created to plan out the ProblemForm project. It is a scrambled collection of ideas, notes, and plans concerning the project's original intent and vision. Many of the other docs were distilled from these notes, and then updated as the project evolved. This document is not intended to be updated; it is a snapshot of the initial planning.

------------------------
------------------------


# ProblemForm: a Human-AI Collaborative Reasoning System

```
ProblemForm is not merely a prompt optimization tool, though it does optimize prompts.

ProblemForm is a human-AI collaborative problem formulation and reasoning system.

The objective is not to only improve wording, though wording will often be improved.

The objective is to improve the formulation of the underlying problem, objective, decision, request, inquiry, or question.
```

**ProblemForm helps humans and AI collaborate to formulate better questions before attempting to answer them.**

Most systems focus on generating better answers.

ProblemForm focuses on developing better questions.

By surfacing assumptions, identifying information gaps, exploring alternative framings, gathering relevant context, and incorporating expert perspectives, ProblemForm helps users converge on higher-quality formulations of the problems they are trying to solve.

----

# Details

* **Project Name**: ProblemForm
* **Core idea**: A web app/CLI/MCP tool that takes a rough user question and iteratively turns it into an optimized prompt/problem statement for another AI or human expert. Internally, the AI is doing problem formulation, assumption excavation, objective discovery, information gathering, expert perspectives, and convergence. Externally, the user is providing feedback and guidance to help the system understand their true intent and optimize the prompt accordingly. The final output is a much clearer, more specific, and better-formulated prompt that can be used to get better answers from an LLM or human expert. It even surfaces meta questions that nobody thought to ask but which could be crucial for solving the problem.
* **Backend/orchestration**: LangGraph
  - LangGraph models a stateful graph. It is designed for state, memory, durable execution, human-in-the-loop workflows, and agent orchestration. In this project, we have a clear multi-phase process that can be modeled as a graph:  
  `assessment → assumptions → gaps → expert perspectives → revision → convergence`.  
* **LLM providers**: start with OpenAI, design provider abstraction so Claude can be swapped in
* **UI**: Streamlit 
  - Streamlit is explicitly aimed at Python data scientists and AI/ML engineers building interactive apps quickly.  
* **MCP**: after the CLI works



## The Software Components

1. **Orchestrator Agent**: The main controller that manages the flow of the process, calling each component in sequence and handling the data passing between them. It will also handle user interactions and provide feedback on the progress.
  - Python 
  - OpenAI Agents SDK or LangGraph
  - Maintains iterative state
  - Supports handoffs/subagents
  - Produces structured JSON outputs for each phase
2. **MCP Server**: MCP is designed for exposing tools, resources, prompts, and workflows to AI applications through a standard interface.  The MCP server will expose tools like 
  - `assess_question_quality`
  - `extract_objective`
  - `identify_assumptions`
  - `generate_expert_questions`
  - `synthesize_prompt`
  - `evaluate_convergence`
  - `export_prompt`
3. **Subagents**: Specialized agents that can be called by the orchestrator to perform specific tasks. For example, the Assumption Excavator Subagent will focus on identifying and challenging assumptions in the user's question.
  - **Objective Analyst**: Focuses on extracting and clarifying the core objective of the user's question.
  - **Assumption Excavator**: Identifies and challenges underlying assumptions in the user's question.
  - **Research Scout**: Gathers relevant information and context to enrich the problem statement.
  - **Expert Panel Generator**: Creates a simulated panel of experts to provide diverse perspectives on the problem.
  - **Prompt Synthesizer**: Combines insights from previous phases to create an optimized prompt.
  - **Convergence Judge**: Evaluates the convergence of the iterative process and determines when the prompt is sufficiently optimized.
4. **User Interface**: CLI + Streamlit web app for user interaction. The UI will allow users to input their initial question, view the iterative process, and receive the final optimized prompt.
  - CLI: For quick interactions and integration into workflows.
  - Streamlit Web App: For a more interactive and visual experience, showing the iterative process and allowing users to provide feedback at each stage.

### Convergence Judge
Convergence States:
- Not Yet Converged
- Near Convergence
- Converged

The system should explicitly assess convergence after each iteration.

Convergence occurs when:
- objectives are clear
- assumptions have been surfaced
- major information gaps have been addressed
- alternative framings have been explored
- further refinement is likely to produce only marginal gains

### Problem State / LangGraph 
The `ProblemState` is the thing LangGraph will actually pass around. 

- raw_input
- inferred_objective
- stated_objective
- assumptions
- ambiguities
- information_gaps
- expert_perspectives
- revisions
- prompt_versions
- convergence_status
- refinement_history
- final_prompt


### Meta Questions Worth Asking
Before concluding an iteration, the system identifies 1-5 questions that nobody has asked yet but which could significantly alter the understanding of the problem.

Because often the breakthrough isn't a better answer, but a better question. And sometimes the best question is one that nobody has thought to ask yet. By surfacing these meta questions, the system can push the user to consider angles they hadn't before, leading to deeper insights and a more optimized prompt.


## Prompt Development Trace
It should be possible to trace the development of the prompt through each phase, showing how the original question evolved into the final optimized prompt. This will help users understand the value of each phase and how their input was transformed.

```
v0: User's raw question
v1: Objective clarified
v2: Assumptions surfaced
v3: Missing context added
v4: Expert perspectives included
v5: Converged final prompt
```

Each version should record:
- what changed
- why it changed
- which agent suggested it
- expected improvement


## Project Merits
This project is a comprehensive demonstration of building a complex, multi-agent system with iterative reasoning and human-in-the-loop workflows. It touches on all the key concepts that employers care about when it comes to agentic systems:
* agents/subagents
* tool calling
* structured outputs
* stateful management/workflows
* human-in-the-loop iteration
* MCP server design
* prompt resources
* convergence/evaluation logic
* exportable artifacts
* safety/security awareness


## Security and Safety Considerations
MCP security matters. Recent reporting has highlighted vulnerabilities around MCP server execution and tool exposure, so your README should explicitly mention sandboxing, tool allowlists, no shell execution by default, and least-privilege design. 

Security principles:
- No shell execution by default.
- Tool allowlist only.
- No arbitrary file access by default.
- Least-privilege API keys.
- Explicit user confirmation before external tool use.
- Sandboxed execution for experimental tools.
- No secrets stored in logs or traces.


-----------------


## Where to Start (?)
Build in this order:

```
1. Pure Python core
2. Provider abstraction (OpenAI, Claude, etc.)
3. CLI
4. LangGraph
5. Streamlit
6. MCP
7. Polish: README/security/demo
8. Bonus: LangSmith
```

Build ProblemForm python package with core logic and provider abstraction first. Get the core iterative process working in a simple Python script.

Then build a CLI around that core logic to allow users to interact with it from the command line. 

Then add LangGraph to manage the orchestration and state of the iterative process, allowing for more complex workflows and agent interactions.

Then add Streamlit for a more interactive web interface that can visualize the iterative process and allow users to provide feedback at each stage.

Then add MCP to expose the tools and workflows to other AI applications and enable integration with external systems.

Finally, add LangSmith for observability and debugging, and polish the overall user experience, documentation, and security features.

Not everything has to be perfect or done at once. The key is to get a working CLI that demonstrates the core iterative process, then build out from there.


## The First Milestone: Core Data Model and CLI
The first milestone does not involve agents yet. It's to make the core data model.

Create:

```bash
problemform/
  __init__.py
  models.py
  prompts.py
  providers/
    base.py
    openai_provider.py
  core/
    assess.py
    refine.py
    converge.py
  cli.py
  examples/
  tests/
README.md
pyproject.toml
```

The first working CLI command should be something like:

```bash
problemform assess "Should I learn the Claude API?"
```

It should output structured sections:
```
Objective
Quality Rating
Ambiguities
Assumptions
Information Gaps
Suggested Revision
Follow-up Questions
Convergence Status
```

The `problemform assess` command will run the question through the assessment phase and produce a structured output of the assessment, assumptions, gaps, and expert perspectives. 

After the assessment, we can iterate on that output with refinement commands:

```bash
problemform refine --assessment-file assessment_output.json
```


## Future Evaluation Metrics
These can be built out later, but some potential metrics for evaluating the effectiveness of the system could include:
- Reduction in ambiguity
- Number of surfaced assumptions
- Number of information gaps identified
- Objective clarity score
- Expert perspective coverage
- Convergence confidence

## Future Observability
To understand how users are interacting with the system and where they might be getting stuck, we can build out observability features such as:
- LangSmith traces
- Agent execution visualization
- Prompt version history
- Token usage
- Cost tracking
- Iteration analytics


-------------

## Quick Recap of Roles and Why they are Distinct
Objective Analyst (The Detective)
    What is the user trying to accomplish?

Assumption Excavator (The Archaeologist)
    What is being treated as true?

Information-Gap Detector (The Researcher)
    What information is missing?

Expert Panel Generator (The Consultant Group)
    What would different experts want to know?
    What would different perspectives want to know?

Alternative-Framing Generator (The Lensmaker)
    What if this isn't the right problem?

Meta Question Generator (The Philosopher)
    What important question are we not asking about the inquiry itself?
    What important question are we not asking about the formulation process?