"""Module K: Requirement Confirmation Engine for Chrysalis AI.

Merges Module A's validated requirement analysis with operator responses from
the Module W Adaptive Requirement Wizard into an immutable ConfirmedProjectSpec.
Preserves verbatim evidence citations, does not invent requirements, and enforces
explicit user confirmation before architectural commitment.
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Any

from backend.app.schemas.analysis import Requirement, RequirementAnalysisResult
from backend.app.schemas.common import EvidenceReference
from backend.app.schemas.wizard import (
    ConfirmedProjectSpec,
    WizardAnswerSubmission,
)

logger = logging.getLogger(__name__)


class RequirementConfirmer:
    """Merges analyzed software requirements and wizard answers into a confirmed specification."""

    def validate_inputs(self, analysis: RequirementAnalysisResult) -> None:
        """Validate input requirement analysis."""
        if analysis is None:
            raise ValueError("Requirement analysis result must be provided.")
        if not analysis.project_name or not analysis.project_name.strip():
            raise ValueError("Project name must not be empty.")

    def confirm_specification(
        self,
        analysis: RequirementAnalysisResult,
        submission: WizardAnswerSubmission | None = None,
        confirm: bool = False,
        confirmed_by_user: bool | None = None,
    ) -> ConfirmedProjectSpec:
        """
        Synthesizes a ConfirmedProjectSpec from requirement analysis and wizard answers.
        
        - Strictly preserves all evidence citations and page numbers.
        - Strictly avoids inventing requirements or hallucinating citations.
        - Sets confirmed_by_user=False unless confirm=True or confirmed_by_user=True is explicitly passed.
        """
        self.validate_inputs(analysis)
        is_confirmed = confirmed_by_user if confirmed_by_user is not None else confirm

        # 1. Base Project Identity & Primary Goal
        p_name = analysis.project_name.strip()
        primary_goal = analysis.executive_summary or f"Operational automation for {p_name}."

        # Default Boundaries
        autonomy_boundary = "human_approval_for_sensitive_actions"
        data_mode = "synthetic"
        connectors: list[str] = ["rest_api", "database"]
        priorities: list[str] = ["accuracy", "reliability"]
        constraints: dict[str, Any] = {}
        clarified_parameters: dict[str, Any] = {}

        # 2. Extract User Answers from Submission (if provided)
        if submission and submission.answers:
            for ans in submission.answers:
                qid = (ans.question_id or "").upper()
                custom = (ans.custom_answer or "").strip()
                opts = ans.selected_option_ids or []
                ans_val = custom or ans.selected_option_id or (opts[0] if opts else ans.answer_summary)
                if ans.question_id:
                    clarified_parameters[ans.question_id] = ans_val

                # Handle Goal Question
                if "GOAL" in qid:
                    if custom:
                        primary_goal = custom
                    elif opts:
                        opt_id = opts[0].lower()
                        if "query" in opt_id:
                            primary_goal = f"Informational query answering and documentation assistant for {p_name}."
                        elif "transaction" in opt_id:
                            primary_goal = f"Multi-step business transaction processing and verification for {p_name}."
                        elif "investigation" in opt_id:
                            primary_goal = f"Autonomous case investigation across disparate data sources for {p_name}."

                # Handle Autonomy Question
                elif "AUTONOMY" in qid:
                    if custom and "suggest" in custom.lower():
                        autonomy_boundary = "suggest_only"
                    elif custom and "low_risk" in custom.lower():
                        autonomy_boundary = "autonomous_low_risk"
                    elif opts:
                        opt_id = opts[0].lower()
                        if "suggest" in opt_id:
                            autonomy_boundary = "suggest_only"
                        elif "low_risk" in opt_id:
                            autonomy_boundary = "autonomous_low_risk"
                        else:
                            autonomy_boundary = "human_approval_for_sensitive_actions"

                # Handle Connectors Question
                elif "CONN" in qid:
                    found_conns = []
                    for opt in opts:
                        opt_l = opt.lower()
                        if "mcp" in opt_l and "mcp" not in found_conns:
                            found_conns.append("mcp")
                        elif "rest" in opt_l and "rest_api" not in found_conns:
                            found_conns.append("rest_api")
                        elif "db" in opt_l and "database" not in found_conns:
                            found_conns.append("database")
                        elif "sdk" in opt_l and "custom_sdk" not in found_conns:
                            found_conns.append("custom_sdk")
                    if found_conns:
                        connectors = found_conns
                    if custom:
                        constraints["custom_connector_notes"] = custom

                # Handle Data Mode Question
                elif "DATA" in qid:
                    if opts:
                        opt_id = opts[0].lower()
                        if "anonymized" in opt_id:
                            data_mode = "anonymized"
                        elif "live" in opt_id:
                            data_mode = "approved_live"
                        else:
                            data_mode = "synthetic"
                    if custom:
                        constraints["data_environment_notes"] = custom

                # Handle Priorities or Constraints
                elif "PRIORITY" in qid:
                    if opts:
                        priorities = opts
                    if custom:
                        priorities.append(custom)
                elif "CONST" in qid:
                    if custom:
                        constraints["custom_constraints"] = custom
                    if opts:
                        constraints["selected_constraints"] = opts

            if submission.additional_notes:
                constraints["operator_notes"] = submission.additional_notes.strip()

        # 3. Harvest All Requirements from Analysis (Zero Hallucination)
        all_reqs: list[Requirement] = []

        # Functional requirements
        for fr in analysis.functional_requirements:
            all_reqs.append(
                Requirement(
                    req_id=fr.req_id,
                    title=fr.title,
                    description=fr.description,
                    category="functional",
                    priority=fr.priority or "high",
                    evidence=list(fr.evidence),
                )
            )

        # Non-functional requirements
        for nfr in analysis.non_functional_requirements:
            all_reqs.append(
                Requirement(
                    req_id=nfr.req_id,
                    title=nfr.title,
                    description=nfr.description,
                    category="non_functional",
                    priority=nfr.priority or "medium",
                    evidence=list(nfr.evidence),
                )
            )

        # 4. Harvest Evidence References
        all_evidence: list[EvidenceReference] = list(analysis.evidence_references)
        for r in all_reqs:
            for ev in r.evidence:
                if ev not in all_evidence:
                    all_evidence.append(ev)

        # 5. Determine Confirmation Timestamp
        timestamp = datetime.now(timezone.utc).isoformat() if confirm else None

        return ConfirmedProjectSpec(
            project_name=p_name,
            primary_goal=primary_goal,
            executive_summary=analysis.executive_summary,
            autonomy_boundary=autonomy_boundary,
            data_mode=data_mode,
            connector_preferences=connectors,
            priorities=priorities,
            constraints=constraints,
            clarified_parameters=clarified_parameters,
            confirmed_requirements=all_reqs,
            functional_requirements=list(analysis.functional_requirements),
            non_functional_requirements=list(analysis.non_functional_requirements),
            modules=list(analysis.modules),
            workflows=list(analysis.workflows),
            business_rules=list(analysis.business_rules),
            risks_and_ambiguities=list(analysis.risks_and_ambiguities),
            evidence_references=all_evidence,
            confirmed_by_user=is_confirmed,
            confirmation_timestamp=timestamp,
        )


def confirm_project_spec(
    analysis: RequirementAnalysisResult,
    submission: WizardAnswerSubmission | None = None,
    confirm: bool = False,
    confirmed_by_user: bool | None = None,
) -> ConfirmedProjectSpec:
    """Convenience helper to synthesize a ConfirmedProjectSpec."""
    confirmer = RequirementConfirmer()
    return confirmer.confirm_specification(
        analysis=analysis,
        submission=submission,
        confirm=confirm,
        confirmed_by_user=confirmed_by_user,
    )
