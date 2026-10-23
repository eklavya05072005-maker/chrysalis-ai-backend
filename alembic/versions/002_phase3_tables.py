"""Phase 3 schema additions: execution_runs, connectors, repair_logs, audit_events

Revision ID: 002_phase3_tables
Revises: 001_initial_schema
Create Date: 2026-10-23 19:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_phase3_tables"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Execution Runs table
    op.create_table(
        "execution_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("runtime", sa.String(length=50), nullable=False),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("elapsed_time_seconds", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("timed_out", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("resource_limit_hit", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("network_isolated", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("checks_performed", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_execution_runs_project_id"), "execution_runs", ["project_id"], unique=False)
    op.create_index(op.f("ix_execution_runs_status"), "execution_runs", ["status"], unique=False)

    # 2. Connectors table
    op.create_table(
        "connectors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("connector_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_mock", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_read_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allowed_endpoints", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("allowed_methods", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("allowed_tools", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("timeout_seconds", sa.Float(), nullable=False, server_default="10.0"),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("max_response_size_kb", sa.Integer(), nullable=False, server_default="1024"),
        sa.Column("state", sa.String(length=50), nullable=False, server_default="configured"),
        sa.Column("config_data", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_connectors_project_id"), "connectors", ["project_id"], unique=False)
    op.create_index(op.f("ix_connectors_connector_type"), "connectors", ["connector_type"], unique=False)
    op.create_index("idx_project_connector_name", "connectors", ["project_id", "name"], unique=True)

    # 3. Repair Logs table
    op.create_table(
        "repair_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("initial_status", sa.String(length=50), nullable=False),
        sa.Column("failure_diagnostics", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("patches", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("rerun_status", sa.String(length=50), nullable=False),
        sa.Column("checks_rerun", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_repair_logs_project_id"), "repair_logs", ["project_id"], unique=False)

    # 4. Audit Events table
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("actor", sa.String(length=100), nullable=False, server_default="system"),
        sa.Column("details", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_events_project_id"), "audit_events", ["project_id"], unique=False)
    op.create_index(op.f("ix_audit_events_event_type"), "audit_events", ["event_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_events_event_type"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_project_id"), table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index(op.f("ix_repair_logs_project_id"), table_name="repair_logs")
    op.drop_table("repair_logs")

    op.drop_index("idx_project_connector_name", table_name="connectors")
    op.drop_index(op.f("ix_connectors_connector_type"), table_name="connectors")
    op.drop_index(op.f("ix_connectors_project_id"), table_name="connectors")
    op.drop_table("connectors")

    op.drop_index(op.f("ix_execution_runs_status"), table_name="execution_runs")
    op.drop_index(op.f("ix_execution_runs_project_id"), table_name="execution_runs")
    op.drop_table("execution_runs")
