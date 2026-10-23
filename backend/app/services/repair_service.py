"""Service coordinating test-guided bounded code repair workflow.

Strictly enforces bounded attempts (default 1), snapshotting, AST validation,
secret scanning, re-running of real validation checks, and records all
patches and attempt history into the database.
"""

from __future__ import annotations
import logging
import uuid
from typing import Dict, List, Optional

from backend.app.ai.repair_engine import CodeRepairEngine
from backend.app.ai.validator import OutputValidator
from backend.app.core.config import Settings, get_settings
from backend.app.repositories import (
    GenerationRepository,
    ProjectRepository,
    RepairRepository,
)
from backend.app.schemas.common import ArchitectureArchetype
from backend.app.schemas.codegen import CodegenManifest, GeneratedFile

from backend.app.schemas.repair import (
    PatchStatus,
    PatchSummary,
    RepairAttemptResult,
    RepairHistoryResponse,
    RepairRequest,
)
from backend.app.schemas.sandbox import (
    ExecutionRunRequest,
    ExecutionStatus,
    SandboxRuntimeType,
)
from backend.app.services.sandbox_service import SandboxService
from backend.app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class RepairService:
    """Orchestrates bounded test-guided code repair workflows."""

    def __init__(
        self,
        project_repo: ProjectRepository,
        generation_repo: GenerationRepository,
        repair_repo: RepairRepository,
        storage_service: StorageService,
        sandbox_service: SandboxService,
        repair_engine: Optional[CodeRepairEngine] = None,
        validator: Optional[OutputValidator] = None,
        settings: Optional[Settings] = None,
    ):
        self.project_repo = project_repo
        self.generation_repo = generation_repo
        self.repair_repo = repair_repo
        self.storage_service = storage_service
        self.sandbox_service = sandbox_service
        self.settings = settings or get_settings()
        self.repair_engine = repair_engine or CodeRepairEngine(settings=self.settings)
        self.validator = validator or OutputValidator(settings=self.settings)

    def execute_bounded_repair(
        self,
        request: RepairRequest,
        runtime_override: Optional[SandboxRuntimeType] = None,
    ) -> RepairHistoryResponse:
        """
        Executes bounded code repair loop on a project's generated source files.
        Never loops indefinitely; respects request.max_attempts (default 1).
        """
        project = self.project_repo.get_by_id(request.project_id)
        if not project:
            raise ValueError(f"Project {request.project_id} not found.")

        # Read current generated files from disk/storage
        db_files = self.generation_repo.get_by_project_id(request.project_id)
        current_files: Dict[str, str] = {}
        for db_file in db_files:
            try:
                content = self.storage_service.read_generated_file(request.project_id, db_file.relative_path)
                current_files[db_file.relative_path] = content
            except Exception:
                pass

        if not current_files:
            raise ValueError("No generated files found to repair.")

        attempts_results: List[RepairAttemptResult] = []
        total_applied = 0
        current_status = ExecutionStatus.FAILED

        # Bound iterations strictly to max_attempts (default 1)
        max_iters = min(max(1, request.max_attempts), 3)

        for attempt_idx in range(1, max_iters + 1):
            diagnostics: List[str] = []
            checks_executed: List[str] = []

            # 1. Run static validation checks (Module G)
            if request.include_static_checks:
                manifest_files = [
                    GeneratedFile(
                        relative_path=p,
                        language="python" if p.endswith(".py") else "text",
                        content=c,
                        purpose="Project file for repair evaluation",
                    )
                    for p, c in current_files.items()
                ]
                manifest = CodegenManifest(
                    project_name="Repair Evaluation",
                    archetype=ArchitectureArchetype.CONSERVATIVE,
                    completeness_notes="Repair manifest evaluation",
                    files=manifest_files,
                )

                static_rep = self.validator.validate_manifest_structure(manifest)
                syntax_rep = self.validator.validate_python_syntax(manifest)
                checks_executed.append("static_validation")


                if static_rep[0].status.value != "passed":
                    diagnostics.append(f"Static manifest check failed: {static_rep[0].message}")
                if syntax_rep[0].status.value != "passed":
                    diagnostics.append(f"Static syntax check failed: {syntax_rep[0].message}")

            # 2. Run sandbox test execution
            if request.include_test_execution:
                run_req = ExecutionRunRequest(
                    project_id=request.project_id,
                    test_command="pytest",
                    runtime_override=runtime_override or (SandboxRuntimeType.MOCK if self.settings.is_testing else None),
                )
                exec_result = self.sandbox_service.execute_project(run_req, generated_files_dict=current_files)
                checks_executed.append(f"sandbox_test_run_{exec_result.runtime}")

                if exec_result.status != ExecutionStatus.TESTS_PASSED:
                    diagnostics.append(f"Test failure: {exec_result.stderr or exec_result.stdout or exec_result.message}")
                else:
                    current_status = ExecutionStatus.TESTS_PASSED

            # If no diagnostics collected, everything already passes!
            if not diagnostics:
                current_status = ExecutionStatus.TESTS_PASSED
                break

            # 3. Propose patches using repair engine
            patch_summaries, valid_patches = self.repair_engine.propose_patches(current_files, diagnostics)

            # If no patches could be proposed, record failure and break
            if not valid_patches:
                attempt_res = RepairAttemptResult(
                    attempt_number=attempt_idx,
                    initial_status=ExecutionStatus.FAILED,
                    failure_diagnostics=diagnostics,
                    patches=patch_summaries,
                    rerun_status=ExecutionStatus.FAILED,
                    checks_rerun=checks_executed,
                    success=False,
                    summary="No valid patches could be synthesized for the collected diagnostics.",
                )
                attempts_results.append(attempt_res)
                self.repair_repo.create(
                    project_id=request.project_id,
                    attempt_number=attempt_idx,
                    initial_status="failed",
                    failure_diagnostics=diagnostics,
                    patches=[p.model_dump() for p in patch_summaries],
                    rerun_status="failed",
                    checks_rerun=checks_executed,
                    success=False,
                    summary=attempt_res.summary,
                )
                break

            # 4. Apply valid patches to disk/storage
            applied_summaries: List[PatchSummary] = []
            for patch in patch_summaries:
                if patch.patch_status == PatchStatus.PROPOSED:
                    # Apply to current memory map and disk
                    current_files[patch.file_path] = valid_patches[patch.file_path]
                    self.storage_service.save_generated_file(
                        project_id=request.project_id,
                        relative_path=patch.file_path,
                        content=valid_patches[patch.file_path],
                    )
                    patch.patch_status = PatchStatus.APPLIED
                    total_applied += 1
                applied_summaries.append(patch)

            # 5. Rerun verification checks to honestly test the patched files
            rerun_diagnostics: List[str] = []
            checks_rerun: List[str] = []

            # Rerun static checks
            manifest_files = [
                GeneratedFile(
                    relative_path=p,
                    language="python" if p.endswith(".py") else "text",
                    content=c,
                    purpose="Repaired file",
                )
                for p, c in current_files.items()
            ]
            recheck_manifest = CodegenManifest(
                project_name="Repaired Project",
                archetype=ArchitectureArchetype.CONSERVATIVE,
                completeness_notes="Repaired manifest recheck",
                files=manifest_files,
            )

            syntax_rep = self.validator.validate_python_syntax(recheck_manifest)
            checks_rerun.append("rerun_static_syntax")

            if syntax_rep[0].status.value != "passed":
                rerun_diagnostics.append(f"Syntax recheck failed: {syntax_rep[0].message}")

            # Rerun sandbox execution
            run_req = ExecutionRunRequest(
                project_id=request.project_id,
                test_command="pytest",
                runtime_override=runtime_override or (SandboxRuntimeType.MOCK if self.settings.is_testing else None),
            )
            rerun_exec = self.sandbox_service.execute_project(run_req, generated_files_dict=current_files)
            checks_rerun.append(f"rerun_sandbox_{rerun_exec.runtime}")

            if rerun_exec.status != ExecutionStatus.TESTS_PASSED:
                rerun_diagnostics.append(f"Rerun test failure: {rerun_exec.stderr or rerun_exec.stdout}")
                attempt_success = False
                attempt_status = ExecutionStatus.FAILED
            else:
                attempt_success = (len(rerun_diagnostics) == 0)
                attempt_status = ExecutionStatus.TESTS_PASSED if attempt_success else ExecutionStatus.FAILED

            # If rerun succeeded, mark applied patches as VERIFIED
            if attempt_success:
                for p in applied_summaries:
                    if p.patch_status == PatchStatus.APPLIED:
                        p.patch_status = PatchStatus.VERIFIED
                current_status = ExecutionStatus.TESTS_PASSED
                summary_msg = f"Repair attempt {attempt_idx} succeeded: applied {len(valid_patches)} patch(es) and passed all rerun verification checks."
            else:
                current_status = ExecutionStatus.FAILED
                summary_msg = f"Repair attempt {attempt_idx} applied {len(valid_patches)} patch(es) but rerun verification checks failed."

            attempt_res = RepairAttemptResult(
                attempt_number=attempt_idx,
                initial_status=ExecutionStatus.FAILED,
                failure_diagnostics=diagnostics,
                patches=applied_summaries,
                rerun_status=attempt_status,
                checks_rerun=checks_rerun,
                success=attempt_success,
                summary=summary_msg,
            )
            attempts_results.append(attempt_res)

            # Persist in DB
            self.repair_repo.create(
                project_id=request.project_id,
                attempt_number=attempt_idx,
                initial_status="failed",
                failure_diagnostics=diagnostics,
                patches=[p.model_dump() for p in applied_summaries],
                rerun_status=attempt_status.value,
                checks_rerun=checks_rerun,
                success=attempt_success,
                summary=summary_msg,
            )

            # Stop if repaired
            if attempt_success:
                break

        # Regenerate package zip after repairs
        if total_applied > 0:
            self.storage_service.create_zip_package(request.project_id)

        return RepairHistoryResponse(
            project_id=request.project_id,
            total_attempts=len(attempts_results),
            final_status=current_status,
            total_patches_applied=total_applied,
            attempts=attempts_results,
        )

    def get_repair_history(self, project_id: uuid.UUID) -> RepairHistoryResponse:
        """Retrieves past repair attempt history for a project."""
        logs = self.repair_repo.get_by_project_id(project_id)
        attempts = []
        total_patches = 0
        final_status = ExecutionStatus.NOT_RUN

        for log in reversed(logs):
            patch_objs = [PatchSummary(**p) for p in (log.patches or [])]
            for p in patch_objs:
                if p.patch_status in (PatchStatus.APPLIED, PatchStatus.VERIFIED):
                    total_patches += 1

            attempts.append(
                RepairAttemptResult(
                    attempt_number=log.attempt_number,
                    initial_status=ExecutionStatus(log.initial_status),
                    failure_diagnostics=log.failure_diagnostics or [],
                    patches=patch_objs,
                    rerun_status=ExecutionStatus(log.rerun_status),
                    checks_rerun=log.checks_rerun or [],
                    success=log.success,
                    summary=log.summary,
                    created_at=log.created_at,
                )
            )
            final_status = ExecutionStatus(log.rerun_status)

        return RepairHistoryResponse(
            project_id=project_id,
            total_attempts=len(attempts),
            final_status=final_status,
            total_patches_applied=total_patches,
            attempts=attempts,
        )
