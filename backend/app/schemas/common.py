"""Common enums, value objects, and base models shared across Chrysalis AI modules.

All models here serve as the baseline contracts between Member 2 (FastAPI Backend)
and Member 3 (AI Engine).
"""

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class CheckStatus(str, Enum):
    """Execution status for tests and validation checks. Never fabricate passed results."""
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    NOT_RUN = "not_run"


class Severity(str, Enum):
    """Severity classification for risks and issues."""
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class TaskCategory(str, Enum):
    """Classification categories for software tasks."""
    DETERMINISTIC = "deterministic"
    AI_ASSISTED = "ai_assisted"
    AGENTIC = "agentic"


class ArchitectureArchetype(str, Enum):
    """The three standardized architecture candidates required for evaluation."""
    CONSERVATIVE = "conservative"
    HYBRID_AGENTIC = "hybrid_agentic"
    AUTOMATION_HEAVY = "automation_heavy"


class EvidenceReference(BaseModel):
    """Traceable reference to source specification text or document page.
    
    Never fabricate quotations, page numbers, or requirements.
    """
    model_config = ConfigDict(extra="forbid")

    source_doc: str = Field(
        ...,
        description="Source document name, identifier, or filename",
        min_length=1,
    )
    page_number: int | None = Field(
        default=None,
        description="Page number in the source material, if available",
        ge=1,
    )
    exact_quote: str = Field(
        ...,
        description="Verbatim text quotation from the source material establishing evidence",
        min_length=1,
    )
    relevance: str = Field(
        ...,
        description="Explanation of how this quotation supports the requirement or rule",
        min_length=3,
    )
