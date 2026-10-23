"""Module A: Requirement Analyzer for Chrysalis AI.

Transforms raw software specification documents into structured, evidence-backed
models with strict citation verification against source text.
"""

from __future__ import annotations
import logging
import re
from typing import Any
from backend.app.ai.prompts import (
    REQUIREMENT_ANALYSIS_SYSTEM_PROMPT,
    build_requirement_analysis_prompt,
)
from backend.app.core.config import Settings, get_settings
from backend.app.integrations.llm_client import (
    LLMClient,
    LLMError,
    LLMTimeoutError,
    get_llm_client,
)
from backend.app.schemas.analysis import (
    AnalyzeRequest,
    RequirementAnalysisResult,
)
from backend.app.schemas.common import EvidenceReference

logger = logging.getLogger(__name__)


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace and newlines for robust substring matching."""
    return re.sub(r"\s+", " ", text).strip().lower()


def is_quote_grounded(
    quote: str,
    spec_text: str,
    source_pages: dict[str, str] | None = None,
) -> bool:
    """Verify that a quotation actually exists as a substring in the source material.
    
    Checks both raw text and whitespace-normalized text.
    """
    clean_quote = quote.strip()
    if not clean_quote:
        return False

    # 1. Direct substring match
    if clean_quote in spec_text:
        return True

    # 2. Check individual pages if provided
    if source_pages:
        for page_text in source_pages.values():
            if clean_quote in page_text:
                return True

    # 3. Normalized whitespace comparison (handles multiline linebreaks / OCR spacing)
    norm_quote = _normalize_whitespace(clean_quote)
    norm_spec = _normalize_whitespace(spec_text)
    if norm_quote in norm_spec:
        return True

    if source_pages:
        for page_text in source_pages.values():
            if norm_quote in _normalize_whitespace(page_text):
                return True

    return False


class RequirementAnalyzer:
    """Orchestrates structured requirement extraction with evidence grounding."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.llm_client = llm_client or get_llm_client(self.settings)

    def validate_request(self, request: AnalyzeRequest) -> None:
        """Validate input payload before making external calls."""
        if not request.spec_text or not request.spec_text.strip():
            raise ValueError("Specification text cannot be empty or whitespace.")

        if len(request.spec_text.strip()) < 10:
            raise ValueError(
                f"Specification text is too short ({len(request.spec_text.strip())} chars). "
                "Minimum 10 characters required."
            )

    def verify_and_sync_evidence(
        self,
        result: RequirementAnalysisResult,
        request: AnalyzeRequest,
    ) -> RequirementAnalysisResult:
        """Verify that all evidence citations are grounded in the source text.
        
        Logs warnings for ungrounded citations and ensures master evidence list is synced.
        """
        all_refs: list[EvidenceReference] = []

        # Check references in business rules
        for rule in result.business_rules:
            verified_rule_refs = []
            for ref in rule.evidence:
                if not is_quote_grounded(ref.exact_quote, request.spec_text, request.source_pages):
                    logger.warning(
                        "Ungrounded quote detected in BusinessRule %s: '%s'",
                        rule.rule_id,
                        ref.exact_quote[:80],
                    )
                verified_rule_refs.append(ref)
                all_refs.append(ref)
            rule.evidence = verified_rule_refs

        # Check references in functional requirements
        for req in result.functional_requirements:
            verified_req_refs = []
            for ref in req.evidence:
                if not is_quote_grounded(ref.exact_quote, request.spec_text, request.source_pages):
                    logger.warning(
                        "Ungrounded quote detected in Functional Req %s: '%s'",
                        req.req_id,
                        ref.exact_quote[:80],
                    )
                verified_req_refs.append(ref)
                all_refs.append(ref)
            req.evidence = verified_req_refs

        # Check references in non-functional requirements
        for req in result.non_functional_requirements:
            for ref in req.evidence:
                if not is_quote_grounded(ref.exact_quote, request.spec_text, request.source_pages):
                    logger.warning(
                        "Ungrounded quote detected in Non-Functional Req %s: '%s'",
                        req.req_id,
                        ref.exact_quote[:80],
                    )
                all_refs.append(ref)

        # Include direct citations from master list
        for ref in result.evidence_references:
            if not is_quote_grounded(ref.exact_quote, request.spec_text, request.source_pages):
                logger.warning(
                    "Ungrounded quote in master evidence index: '%s'",
                    ref.exact_quote[:80],
                )
            all_refs.append(ref)

        # Deduplicate master evidence references by exact quote and source doc
        seen: set[tuple[str, str]] = set()
        deduped: list[EvidenceReference] = []
        for ref in all_refs:
            key = (ref.source_doc, ref.exact_quote.strip())
            if key not in seen:
                seen.add(key)
                deduped.append(ref)

        result.evidence_references = deduped

        # Preserve caller's project name override if provided
        if request.project_name and request.project_name.strip():
            result.project_name = request.project_name.strip()

        return result

    async def analyze(self, request: AnalyzeRequest) -> RequirementAnalysisResult:
        """Perform end-to-end requirement analysis on specification text."""
        self.validate_request(request)

        prompt = build_requirement_analysis_prompt(request)

        try:
            raw_result = await self.llm_client.generate_structured(
                prompt=prompt,
                schema=RequirementAnalysisResult,
                system_instruction=REQUIREMENT_ANALYSIS_SYSTEM_PROMPT,
                temperature=self.settings.llm_temperature,
            )
        except LLMTimeoutError as exc:
            logger.error("LLM timeout during requirement analysis: %s", exc)
            raise
        except LLMError as exc:
            logger.error("LLM error during requirement analysis: %s", exc)
            raise
        except Exception as exc:
            logger.error("Unexpected error in RequirementAnalyzer: %s", exc)
            raise LLMError(f"Unexpected error analyzing requirements: {exc}") from exc

        # Verify evidence grounding and sync citations
        verified_result = self.verify_and_sync_evidence(raw_result, request)
        return verified_result


async def analyze_requirements(
    request: AnalyzeRequest,
    llm_client: LLMClient | None = None,
    settings: Settings | None = None,
) -> RequirementAnalysisResult:
    """Convenience function for Member 2 backend to trigger requirement analysis."""
    analyzer = RequirementAnalyzer(llm_client=llm_client, settings=settings)
    return await analyzer.analyze(request)
