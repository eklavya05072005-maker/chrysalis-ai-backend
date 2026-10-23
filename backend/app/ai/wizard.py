"""Module W: Adaptive Requirement Wizard for Chrysalis AI.

Generates 3 to 5 context-aware, multiple-choice questions from Module A's
RequirementAnalysisResult to clarify operational goals, autonomy boundaries,
connector types, data environments, and safety constraints.
"""

from __future__ import annotations
import logging
from typing import Any

from backend.app.ai.prompts import (
    ADAPTIVE_WIZARD_SYSTEM_PROMPT,
    build_adaptive_wizard_prompt,
)
from backend.app.core.config import Settings, get_settings
from backend.app.integrations.llm_client import (
    LLMClient,
    LLMError,
    LLMTimeoutError,
    get_llm_client,
)
from backend.app.schemas.analysis import RequirementAnalysisResult
from backend.app.schemas.wizard import (
    WizardOption,
    WizardQuestion,
    WizardQuestionnaire,
)

logger = logging.getLogger(__name__)


def _build_fallback_questionnaire(analysis: RequirementAnalysisResult) -> WizardQuestionnaire:
    """Constructs a deterministic, tailored questionnaire when LLM output is unavailable or in offline mode."""
    p_name = analysis.project_name or "Target System"
    summary = analysis.executive_summary or f"Operational specification for {p_name}."

    # Identify if financial, write, or high-risk rules exist
    has_financial = any(
        "$" in (r.description or "") or "payment" in (r.description or "").lower() or "invoice" in (r.description or "").lower()
        for r in analysis.business_rules + analysis.functional_requirements
    )

    questions = [
        WizardQuestion(
            question_id="Q-GOAL",
            category="goal",
            prompt=f"What is the primary operational scope for {p_name}?",
            why_it_matters="Defines the core capability and bounded responsibilities of the generated implementation.",
            options=[
                WizardOption(
                    option_id="opt_goal_query",
                    text="Automated Informational Assistant & Query Answering",
                    impact_summary="Implements read-only retrieval pipeline with low operational risk.",
                ),
                WizardOption(
                    option_id="opt_goal_transaction",
                    text="Multi-Step Business Transaction Processing & Verification",
                    impact_summary="Requires transactional state management, input validation, and audit tracking.",
                ),
                WizardOption(
                    option_id="opt_goal_investigation",
                    text="Autonomous Case Investigation Across Disparate Data Sources",
                    impact_summary="Justifies dynamic planning agent with tool-calling capabilities.",
                ),
            ],
            allow_custom=True,
        ),
        WizardQuestion(
            question_id="Q-AUTONOMY",
            category="autonomy",
            prompt="What level of operational autonomy is permitted for actions and decisions?",
            why_it_matters="Determines whether execution is advisory, human-gated, or autonomous.",
            options=[
                WizardOption(
                    option_id="opt_auto_suggest",
                    text="Advisory Only (Suggest actions, zero autonomous execution)",
                    impact_summary="Keeps system strictly non-agentic or advisory with no mutation capabilities.",
                ),
                WizardOption(
                    option_id="opt_auto_approval",
                    text="Human Approval Required for Sensitive Actions (Refunds, Writes, External Calls)",
                    impact_summary="Enforces mandatory operator approval checkpoints before executing state mutations.",
                ),
                WizardOption(
                    option_id="opt_auto_low_risk",
                    text="Autonomous Execution for Approved Low-Risk Operations",
                    impact_summary="Permits bounded automated actions within pre-defined security thresholds.",
                ),
            ],
            allow_custom=True,
        ),
        WizardQuestion(
            question_id="Q-CONNECTORS",
            category="connectors",
            prompt="Which interface protocols will the system use to connect to external services?",
            why_it_matters="Dictates connector schemas, client libraries, and permission guardrails in generated code.",
            options=[
                WizardOption(
                    option_id="opt_conn_rest",
                    text="Standard REST APIs & Webhooks",
                    impact_summary="Generates HTTP client wrappers with retry and timeout policies.",
                ),
                WizardOption(
                    option_id="opt_conn_mcp",
                    text="Model Context Protocol (MCP) Server Integration",
                    impact_summary="Generates MCP client stubs with schema discovery and tool allowlists.",
                ),
                WizardOption(
                    option_id="opt_conn_db",
                    text="Direct Database Access (SQL / ORM)",
                    impact_summary="Generates scoped query adapters with read-only least-privilege defaults.",
                ),
            ],
            allow_custom=True,
        ),
        WizardQuestion(
            question_id="Q-DATA-MODE",
            category="data_mode",
            prompt="What data environment is authorized for demonstration and testing?",
            why_it_matters="Sets privacy boundaries and whether mock connectors or real credentials are used.",
            options=[
                WizardOption(
                    option_id="opt_data_synthetic",
                    text="Isolated Synthetic Test Data & Mock Tools",
                    impact_summary="Guarantees safe, repeatable demo execution without real credentials.",
                ),
                WizardOption(
                    option_id="opt_data_anonymized",
                    text="Sanitized Anonymized Data Set",
                    impact_summary="Allows realistic evaluation while preserving sensitive data privacy.",
                ),
                WizardOption(
                    option_id="opt_data_live",
                    text="Approved Development/Staging Integration Environment",
                    impact_summary="Tests against actual non-production staging endpoints with sandboxed access.",
                ),
            ],
            allow_custom=True,
        ),
    ]

    return WizardQuestionnaire(
        project_name=p_name,
        summary_context=summary[:300],
        questions=questions,
    )


