"""Pydantic schemas for Module C: Architecture Search Engine.

Defines the three candidate architectures (Conservative, Hybrid Agentic, Automation-Heavy)
solving the identical requirements with distinct trade-offs.
"""

from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.common import ArchitectureArchetype


class ArchitectureComponent(BaseModel):
    """An identifiable architectural component or service."""
    model_config = ConfigDict(extra="ignore")

    component_id: str = Field(..., description="Unique component ID (e.g. COMP-01)")
    name: str = Field(..., description="Component name")
    type: str = Field(
        ...,
        description="Type (e.g. API Gateway, Deterministic Service, LLM Agent, Database, Message Queue)",
    )
    responsibilities: list[str] = Field(..., min_length=1)
    technology_stack: str = Field(..., description="Assumed language, framework, or runtime")


class ArchitectureConnection(BaseModel):
    """Directed connection or protocol between two components."""
    model_config = ConfigDict(extra="ignore")

    from_component_id: str = Field(...)
    to_component_id: str = Field(...)
    protocol: str = Field(..., description="e.g. HTTP/REST, gRPC, WebSocket, DB Query, Message Queue")
    description: str = Field(..., description="Nature of the interaction or payload exchanged")


class ArchitectureDataFlow(BaseModel):
    """Primary end-to-end data flow tracing a critical transaction through components."""
    model_config = ConfigDict(extra="ignore")

    flow_id: str = Field(..., description="Unique flow ID (e.g. FLOW-01)")
    name: str = Field(..., description="Name of the scenario or data pipeline")
    steps: list[str] = Field(..., description="Ordered list of steps tracing the data through components")


class ArchitectureCandidate(BaseModel):
    """Complete specification of a single architecture candidate."""
    model_config = ConfigDict(extra="ignore")

    candidate_id: str = Field(..., description="Unique candidate identifier (e.g. CAND-CONSERVATIVE)")
    archetype: ArchitectureArchetype = Field(
        ...,
        description="One of: conservative, hybrid_agentic, or automation_heavy",
    )
    name: str = Field(..., description="Architecture name")
    summary: str = Field(..., description="Concise architectural summary and philosophy")
    components: list[ArchitectureComponent] = Field(..., min_length=1)
    connections: list[ArchitectureConnection] = Field(..., min_length=1)
    data_flows: list[ArchitectureDataFlow] = Field(..., min_length=1)
    technology_assumptions: list[str] = Field(..., min_length=1)
    advantages: list[str] = Field(..., min_length=1)
    disadvantages: list[str] = Field(..., min_length=1)
    risks: list[str] = Field(..., min_length=1)
    human_approval_points: list[str] = Field(
        default_factory=list,
        description="Explicit intervention or sign-off points built into this architecture",
    )
    estimated_cost: str = Field(
        ...,
        description="Cost estimate accompanied by underlying usage and infrastructure assumptions",
    )
    estimated_latency: str = Field(
        ...,
        description="Latency estimate accompanied by network, model, and queue assumptions",
    )
    complexity_score: float = Field(
        ...,
        ge=1.0,
        le=10.0,
        description="Complexity score on a 1.0 (simplest) to 10.0 (most complex) scale",
    )
    complexity_definition: str = Field(
        ...,
        description="Clear explanation of how the complexity score was derived",
    )
    quality_assumptions: str | None = Field(
        default=None,
        description="Expected quality or accuracy estimates, provided only when assumptions are explicit",
    )


class ArchitectureCandidatesResult(BaseModel):
    """Container holding exactly the three distinct architecture candidates."""
    model_config = ConfigDict(extra="ignore")

    project_name: str = Field(...)
    candidates: list[ArchitectureCandidate] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Must contain exactly 3 candidates (Conservative, Hybrid Agentic, Automation-Heavy)",
    )
    comparison_summary: str = Field(
        ...,
        description="Overview of how each candidate tackles the same functional requirements",
    )


# API DTO schemas for Member 2 database & routes integration
import uuid
from datetime import datetime
from typing import Any, Dict, List


class ArchitectureOptionBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str
    components: List[Dict[str, Any]] = Field(default_factory=list)
    connections: List[Dict[str, Any]] = Field(default_factory=list)
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    estimated_cost: str = Field(..., max_length=100)
    estimated_latency: str = Field(..., max_length=100)
    complexity: str = Field(..., max_length=50)
    human_approval_required: bool = False
    is_selected: bool = False


class ArchitectureOptionCreate(ArchitectureOptionBase):
    project_id: uuid.UUID


class ArchitectureOptionResponse(ArchitectureOptionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime


class ArchitectureSelectRequest(BaseModel):
    architecture_id: uuid.UUID


class ArchitectureListResponse(BaseModel):
    project_id: uuid.UUID
    total: int
    items: List[ArchitectureOptionResponse]

