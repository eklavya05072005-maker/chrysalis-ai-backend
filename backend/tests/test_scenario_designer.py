"""Unit tests for Module E: Scenario Design Engine.

All tests run offline using MockLLMClient and fixtures without external API calls.
"""

import pytest
from backend.app.ai.scenario_designer import (
    CANONICAL_SCENARIO_CATEGORIES,
    ScenarioDesignEngine,
    design_benchmark_scenarios,
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
    ArchitectureCandidatesResult,
    RequirementAnalysisResult,
    ScenarioCase,
    ScenarioDesignResult,
    TaskClassificationResult,
)


@pytest.mark.asyncio
async def test_design_scenarios_covers_all_six_categories(
    mock_llm_client: MockLLMClient,
    sample_analysis_result: RequirementAnalysisResult,
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_classification_result: TaskClassificationResult,
    test_settings: Settings,
):
    engine = ScenarioDesignEngine(llm_client=mock_llm_client, settings=test_settings)
    result = await engine.design_scenarios(
        analysis=sample_analysis_result,
        candidates_result=sample_architecture_candidates_result,
        classification=sample_classification_result,
    )

    assert isinstance(result, ScenarioDesignResult)
    assert len(result.scenarios) >= 6

    present_categories = {s.case_type for s in result.scenarios}
    expected_categories = set(CANONICAL_SCENARIO_CATEGORIES)
    assert expected_categories.issubset(present_categories)


