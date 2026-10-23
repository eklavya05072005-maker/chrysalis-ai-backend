"""Unit tests for Module B: Task Classification Engine.

All tests run offline using MockLLMClient and fixtures without external API calls.
"""

import pytest
from backend.app.ai.classifier import TaskClassifier, classify_tasks
from backend.app.core.config import Settings
from backend.app.integrations.llm_client import (
    LLMAuthenticationError,
    LLMMalformedJSONError,
    LLMTimeoutError,
    MockLLMClient,
)
from backend.app.schemas import (
    EvidenceReference,
    RequirementAnalysisResult,
    TaskCategory,
    TaskClassification,
    TaskClassificationResult,
)


@pytest.mark.asyncio
async def test_classify_tasks_all_three_categories(
    mock_llm_client: MockLLMClient,
    sample_analysis_result: RequirementAnalysisResult,
    sample_spec_text: str,
    test_settings: Settings,
):
    classifier = TaskClassifier(llm_client=mock_llm_client, settings=test_settings)
    result = await classifier.classify(sample_analysis_result, spec_text=sample_spec_text)

    assert isinstance(result, TaskClassificationResult)
    assert len(result.classifications) == 3

    categories = [c.category for c in result.classifications]
    assert TaskCategory.DETERMINISTIC in categories
    assert TaskCategory.AI_ASSISTED in categories
    assert TaskCategory.AGENTIC in categories

    assert result.summary_counts.get("deterministic") == 1
    assert result.summary_counts.get("ai_assisted") == 1
    assert result.summary_counts.get("agentic") == 1

    # Verify that human approval flag is true for sensitive actions
    det_task = next(c for c in result.classifications if c.category == TaskCategory.DETERMINISTIC)
    assert det_task.human_approval_required is True


@pytest.mark.asyncio
async def test_classify_empty_analysis(
    mock_llm_client: MockLLMClient,
    test_settings: Settings,
):
    classifier = TaskClassifier(llm_client=mock_llm_client, settings=test_settings)
    empty_analysis = RequirementAnalysisResult(
        project_name="Empty Project",
        executive_summary="No content.",
        modules=[],
        workflows=[],
        business_rules=[],
        functional_requirements=[],
        non_functional_requirements=[],
        risks_and_ambiguities=[],
        evidence_references=[],
    )

    result = await classifier.classify(empty_analysis)
    assert isinstance(result, TaskClassificationResult)
    assert len(result.classifications) == 0
    assert result.summary_counts.get("deterministic") == 0
    assert result.summary_counts.get("ai_assisted") == 0
    assert result.summary_counts.get("agentic") == 0


@pytest.mark.asyncio
async def test_classify_none_input_raises_value_error(
    mock_llm_client: MockLLMClient,
    test_settings: Settings,
):
    classifier = TaskClassifier(llm_client=mock_llm_client, settings=test_settings)
    with pytest.raises(ValueError) as exc:
        await classifier.classify(None)  # type: ignore
    assert "Requirement analysis result must be provided" in str(exc.value)


def test_confidence_boundary_clamping(test_settings: Settings):
    classifier = TaskClassifier(llm_client=MockLLMClient(), settings=test_settings)

    # 1. Pydantic schema validation should directly reject out-of-bound values on standard instantiation
    with pytest.raises(Exception):
        TaskClassification(
            task_id="TASK-OVER",
            task_name="Overconfident",
            category=TaskCategory.DETERMINISTIC,
            reasoning="Reasoning text long enough",
            confidence=1.5,
        )

    # 2. Sanitizer handles and clamps out-of-bound values if passed via model_construct or external dict
    raw_result = TaskClassificationResult(
        classifications=[
            TaskClassification.model_construct(
                task_id="TASK-OVER",
                task_name="Overconfident",
                category=TaskCategory.DETERMINISTIC,
                reasoning="Reasoning text long enough",
                confidence=1.5,  # Exceeds 1.0
            ),
            TaskClassification.model_construct(
                task_id="TASK-UNDER",
                task_name="Underconfident",
                category=TaskCategory.AI_ASSISTED,
                reasoning="Reasoning text long enough",
                confidence=-0.4,  # Below 0.0
            ),
        ],
        summary_counts={},
    )

    sanitized = classifier._sanitize_and_verify_classifications(raw_result)
    assert sanitized.classifications[0].confidence == 1.0
    assert sanitized.classifications[1].confidence == 0.0
    assert sanitized.summary_counts.get("deterministic") == 1
    assert sanitized.summary_counts.get("ai_assisted") == 1


