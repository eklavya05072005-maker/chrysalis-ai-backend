"""Unit tests for Module A: Requirement Analyzer.

All tests run offline using MockLLMClient and test fixtures without API keys.
"""

import pytest
from backend.app.ai.analyzer import (
    RequirementAnalyzer,
    analyze_requirements,
    is_quote_grounded,
)
from backend.app.core.config import Settings
from backend.app.integrations.llm_client import (
    LLMAuthenticationError,
    LLMMalformedJSONError,
    LLMTimeoutError,
    MockLLMClient,
)
from backend.app.schemas import (
    AnalyzeRequest,
    EvidenceReference,
    RequirementAnalysisResult,
)


@pytest.mark.asyncio
async def test_analyze_valid_request(
    mock_llm_client: MockLLMClient,
    sample_spec_text: str,
    test_settings: Settings,
):
    analyzer = RequirementAnalyzer(llm_client=mock_llm_client, settings=test_settings)
    request = AnalyzeRequest(
        spec_text=sample_spec_text,
        project_name="FinDoc Custom",
    )

    result = await analyzer.analyze(request)

    assert isinstance(result, RequirementAnalysisResult)
    assert result.project_name == "FinDoc Custom"
    assert len(result.modules) == 2
    assert len(result.workflows) == 1
    assert len(result.business_rules) == 1
    assert len(result.functional_requirements) == 1
    assert len(result.non_functional_requirements) == 1
    assert len(result.risks_and_ambiguities) == 1
    assert len(result.evidence_references) >= 1

    # Verify mock interaction
    assert len(mock_llm_client.call_history) == 1
    call = mock_llm_client.call_history[0]
    assert call["type"] == "structured"
    assert call["schema"] == "RequirementAnalysisResult"
    assert "FinDoc Invoice Reconciliation" in call["prompt"]


@pytest.mark.asyncio
async def test_analyze_empty_input_raises_value_error(
    mock_llm_client: MockLLMClient,
    test_settings: Settings,
):
    analyzer = RequirementAnalyzer(llm_client=mock_llm_client, settings=test_settings)

    with pytest.raises(ValueError) as exc:
        # Pydantic AnalyzeRequest enforces min_length=10, but if passed empty or whitespace:
        analyzer.validate_request(AnalyzeRequest.model_construct(spec_text="   \n\t  "))
    assert "empty or whitespace" in str(exc.value)


@pytest.mark.asyncio
async def test_analyze_too_short_input_raises_value_error(
    mock_llm_client: MockLLMClient,
    test_settings: Settings,
):
    analyzer = RequirementAnalyzer(llm_client=mock_llm_client, settings=test_settings)

    with pytest.raises(ValueError) as exc:
        analyzer.validate_request(AnalyzeRequest.model_construct(spec_text="Too short"))
    assert "too short" in str(exc.value)


@pytest.mark.asyncio
async def test_analyze_malformed_llm_json_propagated(
    sample_spec_text: str,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_malformed_json(True)

    analyzer = RequirementAnalyzer(llm_client=mock_client, settings=test_settings)
    request = AnalyzeRequest(spec_text=sample_spec_text)

    with pytest.raises(LLMMalformedJSONError):
        await analyzer.analyze(request)


@pytest.mark.asyncio
async def test_analyze_timeout_propagated(
    sample_spec_text: str,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_timeout(True)

    analyzer = RequirementAnalyzer(llm_client=mock_client, settings=test_settings)
    request = AnalyzeRequest(spec_text=sample_spec_text)

    with pytest.raises(LLMTimeoutError):
        await analyzer.analyze(request)


@pytest.mark.asyncio
async def test_analyze_auth_failure_propagated(
    sample_spec_text: str,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_auth_failure(True)

    analyzer = RequirementAnalyzer(llm_client=mock_client, settings=test_settings)
    request = AnalyzeRequest(spec_text=sample_spec_text)

    with pytest.raises(LLMAuthenticationError):
        await analyzer.analyze(request)


@pytest.mark.asyncio
async def test_analyze_with_source_pages(
    mock_llm_client: MockLLMClient,
    test_settings: Settings,
):
    analyzer = RequirementAnalyzer(llm_client=mock_llm_client, settings=test_settings)
    request = AnalyzeRequest(
        spec_text="Consolidated spec overview text.",
        source_pages={
            "1": "Page 1: Ingestion requirements and OCR pipelines.",
            "2": "Page 2: Strict human approval for payments over $10k.",
        },
        project_name="Paged Project",
    )

    result = await analyzer.analyze(request)
    assert result.project_name == "Paged Project"

    # Verify that source pages were formatted into prompt
    assert len(mock_llm_client.call_history) == 1
    prompt = mock_llm_client.call_history[0]["prompt"]
    assert "--- [Page 1] ---" in prompt
    assert "--- [Page 2] ---" in prompt


def test_is_quote_grounded():
    source_text = "All refunds over $500 must strictly require approval by the billing admin."
    source_pages = {
        "1": "Overview section.",
        "2": "All refunds over $500\n  must strictly require approval by the billing admin.",
    }

    # 1. Exact match in source_text
    assert is_quote_grounded("refunds over $500", source_text) is True

    # 2. Match with multiline breaks in source_pages
    assert is_quote_grounded("refunds over $500 must strictly require approval", "", source_pages) is True

    # 3. Case-insensitive / whitespace-normalized match
    assert is_quote_grounded("  all refunds over $500   must strictly  ", source_text) is True

    # 4. Fabricated quote not in text
    assert is_quote_grounded("Every user gets free unlimited lifetime cloud credits", source_text) is False

    # 5. Empty quote
    assert is_quote_grounded("", source_text) is False


def test_verify_and_sync_evidence(
    sample_analysis_result: RequirementAnalysisResult,
    sample_spec_text: str,
    test_settings: Settings,
):
    analyzer = RequirementAnalyzer(llm_client=MockLLMClient(), settings=test_settings)

    # Add a fabricated quote to verify logger warning handling
    fabricated_ref = EvidenceReference(
        source_doc="FinDoc_Spec.pdf",
        page_number=99,
        exact_quote="This quote does not exist anywhere in the source text.",
        relevance="Fabrication test",
    )
    sample_analysis_result.evidence_references.append(fabricated_ref)

    request = AnalyzeRequest(
        spec_text=sample_spec_text,
        project_name="Override Title",
    )

    synced = analyzer.verify_and_sync_evidence(sample_analysis_result, request)

    assert synced.project_name == "Override Title"
    # Ensure evidence was gathered into master list
    assert len(synced.evidence_references) >= 1


@pytest.mark.asyncio
async def test_convenience_function_analyze_requirements(
    mock_llm_client: MockLLMClient,
    sample_spec_text: str,
):
    request = AnalyzeRequest(spec_text=sample_spec_text)
    result = await analyze_requirements(request, llm_client=mock_llm_client)
    assert isinstance(result, RequirementAnalysisResult)
    assert result.project_name == "FinDoc Invoice Reconciliation System"
