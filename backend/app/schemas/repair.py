"""Canonical schemas for test-guided code repair.

Enforces bounded repair attempts, safe path containment, AST validation,
unified diff generation, and rigorous re-running of validation checks before
marking any repair as successful.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.sandbox import ExecutionStatus


class PatchStatus(str, Enum):
    """Lifecycle status of a proposed repair patch."""
    PROPOSED = "proposed"
    APPLIED = "applied"
    REJECTED = "rejected"
    VERIFIED = "verified"


class PatchSummary(BaseModel):
    """Representation of an individual file patch and its safety checks."""
    model_config = ConfigDict(from_attributes=True)

    file_path: str = Field(..., description="Relative path within the generated project")
    original_hash: str = Field(..., description="SHA-256 hash of original file content")
    patched_hash: str = Field(..., description="SHA-256 hash of proposed/applied content")
    unified_diff: str = Field(..., description="Standard unified diff of changes")
    patch_status: PatchStatus = Field(..., description="Current status of this patch")
    rejection_reason: Optional[str] = Field(default=None, description="Reason if patch was rejected")
    syntax_valid: bool = Field(default=True, description="Whether Python AST parsing succeeded")
    secrets_clean: bool = Field(default=True, description="Whether patch contains no hardcoded secrets")


class RepairRequest(BaseModel):
    """Request payload to initiate bounded code repair for a project."""
    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID = Field(..., description="Project identifier to repair")
    max_attempts: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Maximum repair iterations allowed (strictly bounded, default 1)",
    )
    include_static_checks: bool = Field(
        default=True,
        description="Whether to execute static validation checks (Module G)",
    )
    include_test_execution: bool = Field(
        default=True,
        description="Whether to execute tests in isolated sandbox",
    )


class RepairAttemptResult(BaseModel):
    """Result of a single bounded repair iteration."""
    model_config = ConfigDict(from_attributes=True)

    attempt_number: int = Field(..., ge=1, description="Iteration sequence number")
    initial_status: ExecutionStatus = Field(..., description="Status prior to this repair attempt")
    failure_diagnostics: List[str] = Field(
        default_factory=list,
        description="Collected error messages and failed assertions driving the repair",
    )
    patches: List[PatchSummary] = Field(
        default_factory=list,
        description="Patches proposed and processed in this iteration",
    )
    rerun_status: ExecutionStatus = Field(
        ...,
        description="Status measured after reapplying checks (never fabricated)",
    )
    checks_rerun: List[str] = Field(
        default_factory=list,
        description="Checks executed during verification",
    )
    success: bool = Field(..., description="Whether rerun checks passed cleanly")
    summary: str = Field(..., description="Explanation of changes and verification outcome")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RepairHistoryResponse(BaseModel):
    """Complete audit history of code repair attempts on a project."""
    project_id: uuid.UUID
    total_attempts: int
    final_status: ExecutionStatus
    total_patches_applied: int
    attempts: List[RepairAttemptResult]
