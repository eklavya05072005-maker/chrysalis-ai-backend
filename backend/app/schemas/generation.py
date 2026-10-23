import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class GeneratedFileBase(BaseModel):
    relative_path: str = Field(..., max_length=500)
    filename: str = Field(..., max_length=255)
    language: str = Field(..., max_length=50)
    file_size: int = Field(..., ge=0)
    validation_status: str = Field(default="pending", description="pending, passed, failed")


class GeneratedFileCreate(GeneratedFileBase):
    project_id: uuid.UUID


class GeneratedFileResponse(GeneratedFileBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime


class ValidationReport(BaseModel):
    project_id: uuid.UUID
    total_files: int
    passed_files: int
    failed_files: int
    validation_status: str  # passed, failed
    details: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GenerationSummaryResponse(BaseModel):
    project_id: uuid.UUID
    total_files: int
    status: str
    files: List[GeneratedFileResponse]
