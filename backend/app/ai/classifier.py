"""Module B: Task Classification Engine for Chrysalis AI.

Classifies software requirements and workflow tasks into deterministic, AI-assisted,
or agentic implementations with explicit rationale, confidence scores, and safety gates.
"""

from __future__ import annotations
import logging
from typing import Any
from backend.app.ai.analyzer import is_quote_grounded
from backend.app.ai.prompts import (
    TASK_CLASSIFICATION_SYSTEM_PROMPT,
    build_task_classification_prompt,
)
from backend.app.core.config import Settings, get_settings
from backend.app.integrations.llm_client import (
    LLMClient,
    LLMError,
    LLMTimeoutError,
    get_llm_client,
)
from backend.app.schemas.analysis import RequirementAnalysisResult
from backend.app.schemas.classification import (
    TaskClassification,
    TaskClassificationResult,
)
from backend.app.schemas.common import TaskCategory

logger = logging.getLogger(__name__)


class TaskClassifier:
    """Orchestrates deterministic vs AI-assisted vs agentic workflow classification."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.llm_client = llm_client or get_llm_client(self.settings)

    def extract_tasks_from_analysis(
        self,
        analysis: RequirementAnalysisResult,
    ) -> list[dict[str, Any]]:
        """Extract candidate tasks from functional requirements, business rules, and workflows."""
        candidate_tasks: list[dict[str, Any]] = []

        # 1. Functional Requirements
        for req in analysis.functional_requirements:
            candidate_tasks.append({
                "task_id": req.req_id,
                "task_name": req.title,
                "description": req.description,
                "source_type": "functional_requirement",
                "evidence": req.evidence,
            })

        # 2. Business Rules (usually prime candidates for deterministic enforcement)
        for rule in analysis.business_rules:
            candidate_tasks.append({
                "task_id": rule.rule_id,
                "task_name": f"Rule: {rule.rule_id}",
                "description": f"Enforce constraint: {rule.description}",
                "source_type": "business_rule",
                "evidence": rule.evidence,
            })

        # 3. Workflows (may involve multi-step agentic pipelines)
        for wf in analysis.workflows:
            candidate_tasks.append({
                "task_id": wf.workflow_id,
                "task_name": f"Workflow: {wf.name}",
                "description": f"Trigger: {wf.trigger}. Steps: {', '.join([s.action for s in wf.steps])}",
                "source_type": "workflow",
                "evidence": [],
            })

        return candidate_tasks

    def _sanitize_and_verify_classifications(
        self,
        result: TaskClassificationResult,
        spec_text: str = "",
        analysis_evidence_text: str = "",
    ) -> TaskClassificationResult:
        """Validate confidence boundaries, recalculate summary counts, and verify evidence."""
        counts = {
            TaskCategory.DETERMINISTIC.value: 0,
            TaskCategory.AI_ASSISTED.value: 0,
            TaskCategory.AGENTIC.value: 0,
        }

        full_grounding_text = f"{spec_text}\n{analysis_evidence_text}".strip()

        for item in result.classifications:
            # 1. Validate & clamp confidence boundaries (0.0 to 1.0)
            if item.confidence is not None:
                if item.confidence < 0.0:
                    logger.warning("Clamping negative confidence %s to 0.0 for task %s", item.confidence, item.task_id)
                    item.confidence = 0.0
                elif item.confidence > 1.0:
                    logger.warning("Clamping excessive confidence %s to 1.0 for task %s", item.confidence, item.task_id)
                    item.confidence = 1.0

            # 2. Track category counts
            cat_val = item.category.value if isinstance(item.category, TaskCategory) else str(item.category)
            if cat_val in counts:
                counts[cat_val] += 1
            else:
                counts[cat_val] = 1

            # 3. Verify evidence grounding
            if full_grounding_text:
                for ref in item.supporting_evidence:
                    if not is_quote_grounded(ref.exact_quote, full_grounding_text):
                        logger.warning(
                            "Ungrounded quote in task classification for %s: '%s'",
                            item.task_id,
                            ref.exact_quote[:80],
                        )

        # Synchronize summary counts with actual list contents
        result.summary_counts = counts
        return result

    async def classify(
        self,
        analysis: RequirementAnalysisResult,
        spec_text: str = "",
    ) -> TaskClassificationResult:
        """Classify tasks extracted from requirement analysis into implementation paradigms."""
        if analysis is None:
            raise ValueError("Requirement analysis result must be provided.")

        candidate_tasks = self.extract_tasks_from_analysis(analysis)

        # Handle empty analysis gracefully
        if not candidate_tasks:
            return TaskClassificationResult(
                classifications=[],
                summary_counts={
                    TaskCategory.DETERMINISTIC.value: 0,
                    TaskCategory.AI_ASSISTED.value: 0,
                    TaskCategory.AGENTIC.value: 0,
                },
                classification_notes="No candidate tasks or requirements identified for classification.",
            )

        prompt = build_task_classification_prompt(
            analysis=analysis,
            tasks_to_classify=candidate_tasks,
            spec_text=spec_text,
        )

        try:
            raw_result = await self.llm_client.generate_structured(
                prompt=prompt,
                schema=TaskClassificationResult,
                system_instruction=TASK_CLASSIFICATION_SYSTEM_PROMPT,
                temperature=self.settings.llm_temperature,
            )
        except LLMTimeoutError as exc:
            logger.error("LLM timeout during task classification: %s", exc)
            raise
        except LLMError as exc:
            logger.error("LLM error during task classification: %s", exc)
            raise
        except Exception as exc:
            logger.error("Unexpected error in TaskClassifier: %s", exc)
            raise LLMError(f"Unexpected error during task classification: {exc}") from exc

        # Collect text from existing analysis evidence for grounding check
        analysis_evidence_text = "\n".join([ref.exact_quote for ref in analysis.evidence_references])

        # Sanitize confidence, verify evidence, and sync counts
        return self._sanitize_and_verify_classifications(
            result=raw_result,
            spec_text=spec_text,
            analysis_evidence_text=analysis_evidence_text,
        )


async def classify_tasks(
    analysis: RequirementAnalysisResult,
    llm_client: LLMClient | None = None,
    settings: Settings | None = None,
    spec_text: str = "",
) -> TaskClassificationResult:
    """Convenience helper for Member 2 backend to trigger task classification."""
    classifier = TaskClassifier(llm_client=llm_client, settings=settings)
    return await classifier.classify(analysis=analysis, spec_text=spec_text)
