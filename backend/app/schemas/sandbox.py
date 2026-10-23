"""Canonical schemas for sandbox execution and dynamic verification.

Provides data models for executing generated project code under strict isolation,
capturing stdout/stderr, execution timing, timeout status, resource bounds,
and honest verification status.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ExecutionStatus(str, Enum):
    """Honest verification states. Never claim a state without direct evidence."""
    GENERATED = "generated"
    STATIC_CHECKS_PASSED = "static_checks_passed"
    TESTS_PASSED = "tests_passed"
    DEMO_VERIFIED = "demo_verified"
    INTEGRATION_VERIFIED = "integration_verified"
    FAILED = "failed"
    BLOCKED = "blocked"
    NOT_RUN = "not_run"


class SandboxRuntimeType(str, Enum):
    """Runtime isolation provider."""
    DOCKER = "docker"
    FAIL_CLOSED = "fail_closed"
    MOCK = "mock"


class ExecutionRunRequest(BaseModel):
    """Request to initiate a sandboxed execution or test run."""
    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID = Field(..., description="Target project identifier")
    test_command: str = Field(
        default="pytest",
        description="Command to execute within the isolated container",
        max_length=200,
    )
    target_files: Optional[List[str]] = Field(
        default=None,
        description="Subset of generated relative file paths to execute (defaults to all)",
    )
    timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Maximum execution wall-clock time before aborting",
    )
    memory_limit_mb: int = Field(
        default=512,
        ge=64,
        le=2048,
        description="Maximum RAM allocation for the container in MB",
    )
    cpu_quota: float = Field(
        default=1.0,
        ge=0.1,
        le=4.0,
        description="CPU core quota allocated to container",
    )
    network_enabled: bool = Field(
        default=False,
        description="Whether outbound network is permitted (strictly False by default)",
    )
    runtime_override: Optional[SandboxRuntimeType] = Field(
        default=None,
        description="Optional forced runtime mode for testing (e.g. MOCK or FAIL_CLOSED)",
    )


class ExecutionRunResult(BaseModel):
    """Detailed result of an isolated execution run."""
    model_config = ConfigDict(from_attributes=True)

    run_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique run identifier")
    project_id: uuid.UUID = Field(..., description="Project identifier")
    status: ExecutionStatus = Field(..., description="Resulting verification status")
    runtime: str = Field(..., description="Actual isolation runtime used (docker, mock, fail_closed)")
    exit_code: Optional[int] = Field(default=None, description="Process exit code if completed")
    stdout: str = Field(default="", description="Captured standard output")
    stderr: str = Field(default="", description="Captured standard error")
    elapsed_time_seconds: float = Field(default=0.0, description="Elapsed execution duration")
    timed_out: bool = Field(default=False, description="Whether execution was terminated due to timeout")
    resource_limit_hit: bool = Field(default=False, description="Whether memory or CPU limits were exceeded")
    network_isolated: bool = Field(default=True, description="Whether outbound network was blocked")
    checks_performed: List[str] = Field(default_factory=list, description="List of checks actually performed")
    sandbox_cleaned_up: bool = Field(default=True, description="Whether workspace/container was cleanly purged")
    message: str = Field(..., description="Human-readable summary of outcome and security guarantees")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of execution run")


class ExecutionListResponse(BaseModel):
    """Paginated or listed execution runs for a project."""
    project_id: uuid.UUID
    total: int
    items: List[ExecutionRunResult]
