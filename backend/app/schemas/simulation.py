import uuid
from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class SimulationResultBase(BaseModel):
    architecture_id: uuid.UUID
    scenario_name: str = Field(..., max_length=255)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    expected_outcome: str
    simulated_outcome: str
    result_status: str = Field(..., description="pass, fail, warning")
    metrics: Dict[str, Any] = Field(default_factory=dict)


class SimulationResultCreate(SimulationResultBase):
    project_id: uuid.UUID


class SimulationResultResponse(SimulationResultBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime


class SimulationListResponse(BaseModel):
    project_id: uuid.UUID
    total: int
    items: List[SimulationResultResponse]
