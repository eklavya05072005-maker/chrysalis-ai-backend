import re
import unicodedata
from pathlib import Path
from typing import Union
from fastapi import HTTPException, status


def sanitize_filename(filename: str) -> str:
    """
    Sanitize an untrusted user-supplied filename.
    Strips directory separators, null bytes, and non-printable characters.
    """
    if not filename:
        return "unnamed_file"

    # Normalize unicode characters
    cleaned = unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode("ascii")
    # Extract only the base name (strip any leading directory traversal)
    cleaned = Path(cleaned).name
    # Keep only alphanumeric characters, dashes, underscores, and dots
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", cleaned)
    # Remove consecutive dots (prevent .. path escapes)
    cleaned = re.sub(r"\.{2,}", ".", cleaned)

    # Disallow naked '.', '..', or empty names
    if cleaned in ("", ".", ".."):
        cleaned = "unnamed_file"

    return cleaned


def resolve_safe_path(base_dir: Union[str, Path], relative_path: Union[str, Path]) -> Path:
    """
    Resolves a path relative to base_dir, strictly validating that the target path
    does not escape base_dir (preventing directory traversal attacks).
    Raises HTTPException 400 if a traversal attempt is detected.
    """
    base = Path(base_dir).resolve()
    target = (base / relative_path).resolve()

    try:
        # relative_to will raise ValueError if target is not a subpath of base
        target.relative_to(base)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path: path traversal detected.",
        )

    return target
