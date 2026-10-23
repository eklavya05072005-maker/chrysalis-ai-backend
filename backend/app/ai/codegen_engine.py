"""Module F: Code Generation Engine for Chrysalis AI.

Generates real, structured, compilable project files conforming to the selected
architecture candidate and validated requirements, with strict path safety,
secret protection, and overwrite defense.
"""

from __future__ import annotations
import logging
import os
import re
from pathlib import Path
from typing import Any

from backend.app.ai.prompts import (
    CODE_GENERATION_SYSTEM_PROMPT,
    build_code_generation_prompt,
)
from backend.app.core.config import Settings, get_settings
from backend.app.integrations.llm_client import (
    LLMClient,
    LLMError,
    LLMTimeoutError,
    get_llm_client,
)
from backend.app.schemas.analysis import RequirementAnalysisResult
from backend.app.schemas.architecture import ArchitectureCandidate
from backend.app.schemas.classification import TaskClassificationResult
from backend.app.schemas.codegen import CodegenManifest, GeneratedFile

logger = logging.getLogger(__name__)

# Patterns matching suspected hardcoded live secrets
SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"AIza[0-9A-Za-z-_]{25,}"),  # Google API key
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),     # OpenAI API key
    re.compile(r"ghp_[a-zA-Z0-9]{20,}"),    # GitHub Personal Access Token
    re.compile(r"(?i)api[_-]?key\s*=\s*['\"][0-9a-zA-Z-_]{16,}['\"]"),  # Generic live API key assignment
]


def validate_safe_output_path(base_dir: Path, relative_path: str) -> Path:
    """Enforce path-traversal protection and return safe absolute destination.
    
    Rejects:
    - Absolute paths (starting with / or \\)
    - Windows drive paths (e.g. C:)
    - Directory traversal segments (..)
    - Paths escaping base_dir
    """
    normalized = relative_path.replace("\\", "/").strip()
    if not normalized:
        raise ValueError("Relative path cannot be empty.")

    if ":" in normalized:
        raise ValueError(f"Absolute path with drive letter detected: {relative_path}")

    if normalized.startswith("/"):
        raise ValueError(f"Absolute unix path detected: {relative_path}")

    parts = [p for p in normalized.split("/") if p]
    if any(p == ".." for p in parts) or normalized.startswith("../"):
        raise ValueError(f"Dangerous path traversal detected: {relative_path}")

    resolved_base = base_dir.resolve()
    target_path = (resolved_base / Path(normalized)).resolve()

    try:
        target_path.relative_to(resolved_base)
    except ValueError as exc:
        raise ValueError(f"Path escapes designated output directory: {relative_path}") from exc

    return target_path


def verify_no_secrets(content: str, filename: str) -> None:
    """Ensure no live hardcoded secrets, keys, or passwords exist in generated content."""
    # .env.example with placeholders is explicitly permitted
    if filename.endswith(".env.example"):
        return

    for pattern in SECRET_PATTERNS:
        match = pattern.search(content)
        if match:
            # Check if it's just an innocent placeholder like your-api-key-here
            matched_str = match.group(0).lower()
            if not any(ph in matched_str for ph in ["your-", "dummy", "placeholder", "xxx", "example"]):
                raise ValueError(
                    f"Security violation: Suspected hardcoded secret detected in {filename}. "
                    "Use environment variables or .env.example placeholders."
                )


def write_manifest_to_disk(
    manifest: CodegenManifest,
    output_dir: Path | str,
    overwrite: bool = False,
) -> list[Path]:
    """Safely write manifest files into a designated output directory with traversal checks."""
    out_path = Path(output_dir).resolve()

    # Destination protection: do not overwrite existing user directories containing files unless explicitly requested
    if out_path.exists() and any(out_path.iterdir()) and not overwrite:
        raise FileExistsError(
            f"Target output directory '{out_path}' already exists and contains files. "
            "Set overwrite=True to allow overwriting."
        )

    out_path.mkdir(parents=True, exist_ok=True)
    created_paths: list[Path] = []

    for gen_file in manifest.files:
        verify_no_secrets(gen_file.content, gen_file.relative_path)
        dest_file = validate_safe_output_path(out_path, gen_file.relative_path)
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        dest_file.write_text(gen_file.content, encoding="utf-8")
        created_paths.append(dest_file)

    return created_paths


