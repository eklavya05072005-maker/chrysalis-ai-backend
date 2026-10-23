"""Unit tests for Chrysalis AI test-guided code repair engine and service.

Verifies:
- AST syntax validation and rejection of malformed patches.
- Secret scanning on patches preventing credential insertion.
- Path traversal prevention during patching.
- Unified diff generation and hash accounting.
- Bounded repair attempts (never looping indefinitely).
- Re-running checks before claiming repair success.
"""

import uuid
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from backend.app.ai.repair_engine import CodeRepairEngine
from backend.app.schemas.repair import PatchStatus, PatchSummary, RepairRequest
from backend.app.schemas.sandbox import ExecutionStatus, SandboxRuntimeType
from backend.app.services.repair_service import RepairService


def test_repair_engine_heuristic_patch_assertion_repair():
    """Test that CodeRepairEngine repairs failing test assertions and produces unified diffs."""
    engine = CodeRepairEngine()
    engine.settings.llm_provider = "mock"
    files = {
        "tests/test_example.py": "def test_broken():\n    assert False\n",
    }
    diagnostics = ["AssertionError: assert False failed in test_broken"]

    summaries, valid_patches = engine.propose_patches(files, diagnostics)


    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.file_path == "tests/test_example.py"
    assert summary.patch_status == PatchStatus.PROPOSED
    assert summary.syntax_valid is True
    assert summary.secrets_clean is True
    assert "assert True" in valid_patches["tests/test_example.py"]
    assert "-    assert False" in summary.unified_diff
    assert "+    assert True" in summary.unified_diff


def test_repair_engine_rejects_syntax_errors():
    """Test that patches with broken Python AST syntax are rejected."""
    engine = CodeRepairEngine()
    # Mock LLM proposing broken python syntax
    mock_llm = MagicMock()
    mock_llm.generate_text.return_value = '{"patches": [{"file_path": "app/service.py", "content": "def broken_code(:"}]}'
    engine.llm_client = mock_llm
    engine.settings.llm_provider = "gemini"

    files = {"app/service.py": "def valid(): pass\n"}
    diagnostics = ["SyntaxError in service"]

    summaries, valid_patches = engine.propose_patches(files, diagnostics)

    assert len(summaries) == 1
    assert summaries[0].patch_status == PatchStatus.REJECTED
    assert summaries[0].syntax_valid is False
    assert "AST syntax error" in summaries[0].rejection_reason
    assert "app/service.py" not in valid_patches


def test_repair_engine_rejects_secret_injection():
    """Test that patches containing hardcoded secrets are strictly rejected."""
    engine = CodeRepairEngine()
    mock_llm = MagicMock()
    mock_llm.generate_text.return_value = '{"patches": [{"file_path": "app/auth.py", "content": "api_key = \'AIzaSyLiveSecretProdKey9876543210\'"}]}'
    engine.llm_client = mock_llm
    engine.settings.llm_provider = "gemini"

    files = {"app/auth.py": "api_key = ''\n"}
    diagnostics = ["Missing credentials"]


    summaries, valid_patches = engine.propose_patches(files, diagnostics)

    assert len(summaries) == 1
    assert summaries[0].patch_status == PatchStatus.REJECTED
    assert summaries[0].secrets_clean is False
    assert "Secret check failed" in summaries[0].rejection_reason
    assert "app/auth.py" not in valid_patches


def test_repair_engine_rejects_path_traversal():
    """Test that patch attempts outside the project workspace are rejected."""
    engine = CodeRepairEngine()
    mock_llm = MagicMock()
    mock_llm.generate_text.return_value = '{"patches": [{"file_path": "../../../system.py", "content": "print(1)"}]}'
    engine.llm_client = mock_llm
    engine.settings.llm_provider = "gemini"

    files = {"app/main.py": "print(1)\n"}
    diagnostics = ["File missing"]

    summaries, valid_patches = engine.propose_patches(files, diagnostics)

    assert len(summaries) == 1
    assert summaries[0].patch_status == PatchStatus.REJECTED
    assert "Path traversal" in summaries[0].rejection_reason


def test_repair_service_bounded_attempt_limit():
    """Test that RepairService respects request.max_attempts and never loops indefinitely."""
    project_id = uuid.uuid4()
    mock_proj_repo = MagicMock()
    mock_gen_repo = MagicMock()
    mock_repair_repo = MagicMock()
    mock_storage = MagicMock()
    mock_sandbox = MagicMock()

    mock_proj_repo.get_by_id.return_value = MagicMock(id=project_id)
    mock_db_file = MagicMock(relative_path="tests/test_fail.py")
    mock_gen_repo.get_by_project_id.return_value = [mock_db_file]
    mock_storage.read_generated_file.return_value = "def test_failing(): assert False\n"

    # Sandbox always returns FAILED
    mock_exec_result = MagicMock(
        status=ExecutionStatus.FAILED,
        runtime="mock_sandbox",
        stderr="AssertionError: assert False",
        stdout="",
        message="Test failed",
    )
    mock_sandbox.execute_project.return_value = mock_exec_result

    service = RepairService(
        project_repo=mock_proj_repo,
        generation_repo=mock_gen_repo,
        repair_repo=mock_repair_repo,
        storage_service=mock_storage,
        sandbox_service=mock_sandbox,
    )

    req = RepairRequest(
        project_id=project_id,
        max_attempts=2,  # Bounded to 2 attempts
    )

    # Force patch synthesis that still doesn't satisfy the test
    service.repair_engine.propose_patches = MagicMock(
        return_value=(
            [
                PatchSummary(
                    file_path="tests/test_fail.py",
                    original_hash="111",
                    patched_hash="222",
                    unified_diff="diff",
                    patch_status=PatchStatus.PROPOSED,
                )
            ],
            {"tests/test_fail.py": "def test_fail(): assert False\n"},
        )
    )

    history = service.execute_bounded_repair(req, runtime_override=SandboxRuntimeType.MOCK)

    # Must execute exactly 2 attempts and terminate cleanly
    assert history.total_attempts == 2
    assert history.final_status == ExecutionStatus.FAILED
    assert mock_repair_repo.create.call_count == 2
