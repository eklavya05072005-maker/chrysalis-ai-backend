"""Unit tests for Module C: Architecture Search Engine.

All tests run offline using MockLLMClient and fixtures without external API calls.
"""

import pytest
from backend.app.ai.architecture_generator import (
    ArchitectureSearchEngine,
    generate_architecture_candidates,
)
from backend.app.core.config import Settings
from backend.app.integrations.llm_client import (
    LLMAuthenticationError,
    LLMError,
    LLMMalformedJSONError,
    LLMTimeoutError,
    MockLLMClient,
)
from backend.app.schemas import (
    ArchitectureArchetype,
    ArchitectureCandidate,
    ArchitectureCandidatesResult,
    RequirementAnalysisResult,
    TaskClassificationResult,
)


@pytest.mark.asyncio
async def test_generate_three_distinct_candidates(
    mock_llm_client: MockLLMClient,
    sample_analysis_result: RequirementAnalysisResult,
    sample_classification_result: TaskClassificationResult,
    sample_spec_text: str,
    test_settings: Settings,
):
    engine = ArchitectureSearchEngine(llm_client=mock_llm_client, settings=test_settings)
    result = await engine.generate_candidates(
        analysis=sample_analysis_result,
        classification=sample_classification_result,
        spec_text=sample_spec_text,
    )

    assert isinstance(result, ArchitectureCandidatesResult)
    assert len(result.candidates) == 3

    # Verify that all 3 distinct archetypes are present
    archetypes = {c.archetype for c in result.candidates}
    assert ArchitectureArchetype.CONSERVATIVE in archetypes
    assert ArchitectureArchetype.HYBRID_AGENTIC in archetypes
    assert ArchitectureArchetype.AUTOMATION_HEAVY in archetypes

    # Find each candidate
    conservative = next(c for c in result.candidates if c.archetype == ArchitectureArchetype.CONSERVATIVE)
    hybrid = next(c for c in result.candidates if c.archetype == ArchitectureArchetype.HYBRID_AGENTIC)
    automation = next(c for c in result.candidates if c.archetype == ArchitectureArchetype.AUTOMATION_HEAVY)

    # Verify meaningful differences in complexity score
    assert conservative.complexity_score < hybrid.complexity_score < automation.complexity_score

    # Verify components and approval points exist for all
    for cand in result.candidates:
        assert len(cand.components) >= 2
        assert len(cand.connections) >= 1
        assert len(cand.data_flows) >= 1
        assert len(cand.advantages) >= 1
        assert len(cand.disadvantages) >= 1
        assert len(cand.risks) >= 1
        assert len(cand.human_approval_points) >= 1
        assert "$" in cand.estimated_cost
        assert "ms" in cand.estimated_latency


@pytest.mark.asyncio
async def test_generate_empty_analysis_raises_value_error(
    mock_llm_client: MockLLMClient,
    test_settings: Settings,
):
    engine = ArchitectureSearchEngine(llm_client=mock_llm_client, settings=test_settings)

    # Test None
    with pytest.raises(ValueError) as exc1:
        await engine.generate_candidates(None)  # type: ignore
    assert "Requirement analysis must be provided" in str(exc1.value)

    # Test empty requirements
    empty_analysis = RequirementAnalysisResult(
        project_name="Empty",
        executive_summary="Empty",
        modules=[],
        workflows=[],
        business_rules=[],
        functional_requirements=[],
        non_functional_requirements=[],
        risks_and_ambiguities=[],
        evidence_references=[],
    )
    with pytest.raises(ValueError) as exc2:
        await engine.generate_candidates(empty_analysis)
    assert "contains no functional requirements" in str(exc2.value)


def test_candidate_complexity_bounds_clamping(
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    engine = ArchitectureSearchEngine(llm_client=MockLLMClient(), settings=test_settings)

    # Artificially set out-of-bound complexity scores on candidate model constructs
    sample_architecture_candidates_result.candidates[0].complexity_score = 0.5  # Below 1.0
    sample_architecture_candidates_result.candidates[2].complexity_score = 12.0  # Above 10.0

    sanitized = engine._verify_and_sanitize_candidates(
        sample_architecture_candidates_result,
        sample_analysis_result,
    )
    assert sanitized.candidates[0].complexity_score == 1.0
    assert sanitized.candidates[2].complexity_score == 10.0


def test_invalid_candidate_count_raises_error(
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    engine = ArchitectureSearchEngine(llm_client=MockLLMClient(), settings=test_settings)

    # Remove 1 candidate to create an invalid count of 2
    truncated_result = ArchitectureCandidatesResult.model_construct(
        project_name=sample_architecture_candidates_result.project_name,
        candidates=sample_architecture_candidates_result.candidates[:2],
        comparison_summary="Truncated",
    )

    with pytest.raises(LLMError) as exc:
        engine._verify_and_sanitize_candidates(truncated_result, sample_analysis_result)
    assert "must generate exactly 3 candidates" in str(exc.value)


@pytest.mark.asyncio
async def test_malformed_llm_json_propagated(
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_malformed_json(True)

    engine = ArchitectureSearchEngine(llm_client=mock_client, settings=test_settings)
    with pytest.raises(LLMMalformedJSONError):
        await engine.generate_candidates(sample_analysis_result)


@pytest.mark.asyncio
async def test_timeout_propagated(
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_timeout(True)

    engine = ArchitectureSearchEngine(llm_client=mock_client, settings=test_settings)
    with pytest.raises(LLMTimeoutError):
        await engine.generate_candidates(sample_analysis_result)


@pytest.mark.asyncio
async def test_provider_failure_propagated(
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_auth_failure(True)

    engine = ArchitectureSearchEngine(llm_client=mock_client, settings=test_settings)
    with pytest.raises(LLMAuthenticationError):
        await engine.generate_candidates(sample_analysis_result)


@pytest.mark.asyncio
async def test_convenience_function_generate_architecture_candidates(
    mock_llm_client: MockLLMClient,
    sample_analysis_result: RequirementAnalysisResult,
    sample_classification_result: TaskClassificationResult,
    sample_spec_text: str,
):
    result = await generate_architecture_candidates(
        analysis=sample_analysis_result,
        classification=sample_classification_result,
        llm_client=mock_llm_client,
        spec_text=sample_spec_text,
    )
    assert isinstance(result, ArchitectureCandidatesResult)
    assert len(result.candidates) == 3
    assert result.project_name == "FinDoc Invoice Reconciliation System"
