"""Canonical schemas for the Chrysalis AI Connector subsystem.

Supports REST, MCP, Database, Custom SDK, and deterministic Mock connectors
with strict security validation, least privilege, parameterization, and
safe credential management (no raw secrets stored).
"""

from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConnectorType(str, Enum):
    """Supported connector categories."""
    REST = "rest"
    MCP = "mcp"
    DATABASE = "database"
    CUSTOM_SDK = "custom_sdk"
    MOCK = "mock"


class ConnectorVerificationState(str, Enum):
    """Lifecycle and verification state of a configured connector."""
    CONFIGURED = "configured"
    CONNECTED = "connected"
    VERIFIED = "verified"
    FAILED = "failed"
    BLOCKED = "blocked"


class ConnectorConfigCreate(BaseModel):
    """Request payload to register or configure an integration connector."""
    model_config = ConfigDict(extra="forbid")

    connector_type: ConnectorType = Field(..., description="Type of connector")
    name: str = Field(..., min_length=2, max_length=100, description="Unique name for the connector")
    is_mock: bool = Field(default=False, description="Whether this is a simulated mock connector")
    is_read_only: bool = Field(default=True, description="Strict read-only enforcement")
    requires_approval: bool = Field(default=False, description="Whether human approval is required for calls")
    allowed_endpoints: List[str] = Field(
        default_factory=list,
        description="Allowlist of approved URL prefixes or destinations for REST connectors",
    )
    allowed_methods: List[str] = Field(
        default=["GET"],
        description="Allowlist of permitted HTTP methods (e.g. GET, POST)",
    )
    allowed_tools: List[str] = Field(
        default_factory=list,
        description="Allowlist of approved MCP tool names",
    )
    timeout_seconds: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="Connection/query timeout in seconds",
    )
    rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        le=600,
        description="Rate limit quota per minute",
    )
    max_response_size_kb: int = Field(
        default=1024,
        ge=1,
        le=10240,
        description="Maximum permitted response payload size in KB",
    )
    config_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration parameters (secret references only, e.g. env var names, never raw keys)",
    )

    @field_validator("config_data")
    @classmethod
    def reject_raw_secrets(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure no raw API keys, passwords, or live credentials are submitted."""
        sensitive_keys = {"password", "secret", "api_key", "token", "private_key"}
        for key, val in v.items():
            k_lower = key.lower()
            if any(s in k_lower for s in sensitive_keys):
                str_val = str(val).strip()
                # Accept references like ${ENV_VAR} or ENV_VAR_NAME
                if not (str_val.startswith("${") or str_val.startswith("ENV_") or str_val == "" or "placeholder" in str_val.lower()):
                    if len(str_val) > 16:
                        raise ValueError(
                            f"Field '{key}' appears to contain a raw credential. "
                            "Store secrets in environment variables and provide variable names only."
                        )
        return v


class ConnectorConfigResponse(BaseModel):
    """Sanitized connector representation for API responses (all secrets masked)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    connector_type: ConnectorType
    name: str
    is_mock: bool
    is_read_only: bool
    requires_approval: bool
    is_approved: bool = Field(default=False, description="Whether human approval has been granted")
    allowed_endpoints: List[str]
    allowed_methods: List[str]
    allowed_tools: List[str]
    timeout_seconds: float
    rate_limit_per_minute: int
    max_response_size_kb: int
    state: ConnectorVerificationState
    config_data: Dict[str, Any] = Field(default_factory=dict, description="Sanitized configuration dictionary")
    created_at: datetime
    updated_at: datetime


class ConnectorTestRequest(BaseModel):
    """Payload to test or invoke a connector in a controlled sandbox manner."""
    model_config = ConfigDict(extra="forbid")

    endpoint_or_tool: str = Field(..., description="Target endpoint URL or MCP tool name")
    method: str = Field(default="GET", description="HTTP method for REST or 'EXEC' for MCP")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Input payload / parameters")


class ConnectorTestResponse(BaseModel):
    """Result of testing or invoking a connector."""
    connector_id: uuid.UUID
    connector_name: str
    connector_type: ConnectorType
    is_mock: bool
    success: bool
    status_code: Optional[int] = None
    output_data: Any = None
    execution_time_ms: float = 0.0
    audit_notes: str
    error: Optional[str] = None


class ConnectorListResponse(BaseModel):
    """List of connectors for a project."""
    project_id: uuid.UUID
    total: int
    items: List[ConnectorConfigResponse]
