"""Module D: Architecture Evaluation Engine for Chrysalis AI.

Performs transparent, multi-criteria trade-off scoring and relative ranking
across candidate architectures using explicit weights and honest score classifications.
"""

from __future__ import annotations
import logging
from typing import Any
from backend.app.ai.prompts import (
    ARCHITECTURE_EVALUATION_SYSTEM_PROMPT,
    build_architecture_evaluation_prompt,
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
from backend.app.schemas.evaluation import (
    ArchitectureEvaluationResult,
    CandidateEvaluation,
    CriterionEvaluation,
)

logger = logging.getLogger(__name__)

DEFAULT_CRITERIA_WEIGHTS: dict[str, float] = {
    "requirement_coverage": 0.20,
    "reliability": 0.15,
    "implementation_complexity": 0.15,
    "cost": 0.10,
    "latency": 0.10,
    "operational_risk": 0.15,
    "human_oversight": 0.15,
}

CRITERIA_DISPLAY_NAMES: dict[str, str] = {
    "requirement_coverage": "Requirement Coverage",
    "reliability": "Reliability & Fault Tolerance",
    "implementation_complexity": "Implementation Complexity & Feasibility",
    "cost": "Operating Cost Efficiency",
    "latency": "Transaction Latency & Responsiveness",
    "operational_risk": "Security & Operational Risk Mitigation",
    "human_oversight": "Human Oversight & Guardrails",
}


def normalize_weights(weights: dict[str, float] | None) -> dict[str, float]:
    """Ensure criteria weights sum to exactly 1.0 and cover standard criteria."""
    active = dict(weights or DEFAULT_CRITERIA_WEIGHTS)
    total = sum(active.values())
    if total <= 0:
        raise ValueError("Sum of criteria weights must be greater than zero.")
    return {k: round(v / total, 4) for k, v in active.items()}


def compute_deterministic_complexity_score(complexity_score: float, weight: float) -> CriterionEvaluation:
    """Derive deterministic implementation feasibility score from candidate complexity score.
    
    In Chrysalis AI, candidate complexity_score ranges from 1.0 (simplest) to 10.0 (most complex).
    For the evaluator, raw_score is normalized so 10.0 is the best (easiest to implement):
    raw_score = 11.0 - complexity_score.
    """
    clamped_comp = max(1.0, min(10.0, complexity_score))
    raw = round(11.0 - clamped_comp, 2)
    weighted = round(raw * weight, 3)
    return CriterionEvaluation(
        criterion_key="implementation_complexity",
        criterion_name=CRITERIA_DISPLAY_NAMES["implementation_complexity"],
        raw_score=raw,
        weight=weight,
        weighted_score=weighted,
        score_type="heuristic",
        justification=(
            f"Deterministically mapped from candidate complexity score {clamped_comp:.1f}/10.0. "
            f"Higher score represents lower construction, debugging, and operational complexity."
        ),
    )


class ArchitectureEvaluator:
    """Orchestrates multi-criteria comparison and transparent ranking of architecture candidates."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        settings: Settings | None = None,
        default_weights: dict[str, float] | None = None,
    ):
        self.settings = settings or get_settings()
        self.llm_client = llm_client or get_llm_client(self.settings)
        self.weights = normalize_weights(default_weights or DEFAULT_CRITERIA_WEIGHTS)

    def validate_inputs(
        self,
        candidates_result: ArchitectureCandidatesResult,
        analysis: RequirementAnalysisResult,
    ) -> None:
        """Verify that candidates and requirements are valid for evaluation."""
        if candidates_result is None:
            raise ValueError("Architecture candidates result must be provided.")
        if len(candidates_result.candidates) != 3:
            raise ValueError(
                f"Expected exactly 3 architecture candidates for evaluation, got {len(candidates_result.candidates)}."
            )
        if analysis is None:
            raise ValueError("Requirement analysis must be provided.")

    def _sanitize_and_rank_evaluations(
        self,
        result: ArchitectureEvaluationResult,
        weights: dict[str, float],
        candidates_result: ArchitectureCandidatesResult | None = None,
    ) -> ArchitectureEvaluationResult:
        """Sanitize scores, inject deterministic criteria, recalculate totals, and select top candidate."""
        if len(result.evaluations) != 3:
            raise LLMError(
                f"Architecture Evaluation must evaluate all 3 candidates, but received {len(result.evaluations)}."
            )

        cand_map = {c.candidate_id: c for c in candidates_result.candidates} if candidates_result else {}

        for idx, candidate_eval in enumerate(result.evaluations):
            cand = cand_map.get(candidate_eval.candidate_id)
            if cand is None and candidates_result and idx < len(candidates_result.candidates):
                cand = candidates_result.candidates[idx]
                candidate_eval.candidate_id = cand.candidate_id
                candidate_eval.candidate_name = cand.name
                candidate_eval.archetype = cand.archetype

            # If candidate is known, deterministically compute implementation complexity
            if cand is not None:
                comp_weight = weights.get("implementation_complexity", 0.15)
                det_crit = compute_deterministic_complexity_score(cand.complexity_score, comp_weight)
                found = False
                for crit_idx, crit in enumerate(candidate_eval.criteria_scores):
                    if crit.criterion_key == "implementation_complexity":
                        candidate_eval.criteria_scores[crit_idx] = det_crit
                        found = True
                        break
                if not found:
                    candidate_eval.criteria_scores.append(det_crit)

            total_weighted = 0.0

            for crit in candidate_eval.criteria_scores:
                # 1. Clamp raw score between 0.0 and 10.0
                if crit.raw_score < 0.0:
                    crit.raw_score = 0.0
                elif crit.raw_score > 10.0:
                    crit.raw_score = 10.0

                # 2. Reconcile weight from active weights
                if crit.criterion_key in weights:
                    crit.weight = weights[crit.criterion_key]

                # 3. Recalculate weighted score
                crit.weighted_score = round(crit.raw_score * crit.weight, 3)
                total_weighted += crit.weighted_score

                # 4. Enforce honest score type
                if crit.criterion_key in ["cost", "latency"]:
                    if crit.score_type not in ["estimated", "simulated", "measured"]:
                        crit.score_type = "estimated"
                else:
                    if crit.score_type not in ["heuristic", "estimated", "simulated", "measured"]:
                        crit.score_type = "heuristic"

            candidate_eval.total_weighted_score = round(total_weighted, 2)

        # Sort candidates descending by total_weighted_score
        sorted_evals = sorted(result.evaluations, key=lambda e: e.total_weighted_score, reverse=True)
        result.evaluations = sorted_evals
        top_candidate = sorted_evals[0]

        result.selected_candidate_id = top_candidate.candidate_id
        result.weights_applied = weights
        result.methodology_notes = (
            "Scores represent transparent heuristic and estimated evaluations based on declared architectural "
            "components, complexity definitions, and stated usage assumptions. Results do not represent live "
            "benchmark measurements. The recommended candidate is identified as the highest-scoring option "
            "solely among the candidates evaluated under the active criteria weights, not a universally optimal architecture."
        )

        return result

    async def evaluate(
        self,
        candidates_result: ArchitectureCandidatesResult,
        analysis: RequirementAnalysisResult,
        custom_weights: dict[str, float] | None = None,
    ) -> ArchitectureEvaluationResult:
        """Execute multi-criteria evaluation across all three candidates."""
        self.validate_inputs(candidates_result, analysis)

        weights = normalize_weights(custom_weights) if custom_weights else self.weights

        prompt = build_architecture_evaluation_prompt(
            candidates_result=candidates_result,
            analysis=analysis,
            weights_applied=weights,
        )

        try:
            raw_result = await self.llm_client.generate_structured(
                prompt=prompt,
                schema=ArchitectureEvaluationResult,
                system_instruction=ARCHITECTURE_EVALUATION_SYSTEM_PROMPT,
                temperature=self.settings.llm_temperature,
            )
        except LLMTimeoutError as exc:
            logger.error("LLM timeout during architecture evaluation: %s", exc)
            raise
        except LLMError as exc:
            logger.error("LLM error during architecture evaluation: %s", exc)
            raise
        except Exception as exc:
            logger.error("Unexpected error in ArchitectureEvaluator: %s", exc)
            raise LLMError(f"Unexpected error during architecture evaluation: {exc}") from exc

        return self._sanitize_and_rank_evaluations(raw_result, weights, candidates_result)


async def evaluate_architecture_candidates(
    candidates_result: ArchitectureCandidatesResult,
    analysis: RequirementAnalysisResult,
    custom_weights: dict[str, float] | None = None,
    llm_client: LLMClient | None = None,
    settings: Settings | None = None,
) -> ArchitectureEvaluationResult:
    """Convenience helper for Member 2 backend to trigger architecture evaluation."""
    evaluator = ArchitectureEvaluator(llm_client=llm_client, settings=settings)
    return await evaluator.evaluate(
        candidates_result=candidates_result,
        analysis=analysis,
        custom_weights=custom_weights,
    )
