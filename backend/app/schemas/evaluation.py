"""Pydantic schemas for Module D: Architecture Evaluation Engine.

Provides transparent, multi-criteria trade-off scoring across candidates with
explicit weightings and honest score-type distinctions.
"""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.common import ArchitectureArchetype


class CriterionEvaluation(BaseModel):
    """Detailed evaluation of an architecture candidate on a single specific criterion."""
    model_config = ConfigDict(extra="ignore")

    criterion_key: str = Field(
        ...,
        description="e.g. requirement_coverage, implementation_complexity, cost, latency, reliability, operational_risk, autonomy, human_oversight",
    )
    criterion_name: str = Field(..., description="Human-readable criterion title")
    raw_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Normalized score from 0.0 (poorest) to 10.0 (best performing for this criterion)",
    )
    weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weight allocated to this criterion (sum of all weights = 1.0)",
    )
    weighted_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="raw_score * weight",
    )
    score_type: Literal["heuristic", "estimated", "simulated", "measured"] = Field(
        default="heuristic",
        description="Transparent classification of the score basis. Never mislabel heuristics as measured.",
    )
    justification: str = Field(
        ...,
        description="Specific reasoning and assumptions underlying this score",
        min_length=10,
    )


class CandidateEvaluation(BaseModel):
    """Evaluation summary for one candidate across all criteria."""
    model_config = ConfigDict(extra="ignore")

    candidate_id: str = Field(...)
    candidate_name: str = Field(...)
    archetype: ArchitectureArchetype = Field(...)
    criteria_scores: list[CriterionEvaluation] = Field(..., min_length=1)
    total_weighted_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Sum of all weighted criterion scores",
    )
    key_strengths: list[str] = Field(..., min_length=1)
    primary_trade_offs: list[str] = Field(..., min_length=1)


class ArchitectureEvaluationResult(BaseModel):
    """Complete multi-criteria comparative evaluation report across candidates."""
    model_config = ConfigDict(extra="ignore")

    evaluations: list[CandidateEvaluation] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Evaluations for the 3 evaluated architecture candidates",
    )
    selected_candidate_id: str = Field(
        ...,
        description="ID of the candidate that scored highest under the selected criteria weights",
    )
    selection_rationale: str = Field(
        ...,
        description="Explanation of why this candidate is recommended among those evaluated, noting that it is not claimed to be universally optimal",
    )
    weights_applied: dict[str, float] = Field(
        ...,
        description="Criterion weights applied during this evaluation run",
    )
    methodology_notes: str = Field(
        ...,
        description="Explicit disclosure of estimation assumptions and heuristic nature of the evaluation",
    )
