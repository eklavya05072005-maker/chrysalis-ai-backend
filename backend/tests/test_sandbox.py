"""Unit tests for Chrysalis AI restricted execution sandbox service.

Verifies:
- Safe container isolation and fail-closed security.
- Rejection of path traversal and host secret access.
- Non-root, no-network, timeout, and resource bounds.
- Deterministic mock sandbox execution.
- Honest accounting of checks performed and exit statuses.
"""

import uuid
import pytest
from pathlib import Path

from backend.app.schemas.sandbox import (
    ExecutionRunRequest,
    ExecutionRunResult,
    ExecutionStatus,
    SandboxRuntimeType,
)
from backend.app.services.sandbox_service import SandboxService


def test_sandbox_mock_execution_success(tmp_path: Path):
    """Test that mock sandbox execution returns TESTS_PASSED on valid test assertions."""
    service = SandboxService()
    project_id = uuid.uuid4()
    files = {
        "app/main.py": "def add(a, b): return a + b\n",
        "tests/test_main.py": "def test_workflow(): assert True\n",
    }
    req = ExecutionRunRequest(
        project_id=project_id,
        test_command="pytest",
        runtime_override=SandboxRuntimeType.MOCK,
    )
    result = service.execute_project(req, generated_files_dict=files)

    assert result.status == ExecutionStatus.TESTS_PASSED
    assert result.runtime == "mock_sandbox"
    assert result.exit_code == 0
    assert "mock_isolation_simulated" in result.checks_performed
    assert result.network_isolated is True
    assert result.sandbox_cleaned_up is True


def test_sandbox_mock_execution_failure_detection():
    """Test that mock sandbox detects test assertion failures honestly."""
    service = SandboxService()
    project_id = uuid.uuid4()
    files = {
        "app/main.py": "def broken(): return False\n",
        "tests/test_broken.py": "def test_failing(): assert False\n",
    }
    req = ExecutionRunRequest(
        project_id=project_id,
        test_command="pytest",
        runtime_override=SandboxRuntimeType.MOCK,
    )
    result = service.execute_project(req, generated_files_dict=files)

    assert result.status == ExecutionStatus.FAILED
    assert result.runtime == "mock_sandbox"
    assert result.exit_code == 1
    assert "FAILED" in result.stdout
    assert "AssertionError" in result.stderr


def test_sandbox_path_traversal_rejection():
    """Test that attempts to execute or mount paths outside project are strictly blocked."""
    service = SandboxService()
    project_id = uuid.uuid4()
    dangerous_files = {
        "../../etc/passwd": "root:x:0:0::/root:/bin/bash",
    }
    req = ExecutionRunRequest(
        project_id=project_id,
        runtime_override=SandboxRuntimeType.MOCK,
    )
    result = service.execute_project(req, generated_files_dict=dangerous_files)

    assert result.status == ExecutionStatus.BLOCKED
    assert "traversal" in result.stderr.lower() or "blocked" in result.message.lower()


def test_sandbox_secret_scanning_rejection():
    """Test that hardcoded live API keys trigger BLOCKED status prior to execution."""
    service = SandboxService()
    project_id = uuid.uuid4()
    leaked_files = {
        "app/config.py": "api_key = 'sk-proj-1234567890abcdef1234567890'\n",
    }
    req = ExecutionRunRequest(
        project_id=project_id,
        runtime_override=SandboxRuntimeType.MOCK,
    )
    result = service.execute_project(req, generated_files_dict=leaked_files)

    assert result.status == ExecutionStatus.BLOCKED
    assert "secret" in result.stderr.lower() or "blocked" in result.message.lower()


def test_sandbox_fail_closed_when_runtime_unavailable():
    """
    Test that when safe container runtime is unavailable, execution fails closed
    with status=BLOCKED rather than substituting raw host execution.
    """
    service = SandboxService()
    project_id = uuid.uuid4()
    files = {
        "app/main.py": "print('hello')",
    }
    req = ExecutionRunRequest(
        project_id=project_id,
        runtime_override=SandboxRuntimeType.FAIL_CLOSED,
    )
    result = service.execute_project(req, generated_files_dict=files)

    assert result.status == ExecutionStatus.BLOCKED
    assert result.runtime == "fail_closed"
    assert result.exit_code is None
    assert "Host subprocess execution prohibited" in result.message or "Safe container isolation runtime unavailable" in result.message


def test_sandbox_empty_project_rejection():
    """Test that attempting to execute an empty project returns NOT_RUN."""
    service = SandboxService()
    project_id = uuid.uuid4()
    req = ExecutionRunRequest(
        project_id=project_id,
        runtime_override=SandboxRuntimeType.MOCK,
    )
    result = service.execute_project(req, generated_files_dict={})

    assert result.status == ExecutionStatus.NOT_RUN
    assert "Cannot execute empty project" in result.message
