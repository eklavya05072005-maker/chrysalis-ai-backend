"""Module H: Explainable System Verdict Engine for Chrysalis AI.

Determines the holistic system implementation recommendation:
- Non-agentic: Conventional deterministic microservices / scripts / CRUD.
- Agentic: Autonomous multi-agent coordination with tool calling and dynamic planning.
- Hybrid: Mixed architecture combining deterministic transaction boundaries with
  AI-assisted classification and bounded agentic supervisors.

Strictly separated from Module C's concrete architecture candidates (Conservative,
Hybrid Agentic, Automation-Heavy). Never relies solely on a numerical score.
"""

from __future__ import annotations
import logging
from typing import Any

from backend.app.ai.prompts import (
    SYSTEM_VERDICT_SYSTEM_PROMPT,
    build_system_verdict_prompt,
)
from backend.app.core.config import Settings, get_settings
from backend.app.integrations.llm_client import (
    LLMClient,
    LLMError,
    LLMTimeoutError,
    get_llm_client,
)
from backend.app.schemas.analysis import RequirementAnalysisResult
from backend.app.schemas.classification import TaskClassificationResult
from backend.app.schemas.common import TaskCategory
from backend.app.schemas.verdict import (
    SystemVerdictResult,
    SystemVerdictType,
)
from backend.app.schemas.wizard import ConfirmedProjectSpec
from backend.app.ai.spec_confirmer import RequirementConfirmer

logger = logging.getLogger(__name__)


def _compute_deterministic_heuristic(
    confirmed_spec: ConfirmedProjectSpec,
    classification: TaskClassificationResult,
) -> tuple[SystemVerdictType, str, str, float, float, bool, int, int, int]:
    """
    Computes rule-based architectural verdict heuristics based on task distribution,
    autonomy boundaries, and safety constraints.
    Returns (verdict, headline, default_reasoning, det_ratio, agentic_ratio, needs_approval, det_count, ai_count, agentic_count).
    """
    tasks = classification.classifications
    total_tasks = len(tasks)

    det_count = sum(1 for t in tasks if t.category == TaskCategory.DETERMINISTIC)
    ai_count = sum(1 for t in tasks if t.category == TaskCategory.AI_ASSISTED)
    agentic_count = sum(1 for t in tasks if t.category == TaskCategory.AGENTIC)

    det_ratio = det_count / total_tasks if total_tasks > 0 else 1.0
    agentic_ratio = agentic_count / total_tasks if total_tasks > 0 else 0.0

    # Check if human approval or sensitive gates are mandated
    needs_approval = (
        confirmed_spec.autonomy_boundary == "human_approval_for_sensitive_actions"
        or any(t.human_approval_required for t in tasks)
        or any("approval" in (r.description or "").lower() for r in getattr(confirmed_spec, "confirmed_requirements", []))
        or any("approval" in (r.description or "").lower() for r in getattr(confirmed_spec, "business_rules", []))
    )

    # 1. Non-Agentic Heuristic: Purely or predominantly deterministic (>= 80% det, 0 agentic)
    if (det_ratio >= 0.8 and agentic_count == 0) or (confirmed_spec.autonomy_boundary == "suggest_only" and agentic_count == 0):
        verdict = SystemVerdictType.NON_AGENTIC
        headline = f"Non-Agentic Conventional Implementation Recommended for {confirmed_spec.project_name}"
        reasoning = (
            f"The task suite is predominantly deterministic ({det_count}/{total_tasks} tasks). "
            "Operations follow predictable rules and fixed workflows. Forcing an autonomous agent would introduce "
            "unnecessary latency, token costs, and nondeterministic failure modes. Standard API endpoints, "
            "rules engines, and unit tests provide the safest and most reliable implementation."
        )

    # 2. Agentic Heuristic: Exclusively or predominantly agentic with no conflicting deterministic core
    elif (agentic_count >= 1 and det_count == 0) or (agentic_ratio >= 0.75 and det_count == 0):
        verdict = SystemVerdictType.AGENTIC
        headline = f"Agentic AI Architecture Recommended for {confirmed_spec.project_name}"
        reasoning = (
            f"The requirements demand dynamic tool selection and multi-step investigation ({agentic_count}/{total_tasks} agentic tasks). "
            "Because inputs and resolution paths are unpredictable, a dynamic reasoning agent with access to approved tool "
            "connectors and bounded autonomy provides the required adaptability."
        )

    # 3. Hybrid Heuristic: Composite tasks combining deterministic rules with AI interpretation/planning
    else:
        verdict = SystemVerdictType.HYBRID
        headline = f"Hybrid Architecture Recommended for {confirmed_spec.project_name}"
        reasoning = (
            f"The system exhibits composite operational requirements: {det_count} deterministic rule checks "
            f"combined with {ai_count} AI-assisted parsing tasks and {agentic_count} agentic workflows. "
            "A hybrid architecture cleanly separates concerns: conventional code guarantees strict policy enforcement "
            "and transactional calculations, while agentic components handle open-ended interpretation and tool coordination "
            "under mandatory human oversight."
        )

    return verdict, headline, reasoning, det_ratio, agentic_ratio, needs_approval, det_count, ai_count, agentic_count


