"""Pydantic schemas for Module F: Code Generation Engine.

Defines the structure for generated project files, manifest metadata,
and path safety validation.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from backend.app.schemas.common import ArchitectureArchetype


class GeneratedFile(BaseModel):
    """An individual source or configuration file generated from the architecture."""
    model_config = ConfigDict(extra="ignore")

    relative_path: str = Field(
        ...,
        description="Path relative to the generated project root (e.g. app/routers/items.py)",
    )
    content: str = Field(..., description="Full text content of the generated file")
    language: str = Field(default="python", description="Language or format (python, json, markdown, yaml)")
    purpose: str = Field(..., description="Functional purpose of this file within the architecture")

    @field_validator("relative_path")
    @classmethod
    def validate_safe_relative_path(cls, v: str) -> str:
        """Prevent path traversal vulnerabilities."""
        normalized = v.replace("\\", "/").strip()
        if normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized or normalized == "..":
            raise ValueError(f"Dangerous or traversal path detected: {v}")
        if ":" in normalized:  # Windows drive letter protection
            raise ValueError(f"Absolute path with drive letter detected: {v}")
        return normalized


class CodegenManifest(BaseModel):
    """Manifest of real project files generated for the selected architecture."""
    model_config = ConfigDict(extra="ignore")

    project_name: str = Field(...)
    archetype: ArchitectureArchetype = Field(...)
    target_stack: str = Field(default="Python 3.12+ / FastAPI / Pydantic")
    files: list[GeneratedFile] = Field(default_factory=list)
    total_files: int = Field(default=0)
    setup_instructions: list[str] = Field(
        default_factory=list,
        description="Step-by-step commands to run tests or start the generated project",
    )
    completeness_notes: str = Field(
        ...,
        description="Transparent statement of what was generated versus stubs or external services",
    )
    is_fully_generated: bool = Field(
        default=True,
        description="False if generation was truncated or partial",
    )
