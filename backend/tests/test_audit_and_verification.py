"""Unit tests for Chrysalis AI audit trail and honest verification standing service.

Verifies:
- Tamper-evident audit logging with secret redaction.
- Honest state accounting: GENERATED, STATIC_CHECKS_PASSED, TESTS_PASSED, DEMO_VERIFIED, INTEGRATION_VERIFIED, BLOCKED, NOT_RUN.
- Mock execution strictly prohibited from qualifying as live integration verified.
- Explicit documentation of active operational limitations.
"""

import uuid
import pytest
from unittest.mock import MagicMock

from backend.app.schemas.sandbox import ExecutionStatus
from backend.app.services.audit_service import AuditService


def test_audit_event_scrubs_secrets():
    """Verify audit logger redacts sensitive credentials from event payloads."""
    mock_audit_repo = MagicMock()
    service = AuditService(
        project_repo=MagicMock(),
        audit_repo=mock_audit_repo,
        execution_repo=MagicMock(),
        generation_repo=MagicMock(),
        connector_repo=MagicMock(),
        repair_repo=MagicMock(),
    )

    project_id = uuid.uuid4()
    details = {
        "user_email": "admin@example.com",
        "api_key": "AIzaSySuperSecretKey123",
        "nested": {"db_password": "supersecretpassword", "safe_param": 42},
    }

    service.log_event(project_id, "CONFIG_CHANGE", actor="developer", details=details)

    call_args = mock_audit_repo.create.call_args[1]
    saved_details = call_args["details"]

    assert saved_details["user_email"] == "admin@example.com"
    assert saved_details["api_key"] == "***REDACTED***"
    assert saved_details["nested"]["db_password"] == "***REDACTED***"
    assert saved_details["nested"]["safe_param"] == 42


def test_verification_summary_not_run_when_no_files():
    """Verify standing is NOT_RUN if no files have been generated."""
    project_id = uuid.uuid4()
    mock_gen_repo = MagicMock()
    mock_gen_repo.get_by_project_id.return_value = []

    service = AuditService(
        project_repo=MagicMock(),
        audit_repo=MagicMock(),
        execution_repo=MagicMock(),
        generation_repo=mock_gen_repo,
        connector_repo=MagicMock(),
        repair_repo=MagicMock(),
    )

    summary = service.get_project_summary(project_id)
    assert summary.verification_status == ExecutionStatus.NOT_RUN
    assert summary.static_checks_passed is False
    assert summary.dynamic_tests_passed is False


def test_verification_summary_demo_verified_for_mock_execution():
    """Verify mock sandbox execution achieves DEMO_VERIFIED but NOT INTEGRATION_VERIFIED."""
    project_id = uuid.uuid4()
    mock_proj_repo = MagicMock()
    mock_gen_repo = MagicMock()
    mock_exec_repo = MagicMock()
    mock_conn_repo = MagicMock()
    mock_audit_repo = MagicMock()

    mock_db_file = MagicMock(validation_status="passed")
    mock_gen_repo.get_by_project_id.return_value = [mock_db_file]

    mock_run = MagicMock(
        status=ExecutionStatus.TESTS_PASSED.value,
        runtime="mock_sandbox",
    )
    mock_exec_repo.get_by_project_id.return_value = [mock_run]
    mock_conn_repo.get_by_project_id.return_value = []
    mock_audit_repo.get_by_project_id.return_value = []

    service = AuditService(
        project_repo=mock_proj_repo,
        audit_repo=mock_audit_repo,
        execution_repo=mock_exec_repo,
        generation_repo=mock_gen_repo,
        connector_repo=mock_conn_repo,
        repair_repo=MagicMock(),
    )

    summary = service.get_project_summary(project_id)
    assert summary.verification_status == ExecutionStatus.DEMO_VERIFIED
    assert summary.static_checks_passed is True
    assert summary.dynamic_tests_passed is True
    assert summary.demo_verified is True
    # Strict hackathon rule: Mock execution must never count as verified live integration
    assert summary.integration_verified is False
    assert any("simulated/mock runtime" in lim for lim in summary.active_limitations)


def test_verification_summary_blocked_when_isolation_fails():
    """Verify status is BLOCKED when container runtime fails closed."""
    project_id = uuid.uuid4()
    mock_gen_repo = MagicMock()
    mock_exec_repo = MagicMock()

    mock_db_file = MagicMock(validation_status="passed")
    mock_gen_repo.get_by_project_id.return_value = [mock_db_file]

    mock_blocked_run = MagicMock(
        status=ExecutionStatus.BLOCKED.value,
        runtime="fail_closed",
    )
    mock_exec_repo.get_by_project_id.return_value = [mock_blocked_run]

    service = AuditService(
        project_repo=MagicMock(),
        audit_repo=MagicMock(),
        execution_repo=mock_exec_repo,
        generation_repo=mock_gen_repo,
        connector_repo=MagicMock(),
        repair_repo=MagicMock(),
    )

    summary = service.get_project_summary(project_id)
    assert summary.verification_status == ExecutionStatus.BLOCKED
    assert any("safe container isolation runtime was unavailable" in lim for lim in summary.active_limitations)
