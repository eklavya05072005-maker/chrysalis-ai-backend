"""Pydantic schemas for Module H: Explainable System Verdict Engine.

Represents the overall system implementation verdict (non-agentic, agentic, or hybrid).
Explicitly distinct from the 3 concrete architecture proposals (Conservative, Hybrid Agentic, Automation-Heavy).
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.schemas.common import EvidenceReference


class SystemVerdictType(str, Enum):
    """Overall system recommendation enum."""
    NON_AGENTIC = "non-agentic"
    AGENTIC = "agentic"
    HYBRID = "hybrid"


class SystemVerdictResult(BaseModel):
    """Holistic, explainable verdict determining whether the problem requires agentic AI.
    
    Combines rule-based heuristics, task classification breakdown, and LLM assessment.
    Never relies solely on a numerical threshold.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    project_name: str = Field(..., description="Target project name")
    verdict: SystemVerdictType = Field(
        default=SystemVerdictType.HYBRID,
        description="Overall architectural recommendation: 'non-agentic', 'agentic', or 'hybrid'",
    )
    overall_verdict: Optional[SystemVerdictType] = Field(default=None, description="verdict alias")
    headline: str = Field(
        default="",
        description="One-sentence executive verdict summary",
    )
    confidence_score: float = Field(
        default=0.90,
        ge=0.0,
        le=1.0,
        description="Confidence score for the recommendation based on requirement clarity",
    )
    reasoning: str = Field(
        default="",
        description="Detailed, transparent rationale explaining why this verdict was reached",
    )
    autonomy_boundary: str = Field(
        default="",
        description="Upper boundary of autonomous execution permitted",
    )
    key_risks: list[str] = Field(
        default_factory=list,
        description="Key risks identified",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Operational and design limitations",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions made regarding environment or inputs",
    )
    supporting_evidence: list[EvidenceReference] = Field(
        default_factory=list,
        description="Verbatim evidence citations from specification supporting the verdict",
    )
    deterministic_task_ratio: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Proportion of candidate tasks that are strictly deterministic",
    )
    agentic_task_ratio: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Proportion of candidate tasks that require autonomous reasoning or tool loops",
    )
    deterministic_task_count: int = Field(default=0, description="Count of deterministic tasks")
    ai_assisted_task_count: int = Field(default=0, description="Count of AI assisted tasks")
    agentic_task_count: int = Field(default=0, description="Count of agentic tasks")
    risks_and_limitations: list[str] = Field(
        default_factory=list,
        description="Potential failure modes, latency concerns, cost implications, or drift risks",
    )
    human_approval_required: bool = Field(
        default=False,
        description="Whether high-stakes actions require human-in-the-loop checkpoints",
    )
    recommended_next_step: str = Field(
        default="Proceed to architecture candidate exploration.",
        description="Actionable next step for engineering implementation",
    )

    @model_validator(mode="after")
    def sync_aliases(self) -> "SystemVerdictResult":
        if self.overall_verdict is None:
            self.overall_verdict = self.verdict
        elif self.verdict is None:
            self.verdict = self.overall_verdict
        if not self.headline:
            val = self.overall_verdict.value if isinstance(self.overall_verdict, Enum) else str(self.overall_verdict)
            self.headline = f"System verdict: {val}"
        if not self.key_risks and self.risks_and_limitations:
            self.key_risks = list(self.risks_and_limitations)
        elif not self.risks_and_limitations and self.key_risks:
            self.risks_and_limitations = list(self.key_risks)
        if not self.limitations:
            self.limitations = ["Requires valid external connector credentials and standard network availability."]
        if not self.autonomy_boundary:
            self.autonomy_boundary = (
                "Human approval strictly required for sensitive or high-value actions."
                if self.human_approval_required
                else "Autonomous actions permitted within verified security guardrails."
            )
        return self
