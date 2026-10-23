import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.document import DocumentResponse
from backend.app.schemas.requirement import RequirementResponse
from backend.app.schemas.architecture import ArchitectureOptionResponse
from backend.app.schemas.simulation import SimulationResultResponse
from backend.app.schemas.generation import GeneratedFileResponse


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(ProjectResponse):
    documents: List[DocumentResponse] = Field(default_factory=list)
    requirements: List[RequirementResponse] = Field(default_factory=list)
    architecture_options: List[ArchitectureOptionResponse] = Field(default_factory=list)
    simulation_results: List[SimulationResultResponse] = Field(default_factory=list)
    generated_files: List[GeneratedFileResponse] = Field(default_factory=list)


class ProjectListResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
    page: int
    size: int
    pages: int