@pytest.mark.asyncio
async def test_scenario_required_fields_and_valid_types(
    mock_llm_client: MockLLMClient,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    engine = ScenarioDesignEngine(llm_client=mock_llm_client, settings=test_settings)
    result = await engine.design_scenarios(analysis=sample_analysis_result)

    assert len(result.benchmarking_guide) > 10

    for idx, scen in enumerate(result.scenarios, start=1):
        assert scen.scenario_id.startswith("SCEN-")
        assert scen.case_type in CANONICAL_SCENARIO_CATEGORIES
        assert len(scen.title) > 3
        assert len(scen.description) > 10
        assert isinstance(scen.sample_input, dict)
        assert len(scen.expected_behavior) > 10
        assert len(scen.evaluation_criteria) >= 1
        assert len(scen.failure_conditions) >= 1


@pytest.mark.asyncio
async def test_requirement_traceability_and_candidate_relevance(
    mock_llm_client: MockLLMClient,
    sample_analysis_result: RequirementAnalysisResult,
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_classification_result: TaskClassificationResult,
    test_settings: Settings,
):
    engine = ScenarioDesignEngine(llm_client=mock_llm_client, settings=test_settings)
    result = await engine.design_scenarios(
        analysis=sample_analysis_result,
        candidates_result=sample_architecture_candidates_result,
        classification=sample_classification_result,
    )

    # Sensitive human approval scenario should reflect BR-01 ($10k approval)
    human_approval_scenarios = [
        s for s in result.scenarios if s.case_type == "sensitive_human_approval"
    ]
    assert len(human_approval_scenarios) >= 1
    has_approval_ref = any(
        "10,000" in s.title or "10,000" in s.description or "approval" in s.description.lower()
        for s in human_approval_scenarios
    )
    assert has_approval_ref


def test_empty_or_insufficient_input_raises_value_error(test_settings: Settings):
    engine = ScenarioDesignEngine(llm_client=MockLLMClient(), settings=test_settings)

    # None analysis
    with pytest.raises(ValueError) as exc1:
        engine.validate_inputs(None)  # type: ignore
    assert "Requirement analysis must be provided" in str(exc1.value)

    # Empty analysis with no requirements or rules
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
        engine.validate_inputs(empty_analysis)
    assert "must contain functional requirements or business rules" in str(exc2.value)


def test_missing_canonical_category_triggers_fallback_synthesis(
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    engine = ScenarioDesignEngine(llm_client=MockLLMClient(), settings=test_settings)

    # Partial result with only 1 scenario constructed via model_construct to simulate partial LLM output
    partial_result = ScenarioDesignResult.model_construct(
        project_name=sample_analysis_result.project_name,
        scenarios=[
            ScenarioCase(
                scenario_id="SCEN-01",
                case_type="normal_workflow",
                title="Only Normal Workflow",
                description="Testing single workflow coverage",
                sample_input={"key": "val"},
                expected_behavior="Normal processing",
                evaluation_criteria=["Pass criteria"],
                failure_conditions=["Fail conditions"],
            )
        ],
        benchmarking_guide="Guide",
    )

    sanitized = engine._verify_and_sanitize_scenarios(partial_result, sample_analysis_result)

    # All 6 categories must now be present due to fallback synthesis
    present_categories = {s.case_type for s in sanitized.scenarios}
    assert set(CANONICAL_SCENARIO_CATEGORIES).issubset(present_categories)
    assert len(sanitized.scenarios) >= 6


def test_duplicate_scenario_ids_and_titles_sanitization(
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    engine = ScenarioDesignEngine(llm_client=MockLLMClient(), settings=test_settings)

    # Scenarios with duplicated ID and duplicated Title constructed via model_construct
    dup_result = ScenarioDesignResult.model_construct(
        project_name=sample_analysis_result.project_name,
        scenarios=[
            ScenarioCase(
                scenario_id="SCEN-DUP",
                case_type="normal_workflow",
                title="Duplicate Name",
                description="Desc 1",
                sample_input={},
                expected_behavior="Behavior 1",
                evaluation_criteria=["Criterion 1"],
                failure_conditions=["Condition 1"],
            ),
            ScenarioCase(
                scenario_id="SCEN-DUP",  # Duplicate ID
                case_type="invalid_input",
                title="Duplicate Name",  # Duplicate Title
                description="Desc 2",
                sample_input={},
                expected_behavior="Behavior 2",
                evaluation_criteria=["Criterion 2"],
                failure_conditions=["Condition 2"],
            ),
        ],
        benchmarking_guide="Guide",
    )

    sanitized = engine._verify_and_sanitize_scenarios(dup_result, sample_analysis_result)

    ids = [s.scenario_id for s in sanitized.scenarios]
    assert len(ids) == len(set(ids))  # All unique IDs

    titles = [s.title for s in sanitized.scenarios]
    assert len(titles) == len(set(titles))  # All unique titles


def test_empty_scenarios_from_llm_raises_error(
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    engine = ScenarioDesignEngine(llm_client=MockLLMClient(), settings=test_settings)
    empty_result = ScenarioDesignResult.model_construct(
        project_name=sample_analysis_result.project_name,
        scenarios=[],
        benchmarking_guide="Guide",
    )

    with pytest.raises(LLMError) as exc:
        engine._verify_and_sanitize_scenarios(empty_result, sample_analysis_result)
    assert "empty scenario list" in str(exc.value)


@pytest.mark.asyncio
async def test_timeout_propagated(
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_timeout(True)

    engine = ScenarioDesignEngine(llm_client=mock_client, settings=test_settings)
    with pytest.raises(LLMTimeoutError):
        await engine.design_scenarios(sample_analysis_result)


@pytest.mark.asyncio
async def test_provider_failure_propagated(
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_auth_failure(True)

    engine = ScenarioDesignEngine(llm_client=mock_client, settings=test_settings)
    with pytest.raises(LLMAuthenticationError):
        await engine.design_scenarios(sample_analysis_result)


@pytest.mark.asyncio
async def test_malformed_llm_json_propagated(
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_malformed_json(True)

    engine = ScenarioDesignEngine(llm_client=mock_client, settings=test_settings)
    with pytest.raises(LLMMalformedJSONError):
        await engine.design_scenarios(sample_analysis_result)


@pytest.mark.asyncio
async def test_convenience_function_design_benchmark_scenarios(
    mock_llm_client: MockLLMClient,
    sample_analysis_result: RequirementAnalysisResult,
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_classification_result: TaskClassificationResult,
):
    result = await design_benchmark_scenarios(
        analysis=sample_analysis_result,
        candidates_result=sample_architecture_candidates_result,
        classification=sample_classification_result,
        llm_client=mock_llm_client,
    )
    assert isinstance(result, ScenarioDesignResult)
    assert len(result.scenarios) >= 6
    assert result.project_name == "FinDoc Invoice Reconciliation System"
