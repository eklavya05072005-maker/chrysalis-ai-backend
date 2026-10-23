"""Pydantic schemas for Module A: Requirement Analyzer.

Extracts structured software specifications with strict evidence traceability.
"""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.common import EvidenceReference, Severity


class SoftwareModule(BaseModel):
    """A distinct functional module identified in the software specification."""
    model_config = ConfigDict(extra="ignore")

    module_id: str = Field(..., description="Unique module identifier (e.g. MOD-01)")
    name: str = Field(..., description="Human-readable module name")
    responsibilities: list[str] = Field(
        ...,
        description="Core operational responsibilities of this module",
        min_length=1,
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="IDs or names of other modules or external systems this module depends on",
    )


class WorkflowStep(BaseModel):
    """Single step within an end-to-end software workflow."""
    model_config = ConfigDict(extra="ignore")

    step_number: int = Field(..., ge=1)
    action: str = Field(..., description="Action performed in this step")
    actor: str = Field(..., description="System component or human actor performing the action")
    expected_outcome: str = Field(..., description="State change or output resulting from this step")


class Workflow(BaseModel):
    """End-to-end user or system journey."""
    model_config = ConfigDict(extra="ignore")

    workflow_id: str = Field(..., description="Unique workflow identifier (e.g. WF-01)")
    name: str = Field(..., description="Name of the workflow")
    trigger: str = Field(..., description="Event or user action that initiates the workflow")
    steps: list[WorkflowStep] = Field(..., min_length=1)


class BusinessRule(BaseModel):
    """Concrete business logic constraint or policy."""
    model_config = ConfigDict(extra="ignore")

    rule_id: str = Field(..., description="Unique rule identifier (e.g. BR-01)")
    description: str = Field(..., description="Clear statement of the rule constraint")
    enforcement: Literal["strict", "advisory", "overrideable"] = "strict"
    evidence: list[EvidenceReference] = Field(
        default_factory=list,
        description="Evidence references directly backing this business rule",
    )


class Requirement(BaseModel):
    """Individual functional or non-functional requirement with evidence."""
    model_config = ConfigDict(extra="ignore")

    req_id: str = Field(..., description="Unique requirement identifier (e.g. REQ-F-01, REQ-NF-01)")
    title: str = Field(..., description="Short title")
    description: str = Field(..., description="Detailed specification of the requirement")
    category: Literal["functional", "non_functional"] = "functional"
    priority: Literal["critical", "high", "medium", "low"] = "high"
    evidence: list[EvidenceReference] = Field(
        default_factory=list,
        description="Supporting evidence references from source text",
    )


# Type aliases for backwards compatibility
FunctionalRequirement = Requirement
NonFunctionalRequirement = Requirement



class RiskAmbiguity(BaseModel):
    """Identified uncertainty, open question, or technical risk."""
    model_config = ConfigDict(extra="ignore")

    item_id: str = Field(..., description="Unique risk/ambiguity identifier (e.g. RISK-01)")
    kind: Literal["risk", "ambiguity"] = "risk"
    description: str = Field(..., description="Explanation of the risk or ambiguity")
    severity: Severity = Severity.WARNING
    mitigation_suggestion: str | None = Field(
        default=None,
        description="Actionable suggestion to clarify ambiguity or mitigate risk",
    )


class RequirementAnalysisResult(BaseModel):
    """Structured output returned by the Requirement Analyzer."""
    model_config = ConfigDict(extra="ignore")

    project_name: str = Field(..., description="Inferred or supplied project title")
    executive_summary: str = Field(..., description="High-level synthesis of the system objectives")
    modules: list[SoftwareModule] = Field(default_factory=list)
    workflows: list[Workflow] = Field(default_factory=list)
    business_rules: list[BusinessRule] = Field(default_factory=list)
    functional_requirements: list[Requirement] = Field(default_factory=list)
    non_functional_requirements: list[Requirement] = Field(default_factory=list)
    risks_and_ambiguities: list[RiskAmbiguity] = Field(default_factory=list)
    evidence_references: list[EvidenceReference] = Field(
        default_factory=list,
        description="Master index of all citations extracted from source text",
    )


class AnalyzeRequest(BaseModel):
    """Input payload sent by Member 2 backend to the Requirement Analyzer."""
    model_config = ConfigDict(extra="ignore")

    spec_text: str = Field(..., min_length=10, description="Raw extracted specification text")
    source_pages: dict[str, str] | None = Field(
        default=None,
        description="Optional mapping from page number or label to page text content",
    )
    project_name: str | None = Field(
        default=None,
        description="Optional override project name",
    )
