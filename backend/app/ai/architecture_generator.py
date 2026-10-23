"""Module C: Architecture Search Engine for Chrysalis AI.

Generates exactly three distinct architecture candidates (Conservative, Hybrid Agentic,
and Automation-Heavy) addressing the identical specification requirements with explicit trade-offs.
"""

from __future__ import annotations
import logging
from typing import Any
from backend.app.ai.prompts import (
    ARCHITECTURE_SEARCH_SYSTEM_PROMPT,
    build_architecture_search_prompt,
)
from backend.app.core.config import Settings, get_settings
from backend.app.integrations.llm_client import (
    LLMClient,
    LLMError,
    LLMTimeoutError,
    get_llm_client,
)
from backend.app.schemas.analysis import RequirementAnalysisResult
from backend.app.schemas.architecture import (
    ArchitectureCandidate,
    ArchitectureCandidatesResult,
)
from backend.app.schemas.classification import TaskClassificationResult
from backend.app.schemas.common import ArchitectureArchetype

logger = logging.getLogger(__name__)


class ArchitectureSearchEngine:
    """Orchestrates candidate architecture exploration across three archetypes."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.llm_client = llm_client or get_llm_client(self.settings)

    def validate_inputs(self, analysis: RequirementAnalysisResult) -> None:
        """Validate requirement input before invoking LLM generation."""
        if analysis is None:
            raise ValueError("Requirement analysis must be provided.")

        if not analysis.functional_requirements and not analysis.modules and not analysis.business_rules:
            raise ValueError(
                "Requirement analysis contains no functional requirements, modules, or business rules to architect."
            )

    def _verify_and_sanitize_candidates(
        self,
        result: ArchitectureCandidatesResult,
        analysis: RequirementAnalysisResult,
    ) -> ArchitectureCandidatesResult:
        """Verify candidate completeness, archetype distribution, and complexity bounds."""
        if len(result.candidates) != 3:
            raise LLMError(
                f"Architecture Search Engine must generate exactly 3 candidates, but received {len(result.candidates)}."
            )

        found_archetypes = set()
        for cand in result.candidates:
            # 1. Bounds check on complexity score (1.0 to 10.0)
            if cand.complexity_score < 1.0:
                logger.warning("Clamping complexity score %s to 1.0 for candidate %s", cand.complexity_score, cand.candidate_id)
                cand.complexity_score = 1.0
            elif cand.complexity_score > 10.0:
                logger.warning("Clamping complexity score %s to 10.0 for candidate %s", cand.complexity_score, cand.candidate_id)
                cand.complexity_score = 10.0

            found_archetypes.add(cand.archetype)

        required_archetypes = {
            ArchitectureArchetype.CONSERVATIVE,
            ArchitectureArchetype.HYBRID_AGENTIC,
            ArchitectureArchetype.AUTOMATION_HEAVY,
        }

        # Check if all 3 archetypes are represented
        missing = required_archetypes - found_archetypes
        if missing:
            logger.warning(
                "Generated candidates are missing required archetypes: %s. Candidates found: %s",
                [m.value for m in missing],
                [c.archetype.value for c in result.candidates],
            )

        # Ensure project name alignment
        if not result.project_name or result.project_name.strip() == "":
            result.project_name = analysis.project_name

        return result

    async def generate_candidates(
        self,
        analysis: RequirementAnalysisResult,
        classification: TaskClassificationResult | None = None,
        spec_text: str = "",
    ) -> ArchitectureCandidatesResult:
        """Generate 3 distinct architecture candidates grounded in requirements and task classifications."""
        self.validate_inputs(analysis)

        prompt = build_architecture_search_prompt(
            analysis=analysis,
            classification=classification,
            spec_text=spec_text,
        )

        try:
            raw_result = await self.llm_client.generate_structured(
                prompt=prompt,
                schema=ArchitectureCandidatesResult,
                system_instruction=ARCHITECTURE_SEARCH_SYSTEM_PROMPT,
                temperature=self.settings.llm_temperature,
            )
        except LLMTimeoutError as exc:
            logger.error("LLM timeout during architecture candidate generation: %s", exc)
            raise
        except LLMError as exc:
            logger.error("LLM error during architecture candidate generation: %s", exc)
            raise
        except Exception as exc:
            logger.error("Unexpected error in ArchitectureSearchEngine: %s", exc)
            raise LLMError(f"Unexpected error generating architecture candidates: {exc}") from exc

        return self._verify_and_sanitize_candidates(raw_result, analysis)


async def generate_architecture_candidates(
    analysis: RequirementAnalysisResult,
    classification: TaskClassificationResult | None = None,
    llm_client: LLMClient | None = None,
    settings: Settings | None = None,
    spec_text: str = "",
) -> ArchitectureCandidatesResult:
    """Convenience helper for Member 2 backend to trigger architecture search."""
    engine = ArchitectureSearchEngine(llm_client=llm_client, settings=settings)
    return await engine.generate_candidates(
        analysis=analysis,
        classification=classification,
        spec_text=spec_text,
    )
