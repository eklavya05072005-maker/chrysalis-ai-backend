import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class RequirementBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    requirement_type: str = Field(..., description="e.g. functional, non-functional, agentic, integration, deterministic, ai_assisted")
    priority: str = Field(..., description="e.g. high, medium, low")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    source_page: Optional[int] = None
    evidence_text: Optional[str] = None


class RequirementCreate(RequirementBase):
    project_id: uuid.UUID


class RequirementResponse(RequirementBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime


class RequirementListResponse(BaseModel):
    project_id: uuid.UUID
    total: int
    items: List[RequirementResponse]
