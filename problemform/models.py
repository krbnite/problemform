# problemform.models
from typing import Literal

from pydantic import BaseModel, Field

Phase = Literal[
    "INITIAL_INPUT",
    "OBJECTIVE_ANALYSIS",
    "ASSUMPTION_ESCAVATION",
    "INFORMATION_GAP_DETECTION",
    "EXPERT_PERSPECTIVE_GENERATION",
    "ALTERNATIVE_FRAMING",
    "META_QUESTION_GENERATION",
    "PROMPT_REFINEMENT",
    "CONVERGENCE_EVALUATION",
]

class Assumption(BaseModel):
    assumption: str
    assumption_type: str
    importance: str
    impact_if_wrong: str
    rationale: str

AcquisitionMethod = Literal[
    "user_question",
    "external_research",
    "logical_inference",
    "multiple_methods",
]

Importance = Literal[
    "low",
    "medium",
    "high",
]

class InformationGap(BaseModel):
    gap: str
    importance: Importance
    impact_if_known: str
    acquisition_method: AcquisitionMethod
    rationale: str

class ExpertPerspective(BaseModel):
    perspective_type: str
    perspective_name: str
    rationale: str
    question: str

class AlternativeFraming(BaseModel):
    framing: str
    rationale: str
    difference_from_original: str
    potential_value: str

class MetaQuestion(BaseModel):
    question: str
    rationale: str
    potential_impact: str

class Revision(BaseModel):
    phase: Phase
    description: str
    rationale: str | None = None

class PromptVersion(BaseModel):
    version: int
    prompt: str
    revision: Revision | None = None

ConvergenceStatus = Literal[
    "NOT_CONVERGED",
    "NEAR_CONVERGENCE",
    "CONVERGED",
]

class ConvergenceAssessment(BaseModel):
    status: ConvergenceStatus
    rationale: str

class ProblemState(BaseModel):
    raw_input: str
    stated_objective: str | None = None
    inferred_objective: str | None = None
    assumptions: list[Assumption] = Field(default_factory=list)
    information_gaps: list[InformationGap] = Field(default_factory=list)
    expert_panel_perspectives: list[ExpertPerspective] = Field(default_factory=list)
    alternative_framings: list[AlternativeFraming] = Field(default_factory=list)
    meta_questions: list[MetaQuestion] = Field(default_factory=list)
    prompt_versions: list[PromptVersion] = Field(default_factory=list) 
    convergence_status: ConvergenceStatus = "NOT_CONVERGED"
    phase: Phase = "INITIAL_INPUT"
    final_prompt: str | None = None

    def add_prompt_version(self, 
        prompt: str, 
        revision: Revision | None = None,
    ) -> None:
        version = len(self.prompt_versions)
        self.prompt_versions.append(
            PromptVersion(
                version=version, 
                prompt=prompt, 
                revision=revision,
            )
        )
