import uuid
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, UploadFile, status

from backend.app.db.models import (
    Project,
    Document,
    Requirement,
    ArchitectureOption,
    SimulationResult,
    GeneratedFile,
    ExecutionRun,
    ConnectorModel,
    RepairLog,
    AuditEventModel,
)
from backend.app.repositories import (
    ProjectRepository,
    DocumentRepository,
    RequirementRepository,
    ArchitectureRepository,
    SimulationRepository,
    GenerationRepository,
    ExecutionRepository,
    ConnectorRepository,
    RepairRepository,
    AuditRepository,
)
from backend.app.services.storage_service import StorageService
from backend.app.services.document_service import DocumentService
from backend.app.services.ai_engine import AIEngineInterface
from backend.app.services.validation_service import ValidationService
from backend.app.services.sandbox_service import SandboxService
from backend.app.services.connector_service import ConnectorService
from backend.app.services.repair_service import RepairService
from backend.app.services.audit_service import AuditService
from backend.app.schemas.generation import ValidationReport
from backend.app.schemas.wizard import (
    WizardQuestionnaire,
    WizardAnswerSubmission,
    ConfirmedProjectSpec,
)
from backend.app.schemas.verdict import SystemVerdictResult
from backend.app.schemas.sandbox import (
    ExecutionListResponse,
    ExecutionRunRequest,
    ExecutionRunResult,
    ExecutionStatus,
    SandboxRuntimeType,
)
from backend.app.schemas.connector import (
    ConnectorConfigCreate,
    ConnectorConfigResponse,
    ConnectorListResponse,
    ConnectorTestRequest,
    ConnectorTestResponse,
)
from backend.app.schemas.repair import (
    RepairHistoryResponse,
    RepairRequest,
)
from backend.app.schemas.audit import (
    AuditEventResponse,
    ProjectVerificationSummary,
)

logger = logging.getLogger(__name__)