class AdaptiveRequirementWizard:
    """Orchestrates generation of context-aware adaptive clarification questionnaires."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.llm_client = llm_client or get_llm_client(self.settings)

    def validate_inputs(self, analysis: RequirementAnalysisResult) -> None:
        """Validate input payload before processing."""
        if analysis is None:
            raise ValueError("Requirement analysis result must be provided.")
        if not analysis.project_name or not analysis.project_name.strip():
            raise ValueError("Project name must not be empty.")

    def _verify_and_sanitize_questionnaire(
        self,
        questionnaire: WizardQuestionnaire,
        analysis: RequirementAnalysisResult,
    ) -> WizardQuestionnaire:
        """Ensure questionnaire has between 3 and 5 valid, non-redundant questions."""
        valid_questions: list[WizardQuestion] = []
        seen_categories: set[str] = set()

        for q in questionnaire.questions:
            # Ensure question has valid prompt and why_it_matters
            if not q.prompt or not q.prompt.strip():
                continue
            if not q.why_it_matters or not q.why_it_matters.strip():
                q.why_it_matters = "Materially impacts system architecture and operational boundaries."

            # Ensure question has at least 2 valid options
            valid_opts = [opt for opt in q.options if opt.text and opt.text.strip()]
            if len(valid_opts) < 2:
                continue
            q.options = valid_opts
            q.allow_custom = True

            # Deduplicate by category if duplicated
            if q.category in seen_categories:
                continue
            seen_categories.add(q.category)
            valid_questions.append(q)

        # Fallback if LLM generated fewer than 3 valid questions
        if len(valid_questions) < 3:
            logger.warning(
                "LLM generated only %d valid wizard questions for %s; supplementing with deterministic template.",
                len(valid_questions),
                analysis.project_name,
            )
            fallback = _build_fallback_questionnaire(analysis)
            for fq in fallback.questions:
                if fq.category not in seen_categories and len(valid_questions) < 5:
                    valid_questions.append(fq)
                    seen_categories.add(fq.category)

        # Clamp between 3 and 5 questions
        clamped_questions = valid_questions[:5]
        if len(clamped_questions) < 3:
            clamped_questions = _build_fallback_questionnaire(analysis).questions[:4]

        # Ensure project name and summary context are synchronized
        target_name = analysis.project_name or questionnaire.project_name or "Target System"
        target_summary = analysis.executive_summary or questionnaire.summary_context or "Project operational specification."

        return WizardQuestionnaire(
            project_name=target_name,
            summary_context=target_summary[:300],
            questions=clamped_questions,
        )

    async def generate_questions(
        self,
        analysis: RequirementAnalysisResult,
    ) -> WizardQuestionnaire:
        """Generate 3 to 5 adaptive clarification questions based on specification analysis."""
        self.validate_inputs(analysis)

        prompt = build_adaptive_wizard_prompt(analysis)

        try:
            raw_result = await self.llm_client.generate_structured(
                prompt=prompt,
                schema=WizardQuestionnaire,
                system_instruction=ADAPTIVE_WIZARD_SYSTEM_PROMPT,
                temperature=self.settings.llm_temperature,
            )
            return self._verify_and_sanitize_questionnaire(raw_result, analysis)
        except (LLMTimeoutError, LLMError) as exc:
            logger.warning(
                "LLM call during adaptive wizard generation encountered error (%s). Using deterministic template.",
                exc,
            )
            return _build_fallback_questionnaire(analysis)
        except Exception as exc:
            logger.error("Unexpected error in AdaptiveRequirementWizard: %s", exc)
            return _build_fallback_questionnaire(analysis)

    generate_questionnaire = generate_questions


async def generate_adaptive_questionnaire(
    analysis: RequirementAnalysisResult,
    llm_client: LLMClient | None = None,
    settings: Settings | None = None,
) -> WizardQuestionnaire:
    """Convenience helper to generate adaptive wizard questions."""
    wizard = AdaptiveRequirementWizard(llm_client=llm_client, settings=settings)
    return await wizard.generate_questions(analysis=analysis)
