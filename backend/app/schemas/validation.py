"""Pydantic schemas for Module G: AI Output Validation.

Provides structured results for schema compliance, requirement traceability,
syntax checks, and file structure audits without fabricating results.
"""

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.common import CheckStatus, Severity


class TraceabilityLink(BaseModel):
    """Link tracing a specific requirement to components and business rules."""
    model_config = ConfigDict(extra="ignore")

    req_id: str = Field(...)
    req_title: str = Field(...)
    mapped_component_ids: list[str] = Field(default_factory=list)
    status: Literal["covered", "partially_covered", "uncovered"] = "covered"
    notes: str | None = None


class ValidationCheck(BaseModel):
    """Result of an individual deterministic validation or static analysis check."""
    model_config = ConfigDict(extra="ignore")

    check_id: str = Field(..., description="Unique check ID (e.g. CHK-JSON-01, CHK-SYNTAX-02)")
    name: str = Field(..., description="Short check name")
    category: Literal[
        "schema_validation",
        "field_completeness",
        "traceability",
        "file_structure",
        "syntax_check",
        "test_execution",
    ] = Field(...)
    status: CheckStatus = Field(
        ...,
        description="One of: passed, failed, blocked, not_run. Never fabricate passed results.",
    )
    severity_if_failed: Severity = Severity.HIGH
    message: str = Field(..., description="Detailed outcome message explaining pass/fail basis")
    details: dict[str, Any] | None = Field(default=None)


class ValidationReport(BaseModel):
    """Comprehensive validation report for an architecture candidate and its generated code."""
    model_config = ConfigDict(extra="ignore")

    project_name: str = Field(...)
    candidate_id: str = Field(...)
    overall_status: CheckStatus = Field(...)
    checks_total: int = Field(default=0)
    checks_passed: int = Field(default=0)
    checks_failed: int = Field(default=0)
    checks_blocked: int = Field(default=0)
    checks_not_run: int = Field(default=0)
    checks: list[ValidationCheck] = Field(default_factory=list)
    traceability_matrix: list[TraceabilityLink] = Field(default_factory=list)
    syntax_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
