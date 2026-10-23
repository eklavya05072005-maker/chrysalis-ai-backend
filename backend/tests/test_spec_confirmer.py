"""Unit tests for Module K: Requirement Confirmer.

Deterministic merging of requirement analysis and user answers into ConfirmedProjectSpec.
"""

import pytest
from backend.app.ai.spec_confirmer import RequirementConfirmer, confirm_project_spec
from backend.app.schemas.analysis import RequirementAnalysisResult
from backend.app.schemas.wizard import (
    ConfirmedProjectSpec,
    WizardAnswer,
    WizardAnswerSubmission,
)


def test_spec_confirmer_preserves_requirements_and_evidence(
    sample_analysis_result: RequirementAnalysisResult,
    sample_wizard_submission: WizardAnswerSubmission,
):
    confirmer = RequirementConfirmer()
    confirmed = confirmer.confirm_specification(
        analysis=sample_analysis_result,
        submission=sample_wizard_submission,
        confirmed_by_user=True,
    )

    assert isinstance(confirmed, ConfirmedProjectSpec)
    assert confirmed.project_name == sample_analysis_result.project_name
    assert confirmed.confirmed_by_user is True

    # Zero hallucination check: counts match exactly
    assert len(confirmed.functional_requirements) == len(sample_analysis_result.functional_requirements)
    assert len(confirmed.modules) == len(sample_analysis_result.modules)
    assert len(confirmed.workflows) == len(sample_analysis_result.workflows)
    assert len(confirmed.business_rules) == len(sample_analysis_result.business_rules)
    assert len(confirmed.evidence_references) == len(sample_analysis_result.evidence_references)

    # Citations & page numbers preserved
    for orig_req, conf_req in zip(sample_analysis_result.functional_requirements, confirmed.functional_requirements):
        assert conf_req.req_id == orig_req.req_id
        assert conf_req.title == orig_req.title
        assert len(conf_req.evidence) == len(orig_req.evidence)
        for orig_ev, conf_ev in zip(orig_req.evidence, conf_req.evidence):
            assert conf_ev.exact_quote == orig_ev.exact_quote
            assert conf_ev.page_number == orig_ev.page_number
            assert conf_ev.source_doc == orig_ev.source_doc


def test_spec_confirmer_unconfirmed_by_default(
    sample_analysis_result: RequirementAnalysisResult,
    sample_wizard_submission: WizardAnswerSubmission,
):
    confirmer = RequirementConfirmer()
    unconfirmed = confirmer.confirm_specification(
        analysis=sample_analysis_result,
        submission=sample_wizard_submission,
        confirmed_by_user=False,
    )

    assert unconfirmed.confirmed_by_user is False
    assert len(unconfirmed.clarified_parameters) == len(sample_wizard_submission.answers)


def test_spec_confirmer_custom_answers(
    sample_analysis_result: RequirementAnalysisResult,
):
    submission = WizardAnswerSubmission(
        project_name=sample_analysis_result.project_name,
        answers=[
            WizardAnswer(
                question_id="WIZ-01",
                custom_answer="Custom autonomy level: max $5,000 threshold with Slack bot approvals.",
                answer_summary="Custom threshold with Slack bot",
            ),
            WizardAnswer(
                question_id="WIZ-02",
                selected_option_id="OPT-MCP",
                answer_summary="Model Context Protocol tools",
            ),
        ],
    )

    confirmer = RequirementConfirmer()
    spec = confirmer.confirm_specification(
        analysis=sample_analysis_result,
        submission=submission,
        confirmed_by_user=True,
    )

    assert "WIZ-01" in spec.clarified_parameters
    assert spec.clarified_parameters["WIZ-01"] == "Custom autonomy level: max $5,000 threshold with Slack bot approvals."
    assert "WIZ-02" in spec.clarified_parameters
    assert spec.clarified_parameters["WIZ-02"] == "OPT-MCP"


def test_spec_confirmer_none_submission(
    sample_analysis_result: RequirementAnalysisResult,
):
    confirmer = RequirementConfirmer()
    spec = confirmer.confirm_specification(
        analysis=sample_analysis_result,
        submission=None,
        confirmed_by_user=False,
    )

    assert isinstance(spec, ConfirmedProjectSpec)
    assert spec.confirmed_by_user is False
    assert spec.clarified_parameters == {}


def test_spec_confirmer_invalid_analysis():
    confirmer = RequirementConfirmer()
    with pytest.raises(ValueError):
        confirmer.confirm_specification(
            analysis=None,  # type: ignore
            submission=None,
        )


def test_confirm_project_spec_convenience_fn(
    sample_analysis_result: RequirementAnalysisResult,
    sample_wizard_submission: WizardAnswerSubmission,
):
    spec = confirm_project_spec(
        analysis=sample_analysis_result,
        submission=sample_wizard_submission,
        confirmed_by_user=True,
    )
    assert isinstance(spec, ConfirmedProjectSpec)
    assert spec.confirmed_by_user is True