class CodegenEngine:
    """Orchestrates generation of complete project source code from selected architecture."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.llm_client = llm_client or get_llm_client(self.settings)

    def validate_inputs(
        self,
        selected_candidate: ArchitectureCandidate,
        analysis: RequirementAnalysisResult,
    ) -> None:
        """Verify candidate and requirements are valid for code generation."""
        if selected_candidate is None:
            raise ValueError("Selected architecture candidate must be provided.")
        if analysis is None:
            raise ValueError("Requirement analysis must be provided.")
        if not analysis.functional_requirements and not analysis.business_rules:
            raise ValueError("Requirement analysis must contain requirements or business rules to generate code.")

    def _verify_and_sanitize_manifest(
        self,
        manifest: CodegenManifest,
        selected_candidate: ArchitectureCandidate,
        analysis: RequirementAnalysisResult,
    ) -> CodegenManifest:
        """Validate paths, enforce security hygiene, and ensure core project files exist."""
        if not manifest.files:
            raise LLMError("Code generation returned an empty file manifest.")

        sanitized_files: list[GeneratedFile] = []
        existing_paths: set[str] = set()

        for f in manifest.files:
            # Validate path safety (triggers GeneratedFile validator if traversal present)
            clean_rel = f.relative_path.replace("\\", "/").strip()
            if clean_rel in existing_paths:
                continue
            existing_paths.add(clean_rel)
            f.relative_path = clean_rel

            # Validate no secrets
            verify_no_secrets(f.content, clean_rel)
            sanitized_files.append(f)

        manifest.files = sanitized_files
        manifest.project_name = manifest.project_name or analysis.project_name
        manifest.archetype = selected_candidate.archetype
        manifest.total_files = len(manifest.files)

        if not manifest.setup_instructions:
            manifest.setup_instructions = [
                "python -m venv .venv",
                "source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate",
                "pip install -r requirements.txt",
                "pytest tests/",
                "uvicorn app.main:app --reload",
            ]

        if not manifest.completeness_notes:
            manifest.completeness_notes = (
                f"Generated application codebase structured for {selected_candidate.name} ({selected_candidate.archetype.value}). "
                "Includes core schemas, endpoints, business rules, configuration template, and unit tests. "
                "Note that generated code requires integration verification before production deployment."
            )

        return manifest

    async def generate_manifest(
        self,
        selected_candidate: ArchitectureCandidate,
        analysis: RequirementAnalysisResult,
        classification: TaskClassificationResult | None = None,
        spec_text: str | None = None,
    ) -> CodegenManifest:
        """Generate structured CodegenManifest for the selected architecture."""
        self.validate_inputs(selected_candidate, analysis)

        prompt = build_code_generation_prompt(
            selected_candidate=selected_candidate,
            analysis=analysis,
            classification=classification,
            spec_text=spec_text,
        )

        try:
            raw_result = await self.llm_client.generate_structured(
                prompt=prompt,
                schema=CodegenManifest,
                system_instruction=CODE_GENERATION_SYSTEM_PROMPT,
                temperature=self.settings.llm_temperature,
            )
        except LLMTimeoutError as exc:
            logger.error("LLM timeout during code generation: %s", exc)
            raise
        except LLMError as exc:
            logger.error("LLM error during code generation: %s", exc)
            raise
        except Exception as exc:
            logger.error("Unexpected error in CodegenEngine: %s", exc)
            raise LLMError(f"Unexpected error during code generation: {exc}") from exc

        return self._verify_and_sanitize_manifest(raw_result, selected_candidate, analysis)

    async def generate_and_write(
        self,
        selected_candidate: ArchitectureCandidate,
        analysis: RequirementAnalysisResult,
        output_dir: Path | str,
        overwrite: bool = False,
        classification: TaskClassificationResult | None = None,
        spec_text: str | None = None,
    ) -> tuple[CodegenManifest, list[Path]]:
        """Generate project files and write them safely to the designated output directory."""
        manifest = await self.generate_manifest(
            selected_candidate=selected_candidate,
            analysis=analysis,
            classification=classification,
            spec_text=spec_text,
        )
        written_paths = write_manifest_to_disk(manifest, output_dir=output_dir, overwrite=overwrite)
        return manifest, written_paths


async def generate_project_code(
    selected_candidate: ArchitectureCandidate,
    analysis: RequirementAnalysisResult,
    output_dir: Path | str | None = None,
    overwrite: bool = False,
    classification: TaskClassificationResult | None = None,
    spec_text: str | None = None,
    llm_client: LLMClient | None = None,
    settings: Settings | None = None,
) -> tuple[CodegenManifest, list[Path] | None]:
    """Convenience helper to generate project manifest and optionally persist to disk."""
    engine = CodegenEngine(llm_client=llm_client, settings=settings)
    manifest = await engine.generate_manifest(
        selected_candidate=selected_candidate,
        analysis=analysis,
        classification=classification,
        spec_text=spec_text,
    )
    written_paths = None
    if output_dir:
        written_paths = write_manifest_to_disk(manifest, output_dir=output_dir, overwrite=overwrite)
    return manifest, written_paths
