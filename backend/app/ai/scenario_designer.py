"""Module E: Scenario Design Engine for Chrysalis AI.

Generates standardized, rigorous benchmark scenarios covering normal workflows,
edge cases, external tool failures, low confidence, and human approval points
to evaluate architecture candidates fairly.
"""

from __future__ import annotations
import logging
from typing import Any
from backend.app.ai.prompts import (
    SCENARIO_DESIGN_SYSTEM_PROMPT,
    build_scenario_design_prompt,
)
from backend.app.core.config import Settings, get_settings
from backend.app.integrations.llm_client import (
    LLMClient,
    LLMError,
    LLMTimeoutError,
    get_llm_client,
)
from backend.app.schemas.analysis import RequirementAnalysisResult
from backend.app.schemas.architecture import ArchitectureCandidatesResult
from backend.app.schemas.classification import TaskClassificationResult
from backend.app.schemas.scenario import ScenarioCase, ScenarioDesignResult

logger = logging.getLogger(__name__)

CANONICAL_SCENARIO_CATEGORIES: list[str] = [
    "normal_workflow",
    "invalid_input",
    "missing_information",
    "external_tool_failure",
    "low_confidence_ai",
    "sensitive_human_approval",
]


def _build_fallback_scenario(
    case_type: str,
    scenario_idx: int,
    project_name: str,
    analysis: RequirementAnalysisResult,
) -> ScenarioCase:
    """Construct a synthesized fallback scenario when an LLM omits a canonical category."""
    req_title = (
        analysis.functional_requirements[0].title
        if analysis.functional_requirements
        else "Core Transaction Processing"
    )
    rule_desc = (
        analysis.business_rules[0].description
        if analysis.business_rules
        else "System must enforce state validation rules"
    )

    templates: dict[str, dict[str, Any]] = {
        "normal_workflow": {
            "title": f"Happy-Path End-to-End Processing: {req_title}",
            "description": (
                f"Evaluates how each architecture candidate executes standard valid transactions "
                f"for '{project_name}'. Assesses throughput, latency, and component interactions."
            ),
            "sample_input": {
                "transaction_id": "TX-NORM-1001",
                "document_type": "standard_invoice",
                "status": "valid",
                "amount": 450.00,
            },
            "expected_behavior": (
                "Candidate completes end-to-end ingestion, validation, and persistence without errors. "
                "Emits audit log and returns deterministic status response."
            ),
            "evaluation_criteria": [
                "Transaction processed within expected p95 latency window",
                "All transactional records committed to database with ACID compliance",
            ],
            "failure_conditions": [
                "Unhandled exception or crash",
                "Transaction dropped without error response or audit log",
            ],
        },
        "invalid_input": {
            "title": "Malformed Payload & Schema Violation Handling",
            "description": (
                "Tests architecture resilience when supplied with corrupted payload structures, "
                "invalid data types, and non-conforming inputs."
            ),
            "sample_input": {
                "corrupted_bytes": "0xFFFE_INVALID_BUFFER",
                "amount": "NOT_A_NUMBER",
                "metadata": None,
            },
            "expected_behavior": (
                "API gateway or ingestion component rejects request with 4xx client error, "
                "descriptive validation message, and zero corruption of backend data stores."
            ),
            "evaluation_criteria": [
                "Graceful rejection with informative error code and message",
                "Zero unhandled server 500 crashes or pipeline hangs",
            ],
            "failure_conditions": [
                "Internal server error (500) or unhandled stack trace",
                "Corrupted data persisted into database",
            ],
        },
        "missing_information": {
            "title": "Incomplete Payload & Partial Document Extraction",
            "description": (
                "Evaluates system behavior when required fields or document segments are missing, "
                "triggering extraction fallbacks or clarification requests."
            ),
            "sample_input": {
                "transaction_id": "TX-MISS-2002",
                "invoice_number": None,
                "amount": 890.00,
                "line_items": [],
            },
            "expected_behavior": (
                "System detects missing mandatory fields, halts premature settlement, and queues "
                "item for clarification or manual review according to business policy."
            ),
            "evaluation_criteria": [
                "Missing mandatory fields identified and flagged accurately",
                "Execution paused before irreversible mutations occur",
            ],
            "failure_conditions": [
                "Silent default assumption of missing critical financial fields",
                "Pipeline crash due to null pointer or KeyError",
            ],
        },
        "external_tool_failure": {
            "title": "Downstream Service Timeout & Circuit-Breaker Resilience",
            "description": (
                "Simulates complete network partition or persistent 503 error on external dependencies "
                "(e.g. OCR API, vendor database, or message broker)."
            ),
            "sample_input": {
                "simulated_network_error": "ETIMEDOUT",
                "dependency": "external_ocr_service",
                "retry_count_exceeded": True,
            },
            "expected_behavior": (
                "Architecture handles failure via dead-letter queue, retry backoff with circuit breaker, "
                "and informative degraded-service response to the caller."
            ),
            "evaluation_criteria": [
                "Circuit breaker activates without exhausting connection pool",
                "Failed jobs routed to persistent dead-letter queue for recovery",
            ],
            "failure_conditions": [
                "Thread starvation, infinite retry loops, or total system outage",
                "Loss of in-flight transaction payload during outage",
            ],
        },
        "low_confidence_ai": {
            "title": "Probabilistic OCR Ambiguity & Low-Confidence Resolution",
            "description": (
                "Tests how architectures handle ambiguous OCR scans, conflicting multi-turn classifications, "
                "or model confidence scores falling below acceptable operational thresholds."
            ),
            "sample_input": {
                "ocr_confidence_score": 0.42,
                "confidence_threshold": 0.85,
                "extracted_fields": {"vendor_name": "Acme? Corp?", "amount": "1?00.00"},
            },
            "expected_behavior": (
                "Low confidence detection intercepts automated decision; request is quarantined "
                "and routed to an exception review queue for human operator disambiguation."
            ),
            "evaluation_criteria": [
                "Automated progression prevented when confidence is below threshold",
                "Audit record logs low-confidence extraction flags",
            ],
            "failure_conditions": [
                "System blindly acts on ungrounded or ambiguous low-confidence data",
                "Uncaught model hallucination accepted as verified truth",
            ],
        },
        "sensitive_human_approval": {
            "title": f"Mandatory Human Oversight Gate: {rule_desc[:50]}",
            "description": (
                f"Tests strict enforcement of human oversight on sensitive, high-impact transactions. "
                f"Directly derived from business rule: '{rule_desc}'."
            ),
            "sample_input": {
                "transaction_id": "TX-SENS-5005",
                "amount": 25000.00,
                "approval_required": True,
                "approver_role": "senior_finance_manager",
            },
            "expected_behavior": (
                "System pauses automated execution, registers pending approval state, notifies "
                "authorized human supervisor, and resumes only upon cryptographic approval signature."
            ),
            "evaluation_criteria": [
                "Zero automated settlement without verified human approval",
                "Comprehensive audit trail tracking approver ID, timestamp, and decision",
            ],
            "failure_conditions": [
                "Bypass of human approval gate due to automation override",
                "Irreversible action executed before approval token is granted",
            ],
        },
    }

    spec = templates.get(case_type, templates["normal_workflow"])
    return ScenarioCase(
        scenario_id=f"SCEN-{scenario_idx:02d}",
        case_type=case_type,  # type: ignore
        title=spec["title"],
        description=spec["description"],
        sample_input=spec["sample_input"],
        expected_behavior=spec["expected_behavior"],
        evaluation_criteria=spec["evaluation_criteria"],
        failure_conditions=spec["failure_conditions"],
    )


