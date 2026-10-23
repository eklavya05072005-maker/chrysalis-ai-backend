"""Unit tests for Module W: Adaptive Requirement Wizard.

All tests run offline using MockLLMClient and deterministic fallbacks.
"""

import pytest
from backend.app.ai.wizard import AdaptiveRequirementWizard, generate_adaptive_questionnaire
from backend.app.core.config import Settings
from backend.app.integrations.llm_client import MockLLMClient, LLMTimeoutError
from backend.app.schemas.wizard import (
    WizardQuestionnaire,
    WizardQuestion,
    WizardOption,
)
from backend.app.schemas.analysis import RequirementAnalysisResult


@pytest.mark.asyncio
async def test_wizard_generate_questionnaire_success(
    mock_llm_client: MockLLMClient,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    wizard = AdaptiveRequirementWizard(llm_client=mock_llm_client, settings=test_settings)
    result = await wizard.generate_questionnaire(sample_analysis_result)

    assert isinstance(result, WizardQuestionnaire)
    assert result.project_name == sample_analysis_result.project_name
    assert 3 <= len(result.questions) <= 5

    for q in result.questions:
        assert isinstance(q, WizardQuestion)
        assert q.question_id.startswith("WIZ-")
        assert len(q.question_text) > 10
        assert len(q.options) >= 2
        assert len(q.reason) > 5
        assert q.category in ("goal", "autonomy", "connectors", "data_mode", "constraints")
        for opt in q.options:
            assert isinstance(opt, WizardOption)
            assert opt.option_id
            assert opt.label
            assert opt.architectural_impact


@pytest.mark.asyncio
async def test_wizard_fallback_on_llm_failure(
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    # Setup mock client that raises an exception
    failing_client = MockLLMClient()
    failing_client.simulate_timeout(True)

    wizard = AdaptiveRequirementWizard(llm_client=failing_client, settings=test_settings)
    result = await wizard.generate_questionnaire(sample_analysis_result)

    # Should fall back to safe deterministic questions without crashing
    assert isinstance(result, WizardQuestionnaire)
    assert 3 <= len(result.questions) <= 5
    assert result.project_name == sample_analysis_result.project_name
    categories = [q.category for q in result.questions]
    assert "autonomy" in categories
    assert "connectors" in categories


@pytest.mark.asyncio
async def test_wizard_clamping_too_many_questions(
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    # Prepare 7 questions
    overflow_client = MockLLMClient()
    many_questions = [
        WizardQuestion(
            question_id=f"WIZ-{i:02d}",
            category="constraints",
            question_text=f"Sample Question {i} regarding system constraints?",
            options=[
                WizardOption(option_id="O1", label="Option 1", description="Desc 1", architectural_impact="Impact 1"),
                WizardOption(option_id="O2", label="Option 2", description="Desc 2", architectural_impact="Impact 2"),
            ],
            reason=f"Reason {i}",
            allows_custom=True,
        )
        for i in range(1, 8)
    ]
    overflow_client.set_structured_response(
        WizardQuestionnaire,
        WizardQuestionnaire.model_construct(
            project_name=sample_analysis_result.project_name,
            questions=many_questions,
            notes="Overflow questionnaire",
            summary_context="Overflow questionnaire",
        ),
    )

    wizard = AdaptiveRequirementWizard(llm_client=overflow_client, settings=test_settings)
    result = await wizard.generate_questionnaire(sample_analysis_result)

    # Clamped to maximum 5 questions
    assert len(result.questions) == 5


@pytest.mark.asyncio
async def test_wizard_clamping_too_few_questions(
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    # Prepare only 1 question
    underflow_client = MockLLMClient()
    single_question = [
        WizardQuestion(
            question_id="WIZ-01",
            category="autonomy",
            question_text="Sample Question 1 regarding autonomy?",
            options=[
                WizardOption(option_id="O1", label="Option 1", description="Desc 1", architectural_impact="Impact 1"),
                WizardOption(option_id="O2", label="Option 2", description="Desc 2", architectural_impact="Impact 2"),
            ],
            reason="Reason 1",
            allows_custom=True,
        )
    ]
    underflow_client.set_structured_response(
        WizardQuestionnaire,
        WizardQuestionnaire.model_construct(
            project_name=sample_analysis_result.project_name,
            questions=single_question,
            notes="Underflow questionnaire",
            summary_context="Underflow questionnaire",
        ),
    )

    wizard = AdaptiveRequirementWizard(llm_client=underflow_client, settings=test_settings)
    result = await wizard.generate_questionnaire(sample_analysis_result)

    # Padded with fallbacks to minimum 3 questions
    assert len(result.questions) >= 3


@pytest.mark.asyncio
async def test_wizard_invalid_input(test_settings: Settings):
    wizard = AdaptiveRequirementWizard(settings=test_settings)
    with pytest.raises(ValueError):
        await wizard.generate_questionnaire(None)  # type: ignore


@pytest.mark.asyncio
async def test_generate_adaptive_questionnaire_convenience_fn(
    mock_llm_client: MockLLMClient,
    sample_analysis_result: RequirementAnalysisResult,
):
    result = await generate_adaptive_questionnaire(
        analysis=sample_analysis_result,
        llm_client=mock_llm_client,
    )
    assert isinstance(result, WizardQuestionnaire)
    assert 3 <= len(result.questions) <= 5
