"""Unit tests for Module H: Explainable System Verdict Engine.

Tests deterministic heuristics, LLM-guided verdicts, human approval bounds, and multi-criteria explainability.
"""

import pytest
from backend.app.ai.verdict_engine import SystemVerdictEngine, generate_system_verdict
from backend.app.core.config import Settings
from backend.app.integrations.llm_client import MockLLMClient, LLMTimeoutError
from backend.app.schemas.analysis import (
    RequirementAnalysisResult,
    FunctionalRequirement,
    BusinessRule,
)
from backend.app.schemas.classification import (
    TaskClassificationResult,
    TaskClassification,
)
from backend.app.schemas.common import EvidenceReference, TaskCategory
from backend.app.schemas.verdict import SystemVerdictResult, SystemVerdictType
from backend.app.schemas.wizard import ConfirmedProjectSpec


@pytest.mark.asyncio
async def test_verdict_engine_llm_hybrid(
    mock_llm_client: MockLLMClient,
    sample_analysis_result: RequirementAnalysisResult,
    sample_classification_result: TaskClassificationResult,
    sample_confirmed_project_spec: ConfirmedProjectSpec,
    test_settings: Settings,
):
    engine = SystemVerdictEngine(llm_client=mock_llm_client, settings=test_settings)
    verdict = await engine.generate_verdict(
        analysis=sample_analysis_result,
        classification=sample_classification_result,
        confirmed_spec=sample_confirmed_project_spec,
    )

    assert isinstance(verdict, SystemVerdictResult)
    assert verdict.overall_verdict in (
        SystemVerdictType.NON_AGENTIC,
        SystemVerdictType.AGENTIC,
        SystemVerdictType.HYBRID,
    )
    assert 0.0 <= verdict.confidence_score <= 1.0
    assert len(verdict.reasoning) > 20
    assert len(verdict.autonomy_boundary) > 10
    assert len(verdict.key_risks) >= 1
    assert len(verdict.assumptions) >= 1
    assert len(verdict.limitations) >= 1
    assert len(verdict.recommended_next_step) > 10
    assert len(verdict.supporting_evidence) >= 1


@pytest.mark.asyncio
async def test_verdict_engine_deterministic_fallback_non_agentic(
    sample_analysis_result: RequirementAnalysisResult,
    sample_evidence: EvidenceReference,
    test_settings: Settings,
):
    # Setup pure deterministic classification
    det_classification = TaskClassificationResult(
        classifications=[
            TaskClassification(
                task_id="TASK-01",
                task_name="Standard SQL Database Query",
                category=TaskCategory.DETERMINISTIC,
                reasoning="Exact key lookup in database.",
                supporting_evidence=[sample_evidence],
                human_approval_required=False,
            ),
            TaskClassification(
                task_id="TASK-02",
                task_name="Generate Invoice PDF",
                category=TaskCategory.DETERMINISTIC,
                reasoning="Deterministic templating engine.",
                supporting_evidence=[sample_evidence],
                human_approval_required=False,
            ),
        ],
        summary_counts={"deterministic": 2, "ai_assisted": 0, "agentic": 0},
    )

    # Failing client triggers deterministic heuristic
    failing_client = MockLLMClient()
    failing_client.simulate_timeout(True)

    engine = SystemVerdictEngine(llm_client=failing_client, settings=test_settings)
    verdict = await engine.generate_verdict(
        analysis=sample_analysis_result,
        classification=det_classification,
    )

    assert isinstance(verdict, SystemVerdictResult)
    assert verdict.overall_verdict == SystemVerdictType.NON_AGENTIC
    assert verdict.deterministic_task_count == 2
    assert verdict.agentic_task_count == 0


