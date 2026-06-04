# Conda
If using conda, I recommend creating a new environment for ProblemForm to avoid dependency conflicts with other projects. You can do this with the following commands...

If you prefer named environments:
```
conda create -n problemform python=3.11 # conda create -p ./env python=3.11
conda activate problemform
```

Or if you prefer path-based environments: 
```
conda create -p ./.conda python=3.11
conda activate ./.conda
```

Then, install the required dependencies for each milestone as needed.
_
If using MiniConda, first install pip with `conda install pip` before installing the dependencies below.

```
# Milestones 1-2
pip install pydantic typer rich pytest openai python-dotenv
# Milestone 3
pip install langgraph
# Milestone 4
pip install streamlit
# Milestone 5
pip install mcp
# Milestone 7
pip install langsmith
```