class SystemVerdictEngine:
    """Orchestrates generation of the explainable system-level implementation verdict."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.llm_client = llm_client or get_llm_client(self.settings)

    def validate_inputs(
        self,
        first_input: Any,
        classification: Any,
        confirmed_spec: Any = None,
        analysis: Any = None,
    ) -> None:
        """Validate verdict input parameters."""
        if first_input is None and confirmed_spec is None and analysis is None:
            raise ValueError("Either analysis or confirmed_spec must be provided.")
        if classification is None or not isinstance(classification, TaskClassificationResult):
            raise ValueError("Task classification result must be provided.")

    def _sanitize_verdict(
        self,
        result: SystemVerdictResult,
        confirmed_spec: ConfirmedProjectSpec,
        classification: TaskClassificationResult,
    ) -> SystemVerdictResult:
        """Sanitize verdict boundaries, synchronize task ratios, and enforce safety gates."""
        if result.verdict not in (SystemVerdictType.NON_AGENTIC, SystemVerdictType.AGENTIC, SystemVerdictType.HYBRID):
            result.verdict = SystemVerdictType.HYBRID
        result.overall_verdict = result.verdict

        # Clamp confidence score
        if result.confidence_score < 0.0:
            result.confidence_score = 0.0
        elif result.confidence_score > 1.0:
            result.confidence_score = 1.0

        # Calculate rule heuristics for validation
        (
            h_verdict,
            h_headline,
            h_reasoning,
            det_ratio,
            agentic_ratio,
            needs_approval,
            det_count,
            ai_count,
            agentic_count,
        ) = _compute_deterministic_heuristic(confirmed_spec, classification)

        result.deterministic_task_ratio = det_ratio
        result.agentic_task_ratio = agentic_ratio
        result.deterministic_task_count = det_count
        result.ai_assisted_task_count = ai_count
        result.agentic_task_count = agentic_count

        # Enforce human approval if mandated by boundary
        if confirmed_spec.autonomy_boundary == "human_approval_for_sensitive_actions" or needs_approval:
            result.human_approval_required = True

        # Ensure project name alignment
        result.project_name = confirmed_spec.project_name

        # Ensure supporting evidence is populated from confirmed spec if LLM returned empty
        if not result.supporting_evidence and confirmed_spec.evidence_references:
            result.supporting_evidence = list(confirmed_spec.evidence_references[:3])

        # Ensure assumptions and limitations are present
        if not result.assumptions:
            result.assumptions = [
                f"Operating within {confirmed_spec.data_mode} data environment.",
                f"Connectors configured for: {', '.join(confirmed_spec.connector_preferences)}.",
                f"Autonomy bounded to: {confirmed_spec.autonomy_boundary.replace('_', ' ')}.",
            ]

        if not result.risks_and_limitations:
            result.risks_and_limitations = [
                "Latency overhead during external tool invocations.",
                "Potential tool timeout handled via circuit breaker and fallback handlers.",
            ]
        result.key_risks = list(result.risks_and_limitations)

        if not result.recommended_next_step or not result.recommended_next_step.strip():
            result.recommended_next_step = (
                f"Proceed to architecture generation matching the {result.verdict} verdict."
            )

        return result

    async def generate_verdict(
        self,
        analysis_or_spec: RequirementAnalysisResult | ConfirmedProjectSpec | None = None,
        classification: TaskClassificationResult | None = None,
        confirmed_spec: ConfirmedProjectSpec | None = None,
        analysis: RequirementAnalysisResult | None = None,
    ) -> SystemVerdictResult:
        """Synthesize explainable system implementation verdict."""
        self.validate_inputs(analysis_or_spec, classification, confirmed_spec, analysis)

        # Resolve confirmed_spec and analysis based on argument order
        spec_to_use: ConfirmedProjectSpec
        analysis_to_use: RequirementAnalysisResult | None = analysis

        if isinstance(analysis_or_spec, ConfirmedProjectSpec):
            spec_to_use = analysis_or_spec
        elif isinstance(confirmed_spec, ConfirmedProjectSpec):
            spec_to_use = confirmed_spec
            if isinstance(analysis_or_spec, RequirementAnalysisResult):
                analysis_to_use = analysis_or_spec
        elif isinstance(analysis_or_spec, RequirementAnalysisResult):
            analysis_to_use = analysis_or_spec
            confirmer = RequirementConfirmer()
            spec_to_use = confirmer.confirm_specification(analysis=analysis_or_spec, confirmed_by_user=False)
        elif analysis is not None:
            analysis_to_use = analysis
            confirmer = RequirementConfirmer()
            spec_to_use = confirmer.confirm_specification(analysis=analysis, confirmed_by_user=False)
        else:
            raise ValueError("Could not resolve ConfirmedProjectSpec for verdict evaluation.")

        assert classification is not None

        (
            h_verdict,
            h_headline,
            h_reasoning,
            det_ratio,
            agentic_ratio,
            needs_approval,
            det_count,
            ai_count,
            agentic_count,
        ) = _compute_deterministic_heuristic(spec_to_use, classification)

        prompt = build_system_verdict_prompt(
            confirmed_spec=spec_to_use,
            classification=classification,
            analysis=analysis_to_use,
        )

        try:
            raw_result = await self.llm_client.generate_structured(
                prompt=prompt,
                schema=SystemVerdictResult,
                system_instruction=SYSTEM_VERDICT_SYSTEM_PROMPT,
                temperature=self.settings.llm_temperature,
            )
            return self._sanitize_verdict(raw_result, spec_to_use, classification)
        except (LLMTimeoutError, LLMError) as exc:
            logger.warning(
                "LLM call during verdict generation encountered error (%s). Synthesizing deterministic verdict.",
                exc,
            )
            evidence_list = list(spec_to_use.evidence_references[:3])
            if not evidence_list:
                for item in classification.classifications:
                    if item.supporting_evidence:
                        evidence_list.extend(item.supporting_evidence[:2])
                        break

            fallback = SystemVerdictResult(
                project_name=spec_to_use.project_name,
                verdict=h_verdict,
                overall_verdict=h_verdict,
                headline=h_headline,
                confidence_score=0.92,
                reasoning=h_reasoning,
                supporting_evidence=evidence_list,
                deterministic_task_ratio=det_ratio,
                agentic_task_ratio=agentic_ratio,
                deterministic_task_count=det_count,
                ai_assisted_task_count=ai_count,
                agentic_task_count=agentic_count,
                assumptions=[
                    f"Operating within {spec_to_use.data_mode} data environment.",
                    f"Autonomy boundary: {spec_to_use.autonomy_boundary}.",
                ],
                risks_and_limitations=[
                    "Deterministic enforcement must be tested with boundary value cases.",
                    "Agentic tool operations require timeout and circuit-breaker guardrails.",
                ],
                human_approval_required=needs_approval,
                recommended_next_step=f"Generate 3 concrete architecture proposals aligned with the {h_verdict} path.",
            )
            return fallback
        except Exception as exc:
            logger.error("Unexpected error in SystemVerdictEngine: %s", exc)
            fallback = SystemVerdictResult(
                project_name=spec_to_use.project_name,
                verdict=h_verdict,
                overall_verdict=h_verdict,
                headline=h_headline,
                confidence_score=0.88,
                reasoning=h_reasoning,
                supporting_evidence=list(spec_to_use.evidence_references[:3]),
                deterministic_task_ratio=det_ratio,
                agentic_task_ratio=agentic_ratio,
                deterministic_task_count=det_count,
                ai_assisted_task_count=ai_count,
                agentic_task_count=agentic_count,
                assumptions=[f"Autonomy boundary: {spec_to_use.autonomy_boundary}."],
                risks_and_limitations=["Review human approval checkpoints before production."],
                human_approval_required=needs_approval,
                recommended_next_step=f"Proceed with {h_verdict} architecture generation.",
            )
            return fallback


async def generate_system_verdict(
    analysis: RequirementAnalysisResult | None = None,
    classification: TaskClassificationResult | None = None,
    confirmed_spec: ConfirmedProjectSpec | None = None,
    llm_client: LLMClient | None = None,
    settings: Settings | None = None,
) -> SystemVerdictResult:
    """Convenience helper to synthesize system verdict."""
    engine = SystemVerdictEngine(llm_client=llm_client, settings=settings)
    return await engine.generate_verdict(
        analysis_or_spec=confirmed_spec or analysis,
        classification=classification,
        confirmed_spec=confirmed_spec,
        analysis=analysis,
    )