@pytest.mark.asyncio
async def test_verdict_engine_deterministic_fallback_agentic(
    sample_analysis_result: RequirementAnalysisResult,
    sample_evidence: EvidenceReference,
    test_settings: Settings,
):
    # Setup classification with high agentic tasks and low deterministic
    agentic_classification = TaskClassificationResult(
        classifications=[
            TaskClassification(
                task_id="TASK-01",
                task_name="Autonomous Negotiation Agent",
                category=TaskCategory.AGENTIC,
                reasoning="Autonomous decision making with multi-turn tool interaction.",
                supporting_evidence=[sample_evidence],
                human_approval_required=False,
            ),
            TaskClassification(
                task_id="TASK-02",
                task_name="Self-Directed Vendor Research",
                category=TaskCategory.AGENTIC,
                reasoning="Agent plans and executes web queries autonomously.",
                supporting_evidence=[sample_evidence],
                human_approval_required=False,
            ),
        ],
        summary_counts={"deterministic": 0, "ai_assisted": 0, "agentic": 2},
    )

    failing_client = MockLLMClient()
    failing_client.simulate_timeout(True)

    engine = SystemVerdictEngine(llm_client=failing_client, settings=test_settings)
    verdict = await engine.generate_verdict(
        analysis=sample_analysis_result,
        classification=agentic_classification,
    )

    assert isinstance(verdict, SystemVerdictResult)
    assert verdict.overall_verdict == SystemVerdictType.AGENTIC
    assert verdict.agentic_task_count == 2


@pytest.mark.asyncio
async def test_verdict_engine_deterministic_fallback_hybrid_with_human_approval(
    sample_evidence: EvidenceReference,
    test_settings: Settings,
):
    # Analysis with high-value approval rule
    analysis = RequirementAnalysisResult(
        project_name="FinDoc Reconciliation",
        executive_summary="Invoice matching with finance manager approvals.",
        modules=[],
        workflows=[],
        business_rules=[
            BusinessRule(
                rule_id="BR-01",
                description="Any invoice payment over $10,000 strictly requires manager sign-off.",
                evidence=[sample_evidence],
            )
        ],
        functional_requirements=[
            FunctionalRequirement(
                req_id="REQ-01",
                title="Auto-reconcile low value invoices",
                description="Deterministic lookup",
                evidence=[sample_evidence],
            )
        ],
    )

    classification = TaskClassificationResult(
        classifications=[
            TaskClassification(
                task_id="TASK-01",
                task_name="Match Invoices",
                category=TaskCategory.DETERMINISTIC,
                reasoning="Rule matching",
                supporting_evidence=[sample_evidence],
            ),
            TaskClassification(
                task_id="TASK-02",
                task_name="Investigate Discrepancy",
                category=TaskCategory.AGENTIC,
                reasoning="Agentic email search",
                supporting_evidence=[sample_evidence],
                human_approval_required=True,
            ),
        ],
        summary_counts={"deterministic": 1, "ai_assisted": 0, "agentic": 1},
    )

    failing_client = MockLLMClient()
    failing_client.simulate_timeout(True)

    engine = SystemVerdictEngine(llm_client=failing_client, settings=test_settings)
    verdict = await engine.generate_verdict(
        analysis=analysis,
        classification=classification,
    )

    assert isinstance(verdict, SystemVerdictResult)
    assert verdict.overall_verdict == SystemVerdictType.HYBRID
    # Autonomy boundary must highlight human sign-off
    assert "approval" in verdict.autonomy_boundary.lower() or "human" in verdict.autonomy_boundary.lower()


@pytest.mark.asyncio
async def test_verdict_engine_invalid_inputs(
    sample_analysis_result: RequirementAnalysisResult,
    sample_classification_result: TaskClassificationResult,
    test_settings: Settings,
):
    engine = SystemVerdictEngine(settings=test_settings)

    with pytest.raises(ValueError):
        await engine.generate_verdict(None, sample_classification_result)  # type: ignore

    with pytest.raises(ValueError):
        await engine.generate_verdict(sample_analysis_result, None)  # type: ignore


@pytest.mark.asyncio
async def test_generate_system_verdict_convenience_fn(
    mock_llm_client: MockLLMClient,
    sample_analysis_result: RequirementAnalysisResult,
    sample_classification_result: TaskClassificationResult,
):
    verdict = await generate_system_verdict(
        analysis=sample_analysis_result,
        classification=sample_classification_result,
        llm_client=mock_llm_client,
    )
    assert isinstance(verdict, SystemVerdictResult)
    assert verdict.overall_verdict in (
        SystemVerdictType.NON_AGENTIC,
        SystemVerdictType.AGENTIC,
        SystemVerdictType.HYBRID,
    )