class ScenarioDesignEngine:
    """Orchestrates generation and validation of standard benchmark test scenarios."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.llm_client = llm_client or get_llm_client(self.settings)

    def validate_inputs(self, analysis: RequirementAnalysisResult) -> None:
        """Verify requirement analysis is provided and non-empty."""
        if analysis is None:
            raise ValueError("Requirement analysis must be provided.")
        if not analysis.functional_requirements and not analysis.business_rules:
            raise ValueError(
                "Requirement analysis must contain functional requirements or business rules to design scenarios."
            )

    def _verify_and_sanitize_scenarios(
        self,
        result: ScenarioDesignResult,
        analysis: RequirementAnalysisResult,
    ) -> ScenarioDesignResult:
        """Enforce coverage of all 6 canonical categories, deduplicate IDs, and validate criteria."""
        if not result.scenarios:
            raise LLMError("Scenario design generated an empty scenario list.")

        sanitized_scenarios: list[ScenarioCase] = []
        seen_ids: set[str] = set()
        seen_titles: set[str] = set()

        for idx, scen in enumerate(result.scenarios, start=1):
            # 1. Normalize and deduplicate ID
            scen_id = scen.scenario_id.strip() if scen.scenario_id else f"SCEN-{idx:02d}"
            if scen_id in seen_ids or not scen_id.startswith("SCEN-"):
                scen_id = f"SCEN-{idx:02d}"
            seen_ids.add(scen_id)
            scen.scenario_id = scen_id

            # 2. Check duplicate titles
            clean_title = scen.title.strip()
            if clean_title in seen_titles:
                clean_title = f"{clean_title} (Variant {idx})"
            seen_titles.add(clean_title)
            scen.title = clean_title

            # 3. Validate case_type
            if scen.case_type not in CANONICAL_SCENARIO_CATEGORIES:
                scen.case_type = "normal_workflow"

            # 4. Ensure non-empty evaluation criteria and failure conditions
            if not scen.evaluation_criteria:
                scen.evaluation_criteria = ["Verify expected behavior and valid state transition"]
            if not scen.failure_conditions:
                scen.failure_conditions = ["Unhandled exception, data corruption, or timeout"]

            # 5. Ensure sample_input is a dictionary
            if not isinstance(scen.sample_input, dict):
                scen.sample_input = {"raw_payload": str(scen.sample_input)}

            sanitized_scenarios.append(scen)

        # 6. Ensure all 6 canonical categories are represented
        present_categories = {s.case_type for s in sanitized_scenarios}
        next_idx = len(sanitized_scenarios) + 1

        for cat in CANONICAL_SCENARIO_CATEGORIES:
            if cat not in present_categories:
                fallback_scen = _build_fallback_scenario(
                    case_type=cat,
                    scenario_idx=next_idx,
                    project_name=result.project_name or analysis.project_name,
                    analysis=analysis,
                )
                sanitized_scenarios.append(fallback_scen)
                next_idx += 1

        result.scenarios = sanitized_scenarios

        if not result.benchmarking_guide:
            result.benchmarking_guide = (
                "Benchmark Guide: Member 2 simulation engine should execute each candidate architecture "
                "against these standardized scenarios. Compare candidate responses on pass/fail completion, "
                "latency distribution, and human-in-the-loop escalation accuracy."
            )

        return result

    async def design_scenarios(
        self,
        analysis: RequirementAnalysisResult,
        candidates_result: ArchitectureCandidatesResult | None = None,
        classification: TaskClassificationResult | None = None,
        spec_text: str | None = None,
    ) -> ScenarioDesignResult:
        """Design standardized benchmark scenarios for comparing architecture candidates."""
        self.validate_inputs(analysis)

        prompt = build_scenario_design_prompt(
            analysis=analysis,
            candidates_result=candidates_result,
            classification=classification,
            spec_text=spec_text,
        )

        try:
            raw_result = await self.llm_client.generate_structured(
                prompt=prompt,
                schema=ScenarioDesignResult,
                system_instruction=SCENARIO_DESIGN_SYSTEM_PROMPT,
                temperature=self.settings.llm_temperature,
            )
        except LLMTimeoutError as exc:
            logger.error("LLM timeout during scenario design: %s", exc)
            raise
        except LLMError as exc:
            logger.error("LLM error during scenario design: %s", exc)
            raise
        except Exception as exc:
            logger.error("Unexpected error in ScenarioDesignEngine: %s", exc)
            raise LLMError(f"Unexpected error during scenario design: {exc}") from exc

        return self._verify_and_sanitize_scenarios(raw_result, analysis)


async def design_benchmark_scenarios(
    analysis: RequirementAnalysisResult,
    candidates_result: ArchitectureCandidatesResult | None = None,
    classification: TaskClassificationResult | None = None,
    spec_text: str | None = None,
    llm_client: LLMClient | None = None,
    settings: Settings | None = None,
) -> ScenarioDesignResult:
    """Convenience helper for backend simulation service to design benchmark scenarios."""
    engine = ScenarioDesignEngine(llm_client=llm_client, settings=settings)
    return await engine.design_scenarios(
        analysis=analysis,
        candidates_result=candidates_result,
        classification=classification,
        spec_text=spec_text,
    )
