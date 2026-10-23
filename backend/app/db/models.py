import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict
from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    func,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from backend.app.db.base import Base

# Universal JSON type that automatically uses PostgreSQL native JSONB in production
# and generic JSON in testing/other environments.
CompatibleJSON = JSON().with_variant(JSONB(), "postgresql")


class Project(Base):
    """
    Project model representing an end-to-end Chrysalis AI workflow lifecycle:
    uploaded -> analyzing -> analyzed -> architectures_ready -> simulated ->
    architecture_selected -> generating -> generated -> validating -> validated.
    """
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="uploaded",
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships with cascading deletes
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Document.created_at.desc()",
    )
    requirements: Mapped[List["Requirement"]] = relationship(
        "Requirement",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Requirement.created_at.asc()",
    )
    architecture_options: Mapped[List["ArchitectureOption"]] = relationship(
        "ArchitectureOption",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ArchitectureOption.created_at.asc()",
    )
    simulation_results: Mapped[List["SimulationResult"]] = relationship(
        "SimulationResult",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="SimulationResult.created_at.asc()",
    )
    generated_files: Mapped[List["GeneratedFile"]] = relationship(
        "GeneratedFile",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="GeneratedFile.relative_path.asc()",
    )
    execution_runs: Mapped[List["ExecutionRun"]] = relationship(
        "ExecutionRun",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ExecutionRun.created_at.desc()",
    )
    connectors: Mapped[List["ConnectorModel"]] = relationship(
        "ConnectorModel",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ConnectorModel.created_at.asc()",
    )
    repair_logs: Mapped[List["RepairLog"]] = relationship(
        "RepairLog",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="RepairLog.created_at.desc()",
    )
    audit_events: Mapped[List["AuditEventModel"]] = relationship(
        "AuditEventModel",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="AuditEventModel.created_at.desc()",
    )



class Document(Base):
    """Uploaded PDF document metadata and extracted text reference."""
    __tablename__ = "uploaded_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    upload_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="success",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="documents")


class Requirement(Base):
    """Analyzed software requirement extracted from document."""
    __tablename__ = "requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirement_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # e.g., 'deterministic', 'ai_assisted', 'agentic'
    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # e.g., 'high', 'medium', 'low'
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    evidence_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="requirements")


class ArchitectureOption(Base):
    """Generated software architecture option incorporating Agentic AI workflows."""
    __tablename__ = "architecture_options"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    components: Mapped[List[Dict[str, Any]]] = mapped_column(
        CompatibleJSON,
        nullable=False,
        default=list,
    )
    connections: Mapped[List[Dict[str, Any]]] = mapped_column(
        CompatibleJSON,
        nullable=False,
        default=list,
    )
    pros: Mapped[List[str]] = mapped_column(
        CompatibleJSON,
        nullable=False,
        default=list,
    )
    cons: Mapped[List[str]] = mapped_column(
        CompatibleJSON,
        nullable=False,
        default=list,
    )
    risks: Mapped[List[str]] = mapped_column(
        CompatibleJSON,
        nullable=False,
        default=list,
    )
    estimated_cost: Mapped[str] = mapped_column(String(100), nullable=False)
    estimated_latency: Mapped[str] = mapped_column(String(100), nullable=False)
    complexity: Mapped[str] = mapped_column(String(50), nullable=False)
    human_approval_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_selected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="architecture_options")
    simulations: Mapped[List["SimulationResult"]] = relationship(
        "SimulationResult",
        back_populates="architecture",
        cascade="all, delete-orphan",
    )


class SimulationResult(Base):
    """Simulation run testing architecture resilience and performance under scenario."""
    __tablename__ = "simulation_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    architecture_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("architecture_options.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scenario_name: Mapped[str] = mapped_column(String(255), nullable=False)
    input_data: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON,
        nullable=False,
        default=dict,
    )
    expected_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    simulated_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    result_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # e.g., 'pass', 'fail', 'warning'
    metrics: Mapped[Dict[str, Any]] = mapped_column(
        CompatibleJSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="simulation_results")
    architecture: Mapped["ArchitectureOption"] = relationship("ArchitectureOption", back_populates="simulations")


class GeneratedFile(Base):
    """Metadata of generated source code file for the selected architecture."""
    __tablename__ = "generated_files"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relative_path: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    validation_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="generated_files")

    __table_args__ = (
        Index("idx_project_relative_path", "project_id", "relative_path", unique=True),
    )


class ExecutionRun(Base):
    """Isolated execution run record for generated code verification."""
    __tablename__ = "execution_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    runtime: Mapped[str] = mapped_column(String(50), nullable=False)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    elapsed_time_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    timed_out: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resource_limit_hit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    network_isolated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    checks_performed: Mapped[List[str]] = mapped_column(CompatibleJSON, nullable=False, default=list)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="execution_runs")


class ConnectorModel(Base):
    """Configured integration connector (REST, MCP, DB, Custom, Mock)."""
    __tablename__ = "connectors"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connector_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_read_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allowed_endpoints: Mapped[List[str]] = mapped_column(CompatibleJSON, nullable=False, default=list)
    allowed_methods: Mapped[List[str]] = mapped_column(CompatibleJSON, nullable=False, default=list)
    allowed_tools: Mapped[List[str]] = mapped_column(CompatibleJSON, nullable=False, default=list)
    timeout_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    max_response_size_kb: Mapped[int] = mapped_column(Integer, nullable=False, default=1024)
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="configured")
    config_data: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="connectors")

    __table_args__ = (
        Index("idx_project_connector_name", "project_id", "name", unique=True),
    )


class RepairLog(Base):
    """Test-guided repair iteration log."""
    __tablename__ = "repair_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    initial_status: Mapped[str] = mapped_column(String(50), nullable=False)
    failure_diagnostics: Mapped[List[str]] = mapped_column(CompatibleJSON, nullable=False, default=list)
    patches: Mapped[List[Dict[str, Any]]] = mapped_column(CompatibleJSON, nullable=False, default=list)
    rerun_status: Mapped[str] = mapped_column(String(50), nullable=False)
    checks_rerun: Mapped[List[str]] = mapped_column(CompatibleJSON, nullable=False, default=list)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="repair_logs")


class AuditEventModel(Base):
    """Tamper-evident system audit event."""
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    details: Mapped[Dict[str, Any]] = mapped_column(CompatibleJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="audit_events")

