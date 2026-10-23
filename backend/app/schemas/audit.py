"""Canonical schemas for system audit trail and verification state accounting.

Provides tamper-evident event logging, approval tracking, and honest status
reporting ensuring secrets are never persisted in logs or audit outputs.
"""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.sandbox import ExecutionStatus


class AuditEventCreate(BaseModel):
    """Schema for registering a system audit event."""
    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID = Field(..., description="Associated project identifier")
    event_type: str = Field(..., max_length=100, description="Category of event (e.g. EXECUTION, APPROVAL, REPAIR)")
    actor: str = Field(default="system", max_length=100, description="Originating actor or component")
    details: Dict[str, Any] = Field(default_factory=dict, description="Sanitized metadata and parameters")


class AuditEventResponse(BaseModel):
    """Sanitized audit event representation."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    event_type: str
    actor: str
    details: Dict[str, Any]
    created_at: datetime


class ProjectVerificationSummary(BaseModel):
    """Comprehensive summary of project verification standing across all checks."""
    project_id: uuid.UUID
    verification_status: ExecutionStatus
    static_checks_passed: bool
    dynamic_tests_passed: bool
    demo_verified: bool
    integration_verified: bool
    active_limitations: List[str]
    recent_audit_events: List[AuditEventResponse]
