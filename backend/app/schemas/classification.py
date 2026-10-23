"""Pydantic schemas for Module B: Task Classification Engine.

Classifies software tasks into deterministic, AI-assisted, or agentic workflows
with rigorous rationale and safety guardrails.
"""

from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.common import EvidenceReference, TaskCategory


class TaskItem(BaseModel):
    """An identifiable task extracted from requirements or workflows for classification."""
    model_config = ConfigDict(extra="ignore")

    task_id: str = Field(..., description="Unique task identifier (e.g. TASK-01)")
    name: str = Field(..., description="Short name of the task")
    description: str = Field(..., description="Description of the operation or capability")
    module_id: str | None = Field(default=None, description="Associated module ID if applicable")


class TaskClassification(BaseModel):
    """Detailed classification for an individual software task."""
    model_config = ConfigDict(extra="ignore")

    task_id: str = Field(..., description="Task ID being classified")
    task_name: str = Field(..., description="Task name")
    category: TaskCategory = Field(
        ...,
        description="Recommended paradigm: deterministic, ai_assisted, or agentic",
    )
    reasoning: str = Field(
        ...,
        description="Explicit justification for why this approach was chosen over the others",
        min_length=10,
    )
    supporting_evidence: list[EvidenceReference] = Field(
        default_factory=list,
        description="Citations from specification supporting this decision",
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Model confidence score between 0.0 and 1.0, when available",
    )
    risks: list[str] = Field(
        default_factory=list,
        description="Failure modes, drift risks, or latency concerns for this classification",
    )
    human_approval_required: bool = Field(
        default=False,
        description="Whether this task executes high-stakes operations requiring explicit human approval",
    )


class TaskClassificationResult(BaseModel):
    """Aggregate output from the Task Classification Engine."""
    model_config = ConfigDict(extra="ignore")

    classifications: list[TaskClassification] = Field(default_factory=list)
    summary_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Count of tasks classified under deterministic, ai_assisted, and agentic",
    )
    classification_notes: str | None = Field(
        default=None,
        description="General observations on the distribution of deterministic vs AI tasks",
    )
