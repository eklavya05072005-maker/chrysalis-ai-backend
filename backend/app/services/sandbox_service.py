"""Restricted execution sandbox service for Chrysalis AI.

Enforces strong container isolation (Docker with --network none, non-root,
memory and CPU quotas, read-only/ephemeral mounts, strict timeout) or
fails closed with BLOCKED/NOT_RUN status if a secure container runtime
is unavailable. Raw host subprocess execution is strictly forbidden.
"""

from __future__ import annotations
import logging
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.app.ai.codegen_engine import validate_safe_output_path, verify_no_secrets
from backend.app.core.config import Settings, get_settings
from backend.app.schemas.sandbox import (
    ExecutionRunRequest,
    ExecutionRunResult,
    ExecutionStatus,
    SandboxRuntimeType,
)
from backend.app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

# Configurable fallback docker image for python project execution
SANDBOX_DOCKER_IMAGE = os.environ.get("CHRYSALIS_SANDBOX_IMAGE", "python:3.11-slim")


class SandboxService:
    """Dedicated service for isolated execution of generated project code."""

    def __init__(
        self,
        storage_service: Optional[StorageService] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.storage_service = storage_service or StorageService(self.settings.data_path)

    @staticmethod
    def is_docker_available() -> Tuple[bool, str]:
        """Check whether the Docker daemon is accessible and responsive."""
        try:
            res = subprocess.run(
                ["docker", "info", "--format", "{{.ServerVersion}}"],
                capture_output=True,
                text=True,
                timeout=4,
            )
            if res.returncode == 0 and res.stdout.strip():
                return True, res.stdout.strip()
            return False, res.stderr.strip() or "Docker daemon not running"
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as exc:
            return False, str(exc)

    @staticmethod
    def is_image_available(image_name: str) -> bool:
        """Check whether the designated sandbox container image is available locally."""
        try:
            res = subprocess.run(
                ["docker", "image", "inspect", image_name],
                capture_output=True,
                text=True,
                timeout=4,
            )
            return res.returncode == 0
        except Exception:
            return False

    def execute_project(
        self,
        request: ExecutionRunRequest,
        generated_files_dict: Optional[Dict[str, str]] = None,
    ) -> ExecutionRunResult:
        """
        Execute generated project code inside a restricted sandbox.
        
        If a safe container runtime is unavailable and runtime_override != MOCK,
        it fails closed with status=BLOCKED per security policy.
        """
        run_id = uuid.uuid4()
        start_time = time.time()
        checks_performed: List[str] = [
            "path_traversal_validation",
            "secrets_scanning",
        ]

        # 1. Resolve files to execute
        files_to_run: Dict[str, str] = {}
        if generated_files_dict is not None:
            files_to_run = generated_files_dict
        else:
            # Read from storage
            gen_dir = self.storage_service.base_dir / "generated" / str(request.project_id)
            if not gen_dir.exists():
                return ExecutionRunResult(
                    run_id=run_id,
                    project_id=request.project_id,
                    status=ExecutionStatus.NOT_RUN,
                    runtime="none",
                    exit_code=None,
                    stdout="",
                    stderr="No generated files found on disk for this project.",
                    elapsed_time_seconds=0.0,
                    timed_out=False,
                    resource_limit_hit=False,
                    network_isolated=True,
                    checks_performed=checks_performed,
                    sandbox_cleaned_up=True,
                    message="Project code not found for execution.",
                )
            for path in gen_dir.rglob("*"):
                if path.is_file():
                    rel = path.relative_to(gen_dir).as_posix()
                    try:
                        files_to_run[rel] = path.read_text(encoding="utf-8")
                    except Exception:
                        pass

        if not files_to_run:
            return ExecutionRunResult(
                run_id=run_id,
                project_id=request.project_id,
                status=ExecutionStatus.NOT_RUN,
                runtime="none",
                exit_code=None,
                stdout="",
                stderr="Generated project contains zero files to execute.",
                elapsed_time_seconds=0.0,
                timed_out=False,
                resource_limit_hit=False,
                network_isolated=True,
                checks_performed=checks_performed,
                sandbox_cleaned_up=True,
                message="Cannot execute empty project.",
            )

        # 2. Security validation: path traversal and secret scanning
        for rel_path, content in files_to_run.items():
            # Validate safe relative path
            try:
                validate_safe_output_path(Path("dummy_root"), rel_path)
            except ValueError as ve:
                return ExecutionRunResult(
                    run_id=run_id,
                    project_id=request.project_id,
                    status=ExecutionStatus.BLOCKED,
                    runtime="security_guard",
                    exit_code=None,
                    stdout="",
                    stderr=f"Security violation: path traversal detected ({ve})",
                    elapsed_time_seconds=time.time() - start_time,
                    timed_out=False,
                    resource_limit_hit=False,
                    network_isolated=True,
                    checks_performed=checks_performed,
                    sandbox_cleaned_up=True,
                    message=f"Execution blocked: unsafe file path '{rel_path}'.",
                )
            # Scan for secrets
            try:
                verify_no_secrets(content, rel_path)
            except ValueError as se:
                return ExecutionRunResult(
                    run_id=run_id,
                    project_id=request.project_id,
                    status=ExecutionStatus.BLOCKED,
                    runtime="security_guard",
                    exit_code=None,
                    stdout="",
                    stderr=f"Security violation: hardcoded secret detected ({se})",
                    elapsed_time_seconds=time.time() - start_time,
                    timed_out=False,
                    resource_limit_hit=False,
                    network_isolated=True,
                    checks_performed=checks_performed,
                    sandbox_cleaned_up=True,
                    message=f"Execution blocked: suspected hardcoded secret in '{rel_path}'.",
                )

        checks_performed.append("security_scans_passed")

        # 3. Determine runtime mode
        if request.runtime_override == SandboxRuntimeType.MOCK or self.settings.is_testing:
            if request.runtime_override != SandboxRuntimeType.FAIL_CLOSED and request.runtime_override != SandboxRuntimeType.DOCKER:
                return self._execute_mock(run_id, request, files_to_run, checks_performed, start_time)

        if request.runtime_override == SandboxRuntimeType.FAIL_CLOSED:
            return ExecutionRunResult(
                run_id=run_id,
                project_id=request.project_id,
                status=ExecutionStatus.BLOCKED,
                runtime="fail_closed",
                exit_code=None,
                stdout="",
                stderr="Container runtime unavailable or forced fail-closed.",
                elapsed_time_seconds=time.time() - start_time,
                timed_out=False,
                resource_limit_hit=False,
                network_isolated=True,
                checks_performed=checks_performed,
                sandbox_cleaned_up=True,
                message="Execution blocked: safe container isolation runtime unavailable. Host subprocess execution prohibited.",
            )

        # 4. Check Docker container runtime availability
        docker_ok, docker_msg = self.is_docker_available()
        if not docker_ok:
            logger.warning("Docker unavailable for sandbox execution: %s", docker_msg)
            return ExecutionRunResult(
                run_id=run_id,
                project_id=request.project_id,
                status=ExecutionStatus.BLOCKED,
                runtime="fail_closed",
                exit_code=None,
                stdout="",
                stderr=f"Docker runtime unavailable: {docker_msg}",
                elapsed_time_seconds=time.time() - start_time,
                timed_out=False,
                resource_limit_hit=False,
                network_isolated=True,
                checks_performed=checks_performed,
                sandbox_cleaned_up=True,
                message="Execution blocked: safe container isolation runtime unavailable. Host execution prohibited per security policy.",
            )

        image_available = self.is_image_available(SANDBOX_DOCKER_IMAGE)
        if not image_available:
            logger.warning("Designated sandbox image %s not found locally", SANDBOX_DOCKER_IMAGE)
            return ExecutionRunResult(
                run_id=run_id,
                project_id=request.project_id,
                status=ExecutionStatus.BLOCKED,
                runtime="fail_closed",
                exit_code=None,
                stdout="",
                stderr=f"Sandbox container image '{SANDBOX_DOCKER_IMAGE}' not found locally.",
                elapsed_time_seconds=time.time() - start_time,
                timed_out=False,
                resource_limit_hit=False,
                network_isolated=True,
                checks_performed=checks_performed,
                sandbox_cleaned_up=True,
                message=f"Execution blocked: sandbox container image '{SANDBOX_DOCKER_IMAGE}' not found locally.",
            )

        # 5. Execute in isolated Docker container
        return self._execute_docker(run_id, request, files_to_run, checks_performed, start_time)

    def _execute_mock(
        self,
        run_id: uuid.UUID,
        request: ExecutionRunRequest,
        files: Dict[str, str],
        checks: List[str],
        start_time: float,
    ) -> ExecutionRunResult:
        """Deterministic mock execution for offline testing and demonstration."""
        checks.append("mock_isolation_simulated")
        checks.append("test_assertion_evaluation")

        # Check if any test file contains an intentional failure marker
        has_failure = any(
            "def test_failing" in content or "assert False" in content or "raise AssertionError" in content
            for content in files.values()
        )

        elapsed = min(0.05, request.timeout_seconds)

        if has_failure:
            return ExecutionRunResult(
                run_id=run_id,
                project_id=request.project_id,
                status=ExecutionStatus.FAILED,
                runtime="mock_sandbox",
                exit_code=1,
                stdout="test_sample.py::test_failing FAILED\n\n=== FAILURES ===\nassert False",
                stderr="AssertionError: Condition failed in generated test",
                elapsed_time_seconds=elapsed,
                timed_out=False,
                resource_limit_hit=False,
                network_isolated=not request.network_enabled,
                checks_performed=checks,
                sandbox_cleaned_up=True,
                message="Deterministic mock test execution completed with failed test assertions.",
            )

        return ExecutionRunResult(
            run_id=run_id,
            project_id=request.project_id,
            status=ExecutionStatus.TESTS_PASSED,
            runtime="mock_sandbox",
            exit_code=0,
            stdout="test_sample.py::test_workflow PASSED\n\n=== 1 passed in 0.04s ===",
            stderr="",
            elapsed_time_seconds=elapsed,
            timed_out=False,
            resource_limit_hit=False,
            network_isolated=not request.network_enabled,
            checks_performed=checks,
            sandbox_cleaned_up=True,
            message="Deterministic mock test execution passed all assertions under simulated isolation.",
        )

    def _execute_docker(
        self,
        run_id: uuid.UUID,
        request: ExecutionRunRequest,
        files: Dict[str, str],
        checks: List[str],
        start_time: float,
    ) -> ExecutionRunResult:
        """Execute inside Docker container with least-privilege, network isolation, and limits."""
        temp_dir = tempfile.mkdtemp(prefix="chrysalis_sandbox_")
        container_name = f"chrysalis_run_{run_id.hex[:12]}"
        checks.append("container_workspace_created")

        try:
            # Write only approved files into the temporary staging workspace
            for rel_path, content in files.items():
                dest = Path(temp_dir) / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")

            # Construct Docker execution command with least privilege
            cmd = [
                "docker", "run",
                "--name", container_name,
                "--rm",
                # Network isolation: strictly none by default
                "--network", "none" if not request.network_enabled else "bridge",
                # Resource limits
                "--memory", f"{request.memory_limit_mb}m",
                "--cpus", str(request.cpu_quota),
                # Non-root user
                "--user", "1000:1000",
                # Ephemeral volume mount only
                "-v", f"{temp_dir}:/workspace:rw",
                "-w", "/workspace",
                # Minimal environment (no host credentials leaked)
                "-e", "PYTHONDONTWRITEBYTECODE=1",
                "-e", "PYTHONUNBUFFERED=1",
                "-e", "PATH=/usr/local/bin:/usr/bin:/bin",
                SANDBOX_DOCKER_IMAGE,
                "sh", "-c", request.test_command,
            ]

            checks.append("docker_container_spawned")
            checks.append("network_none_enforced" if not request.network_enabled else "network_permitted")

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds,
            )

            elapsed = time.time() - start_time
            exit_code = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr
            timed_out = False
            resource_limit_hit = (exit_code == 137)  # OOM / SIGKILL

            if exit_code == 0:
                status = ExecutionStatus.TESTS_PASSED
                msg = "Tests executed and passed successfully inside isolated container."
            else:
                status = ExecutionStatus.FAILED
                msg = f"Execution returned non-zero exit code ({exit_code})."

            checks.append("container_exit_captured")

            return ExecutionRunResult(
                run_id=run_id,
                project_id=request.project_id,
                status=status,
                runtime="docker",
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                elapsed_time_seconds=elapsed,
                timed_out=timed_out,
                resource_limit_hit=resource_limit_hit,
                network_isolated=not request.network_enabled,
                checks_performed=checks,
                sandbox_cleaned_up=True,
                message=msg,
            )

        except subprocess.TimeoutExpired as te:
            # Kill running container explicitly if timed out
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, timeout=5)
            elapsed = time.time() - start_time
            checks.append("timeout_interrupted")
            return ExecutionRunResult(
                run_id=run_id,
                project_id=request.project_id,
                status=ExecutionStatus.FAILED,
                runtime="docker",
                exit_code=None,
                stdout=te.stdout or "" if isinstance(te.stdout, str) else "",
                stderr=f"Execution timed out after {request.timeout_seconds} seconds.",
                elapsed_time_seconds=elapsed,
                timed_out=True,
                resource_limit_hit=False,
                network_isolated=not request.network_enabled,
                checks_performed=checks,
                sandbox_cleaned_up=True,
                message=f"Execution exceeded configured timeout ({request.timeout_seconds}s) and was terminated.",
            )

        except Exception as exc:
            logger.error("Sandbox execution error: %s", exc)
            return ExecutionRunResult(
                run_id=run_id,
                project_id=request.project_id,
                status=ExecutionStatus.FAILED,
                runtime="docker",
                exit_code=None,
                stdout="",
                stderr=str(exc),
                elapsed_time_seconds=time.time() - start_time,
                timed_out=False,
                resource_limit_hit=False,
                network_isolated=not request.network_enabled,
                checks_performed=checks,
                sandbox_cleaned_up=True,
                message=f"Execution failed due to runtime exception: {exc}",
            )

        finally:
            # Clean up temporary staging workspace on host
            shutil.rmtree(temp_dir, ignore_errors=True)
