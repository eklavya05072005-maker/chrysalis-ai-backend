import os
import uuid
import zipfile
from pathlib import Path
from typing import Tuple, Optional
from fastapi import HTTPException, status

from backend.app.core.config import settings
from backend.app.core.security import sanitize_filename, resolve_safe_path

# Disallowed directory patterns in generated zip packaging
DISALLOWED_DIRS = {
    ".venv",
    "venv",
    "env",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
}

# Disallowed file patterns in generated zip packaging (secrets, OS artifacts)
DISALLOWED_FILE_PREFIXES = (".env",)
DISALLOWED_FILE_SUFFIXES = (".pem", ".key", ".pyc")
DISALLOWED_EXACT_FILES = {"id_rsa", "id_dsa", ".ds_store", "thumbs.db"}


class StorageService:
    """
    Abstracted physical file storage service.
    Isolates project files into:
      data/uploads/{project_id}/
      data/generated/{project_id}/
      data/packages/{project_id}/
    Guarantees strict directory containment, path-traversal prevention,
    and safe ZIP packaging with secrets/virtualenv exclusion.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or settings.data_path

    def _get_project_dir(self, category: str, project_id: uuid.UUID) -> Path:
        """Returns and creates the category directory for a given project."""
        proj_dir = self.base_dir / category / str(project_id)
        proj_dir.mkdir(parents=True, exist_ok=True)
        return proj_dir

    def save_upload(
        self,
        project_id: uuid.UUID,
        filename: str,
        content: bytes,
    ) -> Tuple[Path, str, int]:
        """
        Saves an uploaded document safely into data/uploads/{project_id}/.
        Generates a unique stored_filename to prevent collision and overwriting.
        Returns (stored_path, stored_filename, file_size).
        """
        clean_name = sanitize_filename(filename)
        stored_filename = f"{uuid.uuid4().hex}_{clean_name}"

        upload_dir = self._get_project_dir("uploads", project_id)
        target_path = resolve_safe_path(upload_dir, stored_filename)

        with open(target_path, "wb") as f:
            f.write(content)

        return target_path, stored_filename, len(content)

    def get_upload_path(self, project_id: uuid.UUID, stored_filename: str) -> Path:
        """Resolves the safe path to an uploaded document."""
        upload_dir = self._get_project_dir("uploads", project_id)
        target_path = resolve_safe_path(upload_dir, stored_filename)
        if not target_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Uploaded file {stored_filename} not found.",
            )
        return target_path

    def save_generated_file(
        self,
        project_id: uuid.UUID,
        relative_path: str,
        content: str,
    ) -> Tuple[Path, int]:
        """
        Saves a generated source code file into data/generated/{project_id}/[relative_path].
        Validates the subpath does not escape data/generated/{project_id}/.
        Returns (target_path, file_size).
        """
        # Normalize relative path separators and strip leading slashes
        clean_rel_path = relative_path.replace("\\", "/").lstrip("/")
        parts = clean_rel_path.split("/")
        safe_parts = [sanitize_filename(p) for p in parts if p]
        safe_rel_path = "/".join(safe_parts)

        gen_dir = self._get_project_dir("generated", project_id)
        target_path = resolve_safe_path(gen_dir, safe_rel_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        content_bytes = content.encode("utf-8")
        with open(target_path, "wb") as f:
            f.write(content_bytes)

        return target_path, len(content_bytes)

    def read_generated_file(self, project_id: uuid.UUID, relative_path: str) -> str:
        """Reads contents of a generated file."""
        clean_rel_path = relative_path.replace("\\", "/").lstrip("/")
        parts = clean_rel_path.split("/")
        safe_parts = [sanitize_filename(p) for p in parts if p]
        safe_rel_path = "/".join(safe_parts)

        gen_dir = self._get_project_dir("generated", project_id)
        target_path = resolve_safe_path(gen_dir, safe_rel_path)

        if not target_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {relative_path} not found.",
            )

        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def create_zip_package(self, project_id: uuid.UUID) -> Path:
        """
        Archives all valid generated files in data/generated/{project_id}/ into
        data/packages/{project_id}/chrysalis_project_{project_id}.zip.

        Strictly enforces:
        - Safe relative paths with no traversal ('..', absolute paths).
        - Exclusion of virtual environments (.venv, venv, env).
        - Exclusion of secrets (.env, *.pem, *.key, id_rsa).
        - Exclusion of build/cache artifacts (__pycache__, .git).
        """
        gen_dir = self._get_project_dir("generated", project_id)
        pkg_dir = self._get_project_dir("packages", project_id)
        zip_filename = f"chrysalis_project_{str(project_id)[:8]}.zip"
        zip_path = resolve_safe_path(pkg_dir, zip_filename)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(gen_dir):
                # Modify dirs in-place to prevent walking into disallowed directories
                dirs[:] = [d for d in dirs if d.lower() not in DISALLOWED_DIRS]

                for file in files:
                    lower_file = file.lower()

                    # Exclude secrets and OS metadata files
                    if (
                        any(lower_file.startswith(pre) for pre in DISALLOWED_FILE_PREFIXES)
                        or any(lower_file.endswith(suf) for suf in DISALLOWED_FILE_SUFFIXES)
                        or lower_file in DISALLOWED_EXACT_FILES
                    ):
                        continue

                    file_path = Path(root) / file

                    # Verify path traversal containment
                    try:
                        arcname = file_path.relative_to(gen_dir)
                    except ValueError:
                        continue

                    arcname_str = str(arcname).replace("\\", "/")
                    if (
                        ".." in arcname_str
                        or arcname_str.startswith("/")
                        or ":" in arcname_str
                    ):
                        continue

                    zipf.write(file_path, arcname=arcname_str)

        return zip_path

    def get_zip_package_path(self, project_id: uuid.UUID) -> Optional[Path]:
        """Returns existing ZIP package path if available."""
        pkg_dir = self._get_project_dir("packages", project_id)
        zip_filename = f"chrysalis_project_{str(project_id)[:8]}.zip"
        target_path = resolve_safe_path(pkg_dir, zip_filename)
        return target_path if target_path.exists() else None
