"""Unit tests for Module D: Architecture Evaluation Engine.

All tests run offline using MockLLMClient and fixtures without external API calls.
"""

import pytest
from backend.app.ai.evaluator import (
    DEFAULT_CRITERIA_WEIGHTS,
    ArchitectureEvaluator,
    compute_deterministic_complexity_score,
    evaluate_architecture_candidates,
    normalize_weights,
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
    ArchitectureEvaluationResult,
    CriterionEvaluation,
    RequirementAnalysisResult,
)


@pytest.mark.asyncio
async def test_evaluate_all_three_candidates_consistently(
    mock_llm_client: MockLLMClient,
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    evaluator = ArchitectureEvaluator(llm_client=mock_llm_client, settings=test_settings)
    result = await evaluator.evaluate(
        candidates_result=sample_architecture_candidates_result,
        analysis=sample_analysis_result,
    )

    assert isinstance(result, ArchitectureEvaluationResult)
    assert len(result.evaluations) == 3

    candidate_ids = {e.candidate_id for e in result.evaluations}
    assert candidate_ids == {"CAND-CONSERVATIVE", "CAND-HYBRID", "CAND-AUTOMATION"}

    standard_keys = {
        "requirement_coverage",
        "reliability",
        "implementation_complexity",
        "cost",
        "latency",
        "operational_risk",
        "human_oversight",
    }

    for cand_eval in result.evaluations:
        eval_keys = {crit.criterion_key for crit in cand_eval.criteria_scores}
        assert standard_keys.issubset(eval_keys)
        assert 0.0 <= cand_eval.total_weighted_score <= 10.0
        assert len(cand_eval.key_strengths) >= 1
        assert len(cand_eval.primary_trade_offs) >= 1

    # Winner must match highest total_weighted_score
    top_score = max(e.total_weighted_score for e in result.evaluations)
    winner = next(e for e in result.evaluations if e.candidate_id == result.selected_candidate_id)
    assert winner.total_weighted_score == top_score

    # Methodology notes must explicitly disclose non-universality
    assert "not a universally optimal architecture" in result.methodology_notes


def test_score_and_weight_boundaries_and_clamping(
    sample_architecture_evaluation_result: ArchitectureEvaluationResult,
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    test_settings: Settings,
):
    evaluator = ArchitectureEvaluator(llm_client=MockLLMClient(), settings=test_settings)

    # 1. Custom weight normalization
    custom = {"requirement_coverage": 2.0, "reliability": 2.0}
    norm = normalize_weights(custom)
    assert norm["requirement_coverage"] == 0.5
    assert norm["reliability"] == 0.5
    assert sum(norm.values()) == 1.0

    # 2. Non-positive sum raises ValueError
    with pytest.raises(ValueError) as exc:
        normalize_weights({"cost": 0.0, "latency": 0.0})
    assert "greater than zero" in str(exc.value)

    # 3. Score boundary clamping in sanitize
    # Artificially inject out-of-bound scores
    evals = sample_architecture_evaluation_result.evaluations
    evals[0].criteria_scores[0].raw_score = -4.0
    evals[0].criteria_scores[1].raw_score = 14.5
    target_id = evals[0].candidate_id

    sanitized = evaluator._sanitize_and_rank_evaluations(
        sample_architecture_evaluation_result,
        weights=DEFAULT_CRITERIA_WEIGHTS,
        candidates_result=sample_architecture_candidates_result,
    )

    modified_eval = next(e for e in sanitized.evaluations if e.candidate_id == target_id)
    assert modified_eval.criteria_scores[0].raw_score == 0.0
    assert modified_eval.criteria_scores[1].raw_score == 10.0


def test_correct_aggregation_and_ranking(
    sample_architecture_evaluation_result: ArchitectureEvaluationResult,
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    test_settings: Settings,
):
    evaluator = ArchitectureEvaluator(llm_client=MockLLMClient(), settings=test_settings)

    # Force candidate 1 to have very low scores and candidate 2 to have high scores
    evals = sample_architecture_evaluation_result.evaluations
    for c in evals[0].criteria_scores:
        c.raw_score = 2.0
    for c in evals[1].criteria_scores:
        c.raw_score = 9.0

    sanitized = evaluator._sanitize_and_rank_evaluations(
        sample_architecture_evaluation_result,
        weights=DEFAULT_CRITERIA_WEIGHTS,
        candidates_result=sample_architecture_candidates_result,
    )

    # Candidate 2 (CAND-HYBRID) should now be the top-ranked candidate
    assert sanitized.selected_candidate_id == "CAND-HYBRID"
    assert sanitized.evaluations[0].candidate_id == "CAND-HYBRID"
    assert sanitized.evaluations[0].total_weighted_score > sanitized.evaluations[2].total_weighted_score


def test_missing_or_malformed_inputs_handling(
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    evaluator = ArchitectureEvaluator(llm_client=MockLLMClient(), settings=test_settings)

    # None candidates_result
    with pytest.raises(ValueError) as exc1:
        evaluator.validate_inputs(None, sample_analysis_result)  # type: ignore
    assert "Architecture candidates result must be provided" in str(exc1.value)

    # Candidate count != 3
    truncated_candidates = ArchitectureCandidatesResult.model_construct(
        project_name=sample_architecture_candidates_result.project_name,
        candidates=sample_architecture_candidates_result.candidates[:2],
        comparison_summary="Truncated",
    )
    with pytest.raises(ValueError) as exc2:
        evaluator.validate_inputs(truncated_candidates, sample_analysis_result)
    assert "Expected exactly 3 architecture candidates" in str(exc2.value)

    # None analysis
    with pytest.raises(ValueError) as exc3:
        evaluator.validate_inputs(sample_architecture_candidates_result, None)  # type: ignore
    assert "Requirement analysis must be provided" in str(exc3.value)


def test_honest_score_type_labels(
    sample_architecture_evaluation_result: ArchitectureEvaluationResult,
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    test_settings: Settings,
):
    evaluator = ArchitectureEvaluator(llm_client=MockLLMClient(), settings=test_settings)

    # Corrupt score types to non-standard or inappropriate values
    for cand in sample_architecture_evaluation_result.evaluations:
        for crit in cand.criteria_scores:
            if crit.criterion_key in ["cost", "latency"]:
                crit.score_type = "heuristic"  # Should be elevated to estimated
            else:
                crit.score_type = "unvalidated_claim"  # type: ignore

    sanitized = evaluator._sanitize_and_rank_evaluations(
        sample_architecture_evaluation_result,
        weights=DEFAULT_CRITERIA_WEIGHTS,
        candidates_result=sample_architecture_candidates_result,
    )

    for cand in sanitized.evaluations:
        for crit in cand.criteria_scores:
            if crit.criterion_key in ["cost", "latency"]:
                assert crit.score_type in ["estimated", "simulated", "measured"]
            else:
                assert crit.score_type in ["heuristic", "estimated", "simulated", "measured"]
                assert crit.score_type != "unvalidated_claim"


@pytest.mark.asyncio
async def test_timeout_propagated(
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_timeout(True)

    evaluator = ArchitectureEvaluator(llm_client=mock_client, settings=test_settings)
    with pytest.raises(LLMTimeoutError):
        await evaluator.evaluate(sample_architecture_candidates_result, sample_analysis_result)


@pytest.mark.asyncio
async def test_provider_failure_propagated(
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_auth_failure(True)

    evaluator = ArchitectureEvaluator(llm_client=mock_client, settings=test_settings)
    with pytest.raises(LLMAuthenticationError):
        await evaluator.evaluate(sample_architecture_candidates_result, sample_analysis_result)


@pytest.mark.asyncio
async def test_malformed_llm_json_propagated(
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
    test_settings: Settings,
):
    mock_client = MockLLMClient()
    mock_client.simulate_malformed_json(True)

    evaluator = ArchitectureEvaluator(llm_client=mock_client, settings=test_settings)
    with pytest.raises(LLMMalformedJSONError):
        await evaluator.evaluate(sample_architecture_candidates_result, sample_analysis_result)


def test_repeatable_deterministic_complexity_scoring():
    # Complexity 2.5 -> raw_score = 11.0 - 2.5 = 8.5
    eval_25 = compute_deterministic_complexity_score(complexity_score=2.5, weight=0.15)
    assert eval_25.criterion_key == "implementation_complexity"
    assert eval_25.raw_score == 8.5
    assert eval_25.weight == 0.15
    assert eval_25.weighted_score == 1.275
    assert eval_25.score_type == "heuristic"

    # Complexity 8.5 -> raw_score = 11.0 - 8.5 = 2.5
    eval_85 = compute_deterministic_complexity_score(complexity_score=8.5, weight=0.15)
    assert eval_85.raw_score == 2.5
    assert eval_85.weighted_score == 0.375

    # Out of range clamping
    eval_low = compute_deterministic_complexity_score(complexity_score=-2.0, weight=0.15)
    assert eval_low.raw_score == 10.0  # clamped to 1.0 -> 11.0 - 1.0 = 10.0

    eval_high = compute_deterministic_complexity_score(complexity_score=15.0, weight=0.15)
    assert eval_high.raw_score == 1.0  # clamped to 10.0 -> 11.0 - 10.0 = 1.0

    # Repeatability check
    repeat_1 = compute_deterministic_complexity_score(complexity_score=4.0, weight=0.20)
    repeat_2 = compute_deterministic_complexity_score(complexity_score=4.0, weight=0.20)
    assert repeat_1.model_dump() == repeat_2.model_dump()


@pytest.mark.asyncio
async def test_convenience_function_evaluate_architecture_candidates(
    mock_llm_client: MockLLMClient,
    sample_architecture_candidates_result: ArchitectureCandidatesResult,
    sample_analysis_result: RequirementAnalysisResult,
):
    result = await evaluate_architecture_candidates(
        candidates_result=sample_architecture_candidates_result,
        analysis=sample_analysis_result,
        llm_client=mock_llm_client,
    )
    assert isinstance(result, ArchitectureEvaluationResult)
    assert len(result.evaluations) == 3
    assert result.selected_candidate_id in {"CAND-CONSERVATIVE", "CAND-HYBRID", "CAND-AUTOMATION"}
