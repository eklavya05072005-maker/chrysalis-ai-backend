"""Pydantic schemas for Module E: Scenario Design.

Standard benchmark scenarios for comparing resilience and behavior across architectures.
"""

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class ScenarioCase(BaseModel):
    """An individual test or benchmark scenario applied across all architectures."""
    model_config = ConfigDict(extra="ignore")

    scenario_id: str = Field(..., description="Unique scenario identifier (e.g. SCEN-01)")
    case_type: Literal[
        "normal_workflow",
        "invalid_input",
        "missing_information",
        "external_tool_failure",
        "low_confidence_ai",
        "sensitive_human_approval",
    ] = Field(..., description="Canonical category of the scenario")
    title: str = Field(..., description="Descriptive scenario title")
    description: str = Field(..., description="Operational narrative of the scenario")
    sample_input: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured input payload fed into the architecture during simulation",
    )
    expected_behavior: str = Field(
        ...,
        description="Detailed description of what an acceptable architecture response must be",
    )
    evaluation_criteria: list[str] = Field(
        ...,
        min_length=1,
        description="Checkpoints determining whether a candidate successfully handles the scenario",
    )
    failure_conditions: list[str] = Field(
        ...,
        min_length=1,
        description="Explicit observable conditions that mark a candidate run as failed",
    )


class ScenarioDesignResult(BaseModel):
    """Collection of standardized benchmark scenarios tailored to the specification."""
    model_config = ConfigDict(extra="ignore")

    project_name: str = Field(...)
    scenarios: list[ScenarioCase] = Field(
        ...,
        min_length=6,
        description="Standard suite covering all 6 essential reliability and edge cases",
    )
    benchmarking_guide: str = Field(
        ...,
        description="Instructions for Member 2 to execute scenarios against candidates",
    )
