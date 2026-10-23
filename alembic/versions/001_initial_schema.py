"""Initial Chrysalis AI schema with PostgreSQL tables and JSONB

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-23 14:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)
    op.create_index(op.f("ix_projects_status"), "projects", ["status"], unique=False)

    # 2. Uploaded Documents table
    op.create_table(
        "uploaded_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("upload_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_uploaded_documents_project_id"), "uploaded_documents", ["project_id"], unique=False)

    # 3. Requirements table
    op.create_table(
        "requirements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requirement_type", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_requirements_priority"), "requirements", ["priority"], unique=False)
    op.create_index(op.f("ix_requirements_project_id"), "requirements", ["project_id"], unique=False)
    op.create_index(op.f("ix_requirements_requirement_type"), "requirements", ["requirement_type"], unique=False)

    # 4. Architecture Options table
    op.create_table(
        "architecture_options",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("components", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("connections", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("pros", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("cons", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("risks", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("estimated_cost", sa.String(length=100), nullable=False),
        sa.Column("estimated_latency", sa.String(length=100), nullable=False),
        sa.Column("complexity", sa.String(length=50), nullable=False),
        sa.Column("human_approval_required", sa.Boolean(), nullable=False),
        sa.Column("is_selected", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_architecture_options_is_selected"), "architecture_options", ["is_selected"], unique=False)
    op.create_index(op.f("ix_architecture_options_project_id"), "architecture_options", ["project_id"], unique=False)

    # 5. Simulation Results table
    op.create_table(
        "simulation_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("architecture_id", sa.Uuid(), nullable=False),
        sa.Column("scenario_name", sa.String(length=255), nullable=False),
        sa.Column("input_data", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("expected_outcome", sa.Text(), nullable=False),
        sa.Column("simulated_outcome", sa.Text(), nullable=False),
        sa.Column("result_status", sa.String(length=50), nullable=False),
        sa.Column("metrics", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["architecture_id"], ["architecture_options.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_simulation_results_architecture_id"), "simulation_results", ["architecture_id"], unique=False)
    op.create_index(op.f("ix_simulation_results_project_id"), "simulation_results", ["project_id"], unique=False)
    op.create_index(op.f("ix_simulation_results_result_status"), "simulation_results", ["result_status"], unique=False)

    # 6. Generated Files table
    op.create_table(
        "generated_files",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("relative_path", sa.String(length=500), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("validation_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_generated_files_project_id"), "generated_files", ["project_id"], unique=False)
    op.create_index(op.f("ix_generated_files_validation_status"), "generated_files", ["validation_status"], unique=False)
    op.create_index("idx_project_relative_path", "generated_files", ["project_id", "relative_path"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_project_relative_path", table_name="generated_files")
    op.drop_index(op.f("ix_generated_files_validation_status"), table_name="generated_files")
    op.drop_index(op.f("ix_generated_files_project_id"), table_name="generated_files")
    op.drop_table("generated_files")

    op.drop_index(op.f("ix_simulation_results_result_status"), table_name="simulation_results")
    op.drop_index(op.f("ix_simulation_results_project_id"), table_name="simulation_results")
    op.drop_index(op.f("ix_simulation_results_architecture_id"), table_name="simulation_results")
    op.drop_table("simulation_results")

    op.drop_index(op.f("ix_architecture_options_project_id"), table_name="architecture_options")
    op.drop_index(op.f("ix_architecture_options_is_selected"), table_name="architecture_options")
    op.drop_table("architecture_options")

    op.drop_index(op.f("ix_requirements_requirement_type"), table_name="requirements")
    op.drop_index(op.f("ix_requirements_project_id"), table_name="requirements")
    op.drop_index(op.f("ix_requirements_priority"), table_name="requirements")
    op.drop_table("requirements")

    op.drop_index(op.f("ix_uploaded_documents_project_id"), table_name="uploaded_documents")
    op.drop_table("uploaded_documents")

    op.drop_index(op.f("ix_projects_status"), table_name="projects")
    op.drop_index(op.f("ix_projects_name"), table_name="projects")
    op.drop_table("projects")
