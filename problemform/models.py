# problemform.models
from typing import Literal

from pydantic import BaseModel, Field

ConvergenceStatus = Literal[
    "NOT_CONVERGED",
    "NEAR_CONVERGENCE",
    "CONVERGED",
]

class ExpertPerspective(BaseModel):
    expert_type: str
    rationale: str
    question: str

class AlternativeFraming(BaseModel):
    framing: str
    rationale: str

class MetaQuestion(BaseModel):
    question: str
    rationale: str

class Revision(BaseModel):
    phase: str
    description: str
    rationale: str | None = None

class PromptVersion(BaseModel):
    version: int
    prompt: str
    revision: Revision | None = None


class ProblemState(BaseModel):
    raw_input: str
    stated_objective: str | None = None
    inferred_objective: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    information_gaps: list[str] = Field(default_factory=list)
    expert_panel_perspectives: list[ExpertPerspective] = Field(default_factory=list)
    alternative_framings: list[AlternativeFraming] = Field(default_factory=list)
    meta_questions: list[MetaQuestion] = Field(default_factory=list)
    prompt_versions: list[PromptVersion] = Field(default_factory=list) 
    convergence_status: ConvergenceStatus = "NOT_CONVERGED"
    final_prompt: str | None = None