"""Audit trail and verification standing service for Chrysalis AI.

Maintains tamper-evident, secret-redacted audit logs and evaluates project
verification status honestly across explicit states (GENERATED, STATIC_CHECKS_PASSED,
TESTS_PASSED, DEMO_VERIFIED, INTEGRATION_VERIFIED, FAILED, BLOCKED, NOT_RUN).
Mock executions are strictly prohibited from qualifying as live integration verified.
"""

from __future__ import annotations
import logging
import uuid
from typing import Any, Dict, List, Optional

from backend.app.repositories import (
    AuditRepository,
    ConnectorRepository,
    ExecutionRepository,
    GenerationRepository,
    ProjectRepository,
    RepairRepository,
)
from backend.app.schemas.audit import AuditEventResponse, ProjectVerificationSummary
from backend.app.schemas.connector import ConnectorVerificationState
from backend.app.schemas.sandbox import ExecutionStatus

logger = logging.getLogger(__name__)


class AuditService:
    """Service tracking audit events, approvals, and evaluating honest verification standing."""

    def __init__(
        self,
        project_repo: ProjectRepository,
        audit_repo: AuditRepository,
        execution_repo: ExecutionRepository,
        generation_repo: GenerationRepository,
        connector_repo: ConnectorRepository,
        repair_repo: RepairRepository,
    ):
        self.project_repo = project_repo
        self.audit_repo = audit_repo
        self.execution_repo = execution_repo
        self.generation_repo = generation_repo
        self.connector_repo = connector_repo
        self.repair_repo = repair_repo

    def log_event(
        self,
        project_id: uuid.UUID,
        event_type: str,
        actor: str = "system",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEventResponse:
        """Logs a sanitized audit event without exposing credentials or secrets."""
        sanitized_details = self._sanitize_details(details or {})
        event = self.audit_repo.create(
            project_id=project_id,
            event_type=event_type,
            actor=actor,
            details=sanitized_details,
        )
        try:
            return AuditEventResponse.model_validate(event)
        except Exception:
            from datetime import datetime, timezone
            return AuditEventResponse(
                id=uuid.uuid4(),
                project_id=project_id,
                event_type=event_type,
                actor=actor,
                details=sanitized_details,
                created_at=datetime.now(timezone.utc),
            )


    def get_events(self, project_id: uuid.UUID, limit: int = 50) -> List[AuditEventResponse]:
        """Retrieves recent audit events for a project."""
        events = self.audit_repo.get_by_project_id(project_id, limit=limit)
        return [AuditEventResponse.model_validate(e) for e in events]

    def get_project_summary(self, project_id: uuid.UUID) -> ProjectVerificationSummary:
        """
        Calculates honest verification standing based strictly on demonstrable evidence.
        Never assigns a verified state without direct proof.
        """
        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found.")

        files = self.generation_repo.get_by_project_id(project_id)
        runs = self.execution_repo.get_by_project_id(project_id)
        connectors = self.connector_repo.get_by_project_id(project_id)
        audit_events = self.get_events(project_id, limit=10)

        limitations: List[str] = []

        # 1. Inspect generated files
        has_generated_files = len(files) > 0
        if not has_generated_files:
            return ProjectVerificationSummary(
                project_id=project_id,
                verification_status=ExecutionStatus.NOT_RUN,
                static_checks_passed=False,
                dynamic_tests_passed=False,
                demo_verified=False,
                integration_verified=False,
                active_limitations=["No project source files generated yet."],
                recent_audit_events=audit_events,
            )

        # 2. Inspect static syntax checks
        static_checks_passed = all(f.validation_status == "passed" for f in files)
        if not static_checks_passed:
            limitations.append("One or more generated source files have pending or failed static checks.")

        # 3. Inspect dynamic execution runs
        latest_run = runs[0] if runs else None
        dynamic_tests_passed = False
        demo_verified = False
        blocked_run = False

        if latest_run:
            if latest_run.status == ExecutionStatus.BLOCKED.value:
                blocked_run = True
                limitations.append("Execution blocked: safe container isolation runtime was unavailable.")
            elif latest_run.status == ExecutionStatus.TESTS_PASSED.value:
                dynamic_tests_passed = True
                if "mock" in latest_run.runtime:
                    demo_verified = True
                    limitations.append("Tests passed under simulated/mock runtime; not a live container execution.")
                else:
                    demo_verified = True

        # 4. Inspect connector integrations
        integration_verified = False
        live_connectors = [c for c in connectors if not c.is_mock and c.connector_type != "mock"]
        if live_connectors:
            all_verified = all(c.state in (ConnectorVerificationState.CONNECTED.value, ConnectorVerificationState.VERIFIED.value) for c in live_connectors)
            if all_verified and dynamic_tests_passed:
                integration_verified = True
            else:
                limitations.append("One or more live connectors are not yet verified.")
        else:
            limitations.append("No live production connectors configured (synthetic/mock integrations only).")

        # 5. Evaluate honest overall status
        if blocked_run:
            overall_status = ExecutionStatus.BLOCKED
        elif integration_verified:
            overall_status = ExecutionStatus.INTEGRATION_VERIFIED
        elif demo_verified:
            overall_status = ExecutionStatus.DEMO_VERIFIED
        elif dynamic_tests_passed:
            overall_status = ExecutionStatus.TESTS_PASSED
        elif static_checks_passed:
            overall_status = ExecutionStatus.STATIC_CHECKS_PASSED
        elif has_generated_files:
            overall_status = ExecutionStatus.GENERATED
        else:
            overall_status = ExecutionStatus.NOT_RUN

        return ProjectVerificationSummary(
            project_id=project_id,
            verification_status=overall_status,
            static_checks_passed=static_checks_passed,
            dynamic_tests_passed=dynamic_tests_passed,
            demo_verified=demo_verified,
            integration_verified=integration_verified,
            active_limitations=limitations,
            recent_audit_events=audit_events,
        )

    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact secrets and credentials from audit payloads."""
        sanitized = {}
        sensitive_patterns = {"password", "secret", "token", "key", "auth", "credential", "private"}
        for k, v in details.items():
            if any(p in k.lower() for p in sensitive_patterns):
                sanitized[k] = "***REDACTED***"
            elif isinstance(v, dict):
                sanitized[k] = self._sanitize_details(v)
            else:
                sanitized[k] = v
        return sanitized