class ProjectService:
    """
    Core domain service orchestrating the Chrysalis AI workflow lifecycle:
    uploaded -> analyzing -> analyzed -> architectures_ready -> simulated ->
    architecture_selected -> generating -> generated -> validating -> validated ->
    executed -> repaired -> verified.
    """

    def __init__(
        self,
        project_repo: ProjectRepository,
        document_repo: DocumentRepository,
        requirement_repo: RequirementRepository,
        architecture_repo: ArchitectureRepository,
        simulation_repo: SimulationRepository,
        generation_repo: GenerationRepository,
        storage_service: StorageService,
        ai_engine: AIEngineInterface,
        execution_repo: Optional[ExecutionRepository] = None,
        connector_repo: Optional[ConnectorRepository] = None,
        repair_repo: Optional[RepairRepository] = None,
        audit_repo: Optional[AuditRepository] = None,
        sandbox_service: Optional[SandboxService] = None,
        connector_service: Optional[ConnectorService] = None,
        repair_service: Optional[RepairService] = None,
        audit_service: Optional[AuditService] = None,
    ):
        self.project_repo = project_repo
        self.document_repo = document_repo
        self.requirement_repo = requirement_repo
        self.architecture_repo = architecture_repo
        self.simulation_repo = simulation_repo
        self.generation_repo = generation_repo
        self.storage_service = storage_service
        self.ai_engine = ai_engine

        # Phase 3 repositories & services (initialized safely if omitted)
        self.execution_repo = execution_repo
        self.connector_repo = connector_repo
        self.repair_repo = repair_repo
        self.audit_repo = audit_repo
        self.sandbox_service = sandbox_service or SandboxService(storage_service=storage_service)
        self.connector_service = connector_service or (
            ConnectorService(connector_repo=connector_repo) if connector_repo else None
        )
        self.repair_service = repair_service or (
            RepairService(
                project_repo=project_repo,
                generation_repo=generation_repo,
                repair_repo=repair_repo,
                storage_service=storage_service,
                sandbox_service=self.sandbox_service,
            ) if repair_repo else None
        )
        self.audit_service = audit_service or (
            AuditService(
                project_repo=project_repo,
                audit_repo=audit_repo,
                execution_repo=execution_repo,
                generation_repo=generation_repo,
                connector_repo=connector_repo,
                repair_repo=repair_repo,
            ) if (audit_repo and execution_repo and connector_repo and repair_repo) else None
        )


    def create_project_with_document(
        self,
        name: str,
        description: Optional[str],
        file: UploadFile,
    ) -> Project:
        """
        Creates a new project and attaches the uploaded requirements PDF.
        Stores file on disk in data/uploads/{project_id}/ and metadata in database.
        """
        # Read file content
        content = file.file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        # Validate PDF
        DocumentService.validate_pdf_upload(file, content)

        # Extract text using pypdf
        extracted_text, _ = DocumentService.extract_text_from_pdf(content)

        # Persist Project in DB
        project = self.project_repo.create(name=name, description=description)

        try:
            # Save file to storage
            _, stored_filename, file_size = self.storage_service.save_upload(
                project_id=project.id,
                filename=file.filename or "requirements.pdf",
                content=content,
            )

            # Persist Document metadata in DB
            self.document_repo.create(
                project_id=project.id,
                original_filename=file.filename or "requirements.pdf",
                stored_filename=stored_filename,
                file_type=file.content_type or "application/pdf",
                file_size=file_size,
                extracted_text=extracted_text,
                upload_status="success",
            )
            return project

        except Exception as exc:
            logger.error(f"Failed to persist uploaded document for project {project.id}: {exc}")
            self.project_repo.update_status(project.id, "upload_failed", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save document: {str(exc)}",
            )

    def get_project(self, project_id: uuid.UUID) -> Project:
        """Retrieve project with full details or raise 404."""
        project = self.project_repo.get_by_id(project_id, eager=True)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )
        return project

    def list_projects(self, page: int = 1, size: int = 20) -> Tuple[List[Project], int, int]:
        """List paginated projects. Returns (items, total, total_pages)."""
        skip = (page - 1) * size
        items, total = self.project_repo.list_projects(skip=skip, limit=size)
        pages = (total + size - 1) // size if size > 0 else 1
        return items, total, pages

    def analyze_requirements(self, project_id: uuid.UUID) -> List[Requirement]:
        """
        Analyzes uploaded document and persists extracted requirements in database.
        Lifecycle: uploaded/analyzed -> analyzing -> analyzed (or analysis_failed).
        """
        project = self.get_project(project_id)
        docs = self.document_repo.get_by_project_id(project_id)
        if not docs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No documents found for this project to analyze.",
            )

        combined_text = "\n\n".join([d.extracted_text or "" for d in docs])
        self.project_repo.update_status(project_id, "analyzing")

        try:
            raw_reqs = self.ai_engine.analyze_requirements(combined_text, project.name)
            # Idempotent: remove previous requirements if re-analyzing
            self.requirement_repo.delete_by_project(project_id)
            saved = self.requirement_repo.bulk_create(project_id, raw_reqs)
            self.project_repo.update_status(project_id, "analyzed")
            return saved

        except Exception as exc:
            logger.error(f"Error during requirement analysis for project {project_id}: {exc}")
            self.project_repo.update_status(project_id, "analysis_failed", str(exc))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI Engine failed to analyze requirements: {str(exc)}",
            )

    def generate_architectures(self, project_id: uuid.UUID) -> List[ArchitectureOption]:
        """
        Generates and persists 3 architecture options incorporating Agentic workflows.
        Lifecycle: analyzed -> generating_architectures -> architectures_ready.
        """
        project = self.get_project(project_id)
        reqs = self.requirement_repo.get_by_project_id(project_id)
        if not reqs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project must be analyzed before architectures can be generated.",
            )

        reqs_data = [
            {
                "title": r.title,
                "description": r.description,
                "requirement_type": r.requirement_type,
                "priority": r.priority,
                "source_page": r.source_page,
                "evidence_text": r.evidence_text,
            }
            for r in reqs
        ]

        self.project_repo.update_status(project_id, "generating_architectures")

        try:
            raw_archs = self.ai_engine.generate_architectures(reqs_data, project.name)
            # Idempotent: delete previous architectures for project
            self.architecture_repo.delete_by_project(project_id)
            saved = self.architecture_repo.bulk_create(project_id, raw_archs)
            self.project_repo.update_status(project_id, "architectures_ready")
            return saved

        except Exception as exc:
            logger.error(f"Error during architecture generation for project {project_id}: {exc}")
            self.project_repo.update_status(project_id, "architectures_failed", str(exc))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI Engine failed to generate architectures: {str(exc)}",
            )

    def simulate_architectures(self, project_id: uuid.UUID) -> List[SimulationResult]:
        """
        Runs scenario simulations across all generated architectures and persists results in database.
        Lifecycle: architectures_ready -> simulated.
        """
        project = self.get_project(project_id)
        archs = self.architecture_repo.get_by_project_id(project_id)
        if not archs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No architecture options available for simulation.",
            )

        reqs = self.requirement_repo.get_by_project_id(project_id)
        arch_data = [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "estimated_latency": a.estimated_latency,
                "estimated_cost": a.estimated_cost,
            }
            for a in archs
        ]
        req_data = [
            {
                "title": r.title,
                "description": r.description,
                "requirement_type": r.requirement_type,
            }
            for r in reqs
        ]

        try:
            raw_sims = self.ai_engine.evaluate_architectures(arch_data, req_data)
            # Idempotent: delete old simulation results
            self.simulation_repo.delete_by_project(project_id)
            saved = self.simulation_repo.bulk_create(project_id, raw_sims)
            self.project_repo.update_status(project_id, "simulated")
            return saved

        except Exception as exc:
            logger.error(f"Simulation failed for project {project_id}: {exc}")
            self.project_repo.update_status(project_id, "simulation_failed", str(exc))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Simulation failed: {str(exc)}",
            )

    def select_architecture(self, project_id: uuid.UUID, architecture_id: uuid.UUID) -> ArchitectureOption:
        """
        Saves the chosen architecture and updates project status to architecture_selected.
        """
        self.get_project(project_id)
        arch = self.architecture_repo.select_architecture(project_id, architecture_id)
        if not arch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected architecture does not exist for this project.",
            )

        self.project_repo.update_status(project_id, "architecture_selected")
        return arch

    def generate_files(self, project_id: uuid.UUID) -> List[GeneratedFile]:
        """
        Generates source files and stores files on disk and metadata in database.
        Lifecycle: architecture_selected -> generating -> generated.
        """
        project = self.get_project(project_id)
        selected_arch = self.architecture_repo.get_selected(project_id)
        if not selected_arch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An architecture option must be selected before generating files.",
            )

        self.project_repo.update_status(project_id, "generating")

        try:
            raw_files = self.ai_engine.generate_project_files(
                selected_architecture={
                    "id": selected_arch.id,
                    "name": selected_arch.name,
                    "description": selected_arch.description,
                    "components": selected_arch.components,
                },
                project_name=project.name,
            )

            # Idempotent cleanup of old generated files
            self.generation_repo.delete_by_project(project_id)

            files_metadata: List[Dict[str, Any]] = []
            for file_spec in raw_files:
                # Save physical file to data/generated/{project_id}/
                _, file_size = self.storage_service.save_generated_file(
                    project_id=project_id,
                    relative_path=file_spec["relative_path"],
                    content=file_spec["content"],
                )

                files_metadata.append(
                    {
                        "relative_path": file_spec["relative_path"],
                        "filename": file_spec["filename"],
                        "language": file_spec["language"],
                        "file_size": file_size,
                        "validation_status": "pending",
                    }
                )

            saved = self.generation_repo.bulk_create(project_id, files_metadata)
            # Create zip package
            self.storage_service.create_zip_package(project_id)
            self.project_repo.update_status(project_id, "generated")
            return saved

        except Exception as exc:
            logger.error(f"File generation failed for project {project_id}: {exc}")
            self.project_repo.update_status(project_id, "generation_failed", str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File generation failed: {str(exc)}",
            )

    def validate_files(self, project_id: uuid.UUID) -> ValidationReport:
        """
        Runs non-executing static code syntax validation on all generated files.
        Lifecycle: generated -> validating -> validated (or validation_failed).
        """
        self.get_project(project_id)
        files = self.generation_repo.get_by_project_id(project_id)
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No generated files found to validate.",
            )

        self.project_repo.update_status(project_id, "validating")

        passed_count = 0
        failed_count = 0
        details: List[Dict[str, Any]] = []
        status_map: Dict[str, str] = {}

        for f in files:
            try:
                content = self.storage_service.read_generated_file(project_id, f.relative_path)
                result = ValidationService.validate_file_content(f.filename, content)
                is_valid = result["valid"]
                error_msg = result["error"]
            except Exception as e:
                is_valid = False
                error_msg = str(e)

            val_status = "passed" if is_valid else "failed"
            status_map[f.relative_path] = val_status

            if is_valid:
                passed_count += 1
            else:
                failed_count += 1

            details.append(
                {
                    "relative_path": f.relative_path,
                    "filename": f.filename,
                    "status": val_status,
                    "error": error_msg,
                }
            )

        # Bulk update validation status in DB
        self.generation_repo.bulk_update_validation(project_id, status_map)

        overall_status = "validated" if failed_count == 0 else "validation_failed"
        self.project_repo.update_status(
            project_id,
            overall_status,
            f"{failed_count} file(s) failed syntax validation" if failed_count > 0 else None,
        )

        return ValidationReport(
            project_id=project_id,
            total_files=len(files),
            passed_files=passed_count,
            failed_files=failed_count,
            validation_status=overall_status,
            details=details,
        )

    def get_generated_files(self, project_id: uuid.UUID) -> List[GeneratedFile]:
        """Retrieves generated file metadata from database."""
        self.get_project(project_id)
        return self.generation_repo.get_by_project_id(project_id)

    def get_download_package_path(self, project_id: uuid.UUID) -> Path:
        """Retrieves or creates downloadable ZIP package."""
        self.get_project(project_id)
        zip_path = self.storage_service.get_zip_package_path(project_id)
        if not zip_path or not zip_path.exists():
            # Check if files exist to create zip
            files = self.generation_repo.get_by_project_id(project_id)
            if not files:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No generated files available for download.",
                )
            zip_path = self.storage_service.create_zip_package(project_id)

        return zip_path

    def get_wizard_questionnaire(self, project_id: uuid.UUID) -> WizardQuestionnaire:
        """Generates or retrieves adaptive 3-5 questions for requirement elicitation."""
        project = self.get_project(project_id)
        docs = self.document_repo.get_by_project_id(project_id)
        combined_text = "\n\n".join([d.extracted_text or "" for d in docs]) if docs else ""
        return self.ai_engine.generate_wizard_questionnaire(project.name, document_text=combined_text)

    def submit_wizard_answers(
        self,
        project_id: uuid.UUID,
        submission: Optional[WizardAnswerSubmission] = None,
        confirm: bool = False,
    ) -> ConfirmedProjectSpec:
        """Merges user answers into ConfirmedProjectSpec, maintaining citation audit trail."""
        project = self.get_project(project_id)
        docs = self.document_repo.get_by_project_id(project_id)
        combined_text = "\n\n".join([d.extracted_text or "" for d in docs]) if docs else ""
        return self.ai_engine.confirm_specification(
            project_name=project.name,
            submission=submission,
            confirm=confirm,
            document_text=combined_text,
        )

    def get_confirmed_specification(self, project_id: uuid.UUID) -> ConfirmedProjectSpec:
        """Retrieves current confirmed specification or synthesizes default if pending."""
        project = self.get_project(project_id)
        spec = self.ai_engine.get_confirmed_specification(project.name)
        if spec is None:
            return self.submit_wizard_answers(project_id, submission=None, confirm=False)
        return spec

    def generate_system_verdict(self, project_id: uuid.UUID) -> SystemVerdictResult:
        """Produces explainable verdict (non-agentic, agentic, or hybrid)."""
        project = self.get_project(project_id)
        docs = self.document_repo.get_by_project_id(project_id)
        combined_text = "\n\n".join([d.extracted_text or "" for d in docs]) if docs else ""
        return self.ai_engine.generate_system_verdict(project.name, document_text=combined_text)

    def get_system_verdict(self, project_id: uuid.UUID) -> SystemVerdictResult:
        """Retrieves cached system verdict or computes it on demand."""
        project = self.get_project(project_id)
        verdict = self.ai_engine.get_system_verdict(project.name)
        if verdict is None:
            return self.generate_system_verdict(project_id)
        return verdict

    # ==========================================================================
    # Phase 3: Restricted Execution Sandbox Methods
    # ==========================================================================

    def execute_sandbox_run(
        self,
        project_id: uuid.UUID,
        request: ExecutionRunRequest,
    ) -> ExecutionRunResult:
        """Executes generated project tests inside an isolated sandbox."""
        self.get_project(project_id)
        result = self.sandbox_service.execute_project(request)

        # Persist run if repository is wired
        if self.execution_repo:
            saved_run = self.execution_repo.create(
                project_id=project_id,
                status=result.status.value,
                runtime=result.runtime,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                elapsed_time_seconds=result.elapsed_time_seconds,
                timed_out=result.timed_out,
                resource_limit_hit=result.resource_limit_hit,
                network_isolated=result.network_isolated,
                checks_performed=result.checks_performed,
                message=result.message,
                run_id=result.run_id,
            )
            result.run_id = saved_run.id

        # Log audit event
        if self.audit_service:
            self.audit_service.log_event(
                project_id=project_id,
                event_type="EXECUTION_RUN",
                details={
                    "status": result.status.value,
                    "runtime": result.runtime,
                    "exit_code": result.exit_code,
                    "elapsed_time_seconds": result.elapsed_time_seconds,
                },
            )

        return result

    def get_execution_run(self, project_id: uuid.UUID, run_id: uuid.UUID) -> ExecutionRunResult:
        """Retrieves an execution run by ID."""
        self.get_project(project_id)
        if not self.execution_repo:
            raise HTTPException(status_code=500, detail="Execution repository not initialized.")
        run = self.execution_repo.get_by_id(run_id)
        if not run or run.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution run not found.")

        return ExecutionRunResult(
            run_id=run.id,
            project_id=run.project_id,
            status=ExecutionStatus(run.status),
            runtime=run.runtime,
            exit_code=run.exit_code,
            stdout=run.stdout or "",
            stderr=run.stderr or "",
            elapsed_time_seconds=run.elapsed_time_seconds,
            timed_out=run.timed_out,
            resource_limit_hit=run.resource_limit_hit,
            network_isolated=run.network_isolated,
            checks_performed=run.checks_performed or [],
            sandbox_cleaned_up=True,
            message=run.message,
            created_at=run.created_at,
        )

    def list_execution_runs(self, project_id: uuid.UUID) -> ExecutionListResponse:
        """Lists past execution runs for a project."""
        self.get_project(project_id)
        if not self.execution_repo:
            return ExecutionListResponse(project_id=project_id, total=0, items=[])

        runs = self.execution_repo.get_by_project_id(project_id)
        items = [
            ExecutionRunResult(
                run_id=r.id,
                project_id=r.project_id,
                status=ExecutionStatus(r.status),
                runtime=r.runtime,
                exit_code=r.exit_code,
                stdout=r.stdout or "",
                stderr=r.stderr or "",
                elapsed_time_seconds=r.elapsed_time_seconds,
                timed_out=r.timed_out,
                resource_limit_hit=r.resource_limit_hit,
                network_isolated=r.network_isolated,
                checks_performed=r.checks_performed or [],
                sandbox_cleaned_up=True,
                message=r.message,
                created_at=r.created_at,
            )
            for r in runs
        ]
        return ExecutionListResponse(project_id=project_id, total=len(items), items=items)

    # ==========================================================================
    # Phase 3: Test-Guided Code Repair Methods
    # ==========================================================================

    def repair_project(
        self,
        project_id: uuid.UUID,
        request: RepairRequest,
    ) -> RepairHistoryResponse:
        """Executes bounded code repair loop and records audit logs."""
        self.get_project(project_id)
        if not self.repair_service:
            raise HTTPException(status_code=500, detail="Repair service not initialized.")

        history = self.repair_service.execute_bounded_repair(request)

        if self.audit_service:
            self.audit_service.log_event(
                project_id=project_id,
                event_type="CODE_REPAIR_ATTEMPT",
                details={
                    "total_attempts": history.total_attempts,
                    "final_status": history.final_status.value,
                    "total_patches_applied": history.total_patches_applied,
                },
            )

        return history

    def get_repair_history(self, project_id: uuid.UUID) -> RepairHistoryResponse:
        """Retrieves history of past code repair attempts."""
        self.get_project(project_id)
        if not self.repair_service:
            raise HTTPException(status_code=500, detail="Repair service not initialized.")
        return self.repair_service.get_repair_history(project_id)

    # ==========================================================================
    # Phase 3: Connector Subsystem Methods
    # ==========================================================================

    def register_connector(
        self,
        project_id: uuid.UUID,
        config: ConnectorConfigCreate,
    ) -> ConnectorConfigResponse:
        """Registers and validates a new connector configuration."""
        self.get_project(project_id)
        if not self.connector_service:
            raise HTTPException(status_code=500, detail="Connector service not initialized.")

        try:
            resp = self.connector_service.register_connector(project_id, config)
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

        if self.audit_service:
            self.audit_service.log_event(
                project_id=project_id,
                event_type="CONNECTOR_REGISTERED",
                details={"connector_id": str(resp.id), "name": resp.name, "type": resp.connector_type.value},
            )

        return resp

    def list_connectors(self, project_id: uuid.UUID) -> ConnectorListResponse:
        """Lists all registered connectors for a project (secrets masked)."""
        self.get_project(project_id)
        if not self.connector_service:
            return ConnectorListResponse(project_id=project_id, total=0, items=[])
        return self.connector_service.list_connectors(project_id)

    def test_connector(
        self,
        project_id: uuid.UUID,
        connector_id: uuid.UUID,
        request: ConnectorTestRequest,
    ) -> ConnectorTestResponse:
        """Tests connector connectivity under sandbox constraints."""
        self.get_project(project_id)
        if not self.connector_service:
            raise HTTPException(status_code=500, detail="Connector service not initialized.")

        try:
            resp = self.connector_service.test_connector(connector_id, request)
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

        if self.audit_service:
            self.audit_service.log_event(
                project_id=project_id,
                event_type="CONNECTOR_TESTED",
                details={"connector_id": str(connector_id), "success": resp.success, "is_mock": resp.is_mock},
            )

        return resp

    def approve_connector(
        self,
        project_id: uuid.UUID,
        connector_id: uuid.UUID,
    ) -> ConnectorConfigResponse:
        """Grants human approval for write or sensitive operations on a connector."""
        self.get_project(project_id)
        if not self.connector_service:
            raise HTTPException(status_code=500, detail="Connector service not initialized.")

        try:
            resp = self.connector_service.approve_connector(connector_id)
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

        if self.audit_service:
            self.audit_service.log_event(
                project_id=project_id,
                event_type="CONNECTOR_APPROVED",
                details={"connector_id": str(connector_id), "name": resp.name},
            )

        return resp

    # ==========================================================================
    # Phase 3: Audit Trail and Honest Verification Standing Methods
    # ==========================================================================

    def get_audit_summary(self, project_id: uuid.UUID) -> ProjectVerificationSummary:
        """Returns comprehensive honest verification standing across all checks."""
        self.get_project(project_id)
        if not self.audit_service:
            raise HTTPException(status_code=500, detail="Audit service not initialized.")
        return self.audit_service.get_project_summary(project_id)

    def list_audit_events(self, project_id: uuid.UUID) -> List[AuditEventResponse]:
        """Lists tamper-evident audit events for a project."""
        self.get_project(project_id)
        if not self.audit_service:
            return []
        return self.audit_service.get_events(project_id)