@pytest.mark.asyncio
async def test_classify_malformed_llm_json_propagated(
    sample_analysis_result: RequirementAnalysisResult,
    sample_spec_text: str,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_malformed_json(True)

    classifier = TaskClassifier(llm_client=mock_client, settings=test_settings)

    with pytest.raises(LLMMalformedJSONError):
        await classifier.classify(sample_analysis_result, spec_text=sample_spec_text)


@pytest.mark.asyncio
async def test_classify_timeout_propagated(
    sample_analysis_result: RequirementAnalysisResult,
    sample_spec_text: str,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_timeout(True)

    classifier = TaskClassifier(llm_client=mock_client, settings=test_settings)

    with pytest.raises(LLMTimeoutError):
        await classifier.classify(sample_analysis_result, spec_text=sample_spec_text)


@pytest.mark.asyncio
async def test_classify_provider_error_propagated(
    sample_analysis_result: RequirementAnalysisResult,
    sample_spec_text: str,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_auth_failure(True)

    classifier = TaskClassifier(llm_client=mock_client, settings=test_settings)

    with pytest.raises(LLMAuthenticationError):
        await classifier.classify(sample_analysis_result, spec_text=sample_spec_text)


def test_classify_evidence_grounding_verification(
    test_settings: Settings,
    sample_evidence: EvidenceReference,
):
    classifier = TaskClassifier(llm_client=MockLLMClient(), settings=test_settings)

    # Valid grounded evidence and ungrounded evidence
    grounded_ref = sample_evidence
    ungrounded_ref = EvidenceReference(
        source_doc="fake.pdf",
        exact_quote="This quote does not exist anywhere in the spec text.",
        relevance="Fabricated test",
    )

    raw_result = TaskClassificationResult(
        classifications=[
            TaskClassification(
                task_id="TASK-01",
                task_name="Grounded Task",
                category=TaskCategory.DETERMINISTIC,
                reasoning="Reasoning text long enough",
                supporting_evidence=[grounded_ref, ungrounded_ref],
                confidence=0.9,
            )
        ],
        summary_counts={},
    )

    # Should execute and log warning for ungrounded without crashing
    sanitized = classifier._sanitize_and_verify_classifications(
        raw_result,
        spec_text="Any invoice exceeding $10,000 must strictly require a senior finance manager approval before payment scheduling.",
    )
    assert len(sanitized.classifications) == 1
    assert sanitized.summary_counts.get("deterministic") == 1


def test_extract_tasks_from_analysis(
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    classifier = TaskClassifier(llm_client=MockLLMClient(), settings=test_settings)
    tasks = classifier.extract_tasks_from_analysis(sample_analysis_result)

    assert len(tasks) >= 3  # 1 functional req + 1 business rule + 1 workflow
    task_types = [t["source_type"] for t in tasks]
    assert "functional_requirement" in task_types
    assert "business_rule" in task_types
    assert "workflow" in task_types


@pytest.mark.asyncio
async def test_convenience_function_classify_tasks(
    mock_llm_client: MockLLMClient,
    sample_analysis_result: RequirementAnalysisResult,
    sample_spec_text: str,
):
    result = await classify_tasks(
        analysis=sample_analysis_result,
        llm_client=mock_llm_client,
        spec_text=sample_spec_text,
    )
    assert isinstance(result, TaskClassificationResult)
    assert len(result.classifications) == 3
