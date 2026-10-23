import uuid
from typing import Optional, List
from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    Query,
    status,
)
from fastapi.responses import FileResponse

from backend.app.api.dependencies import get_project_service
from backend.app.services.project_service import ProjectService
from backend.app.schemas.project import (
    ProjectResponse,
    ProjectDetailResponse,
    ProjectListResponse,
)
from backend.app.schemas.requirement import RequirementResponse, RequirementListResponse
from backend.app.schemas.architecture import (
    ArchitectureOptionResponse,
    ArchitectureSelectRequest,
    ArchitectureListResponse,
)
from backend.app.schemas.simulation import (
    SimulationResultResponse,
    SimulationListResponse,
)
from backend.app.schemas.generation import (
    GeneratedFileResponse,
    ValidationReport,
    GenerationSummaryResponse,
)
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

router = APIRouter(prefix="/projects", tags=["Projects"])



@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Project and Upload PDF",
    description="Creates a new project and processes the uploaded requirements document.",
)
def create_project(
    name: str = Form(..., description="Project name"),
    description: Optional[str] = Form(None, description="Project description"),
    file: UploadFile = File(..., description="Requirements PDF document"),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    project = service.create_project_with_document(name=name, description=description, file=file)
    return ProjectResponse.model_validate(project)


@router.get(
    "",
    response_model=ProjectListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Projects",
    description="Retrieves a paginated list of projects ordered by creation date.",
)
def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: ProjectService = Depends(get_project_service),
) -> ProjectListResponse:
    items, total, pages = service.list_projects(page=page, size=size)
    return ProjectListResponse(
        items=[ProjectResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Project Details",
    description="Retrieves full project details including documents, requirements, architectures, and simulation results.",
)
def get_project(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> ProjectDetailResponse:
    project = service.get_project(project_id)
    return ProjectDetailResponse.model_validate(project)


@router.post(
    "/{project_id}/analyze",
    response_model=RequirementListResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract and Analyze Requirements",
    description="Invokes the AI Engine to extract and categorize software requirements from uploaded documents.",
)
def analyze_requirements(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> RequirementListResponse:
    reqs = service.analyze_requirements(project_id)
    items = [RequirementResponse.model_validate(r) for r in reqs]
    return RequirementListResponse(
        project_id=project_id,
        total=len(items),
        items=items,
    )


@router.post(
    "/{project_id}/architectures",
    response_model=ArchitectureListResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Architecture Options",
    description="Invokes the AI Engine to generate 3 tailored architecture options with Agentic AI workflows.",
)
def generate_architectures(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> ArchitectureListResponse:
    archs = service.generate_architectures(project_id)
    items = [ArchitectureOptionResponse.model_validate(a) for a in archs]
    return ArchitectureListResponse(
        project_id=project_id,
        total=len(items),
        items=items,
    )


@router.post(
    "/{project_id}/simulate",
    response_model=SimulationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate Architectures",
    description="Simulates load and fault-tolerance scenarios across all generated architectures.",
)
def simulate_architectures(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> SimulationListResponse:
    sims = service.simulate_architectures(project_id)
    items = [SimulationResultResponse.model_validate(s) for s in sims]
    return SimulationListResponse(
        project_id=project_id,
        total=len(items),
        items=items,
    )


@router.post(
    "/{project_id}/select",
    response_model=ArchitectureOptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Select Architecture Option",
    description="Selects an architecture option to be used for source code generation.",
)
def select_architecture(
    project_id: uuid.UUID,
    payload: ArchitectureSelectRequest,
    service: ProjectService = Depends(get_project_service),
) -> ArchitectureOptionResponse:
    selected = service.select_architecture(project_id, payload.architecture_id)
    return ArchitectureOptionResponse.model_validate(selected)


@router.post(
    "/{project_id}/generate",
    response_model=GenerationSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Source Files",
    description="Generates complete agentic source code and archives the project into a package.",
)
def generate_files(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> GenerationSummaryResponse:
    files = service.generate_files(project_id)
    file_items = [GeneratedFileResponse.model_validate(f) for f in files]
    return GenerationSummaryResponse(
        project_id=project_id,
        total_files=len(file_items),
        status="generated",
        files=file_items,
    )


@router.post(
    "/{project_id}/validate",
    response_model=ValidationReport,
    status_code=status.HTTP_200_OK,
    summary="Validate Generated Files",
    description="Executes static AST syntax and schema validation across all generated files.",
)
def validate_files(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> ValidationReport:
    report = service.validate_files(project_id)
    return report


@router.get(
    "/{project_id}/files",
    response_model=List[GeneratedFileResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve Generated Files Metadata",
    description="Returns metadata for all files generated for the project.",
)
def get_files(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> List[GeneratedFileResponse]:
    files = service.get_generated_files(project_id)
    return [GeneratedFileResponse.model_validate(f) for f in files]


@router.get(
    "/{project_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download Project Package ZIP",
    description="Downloads the generated software package as a ZIP archive.",
)
def download_package(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
):
    zip_path = service.get_download_package_path(project_id)
    return FileResponse(
        path=str(zip_path),
        filename=zip_path.name,
        media_type="application/zip",
    )


@router.get(
    "/{project_id}/wizard",
    response_model=WizardQuestionnaire,
    status_code=status.HTTP_200_OK,
    summary="Generate Adaptive Questionnaire",
    description="Generates 3-5 context-aware architectural questions (autonomy, connectors, data mode, constraints).",
)
def get_wizard_questionnaire(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> WizardQuestionnaire:
    return service.get_wizard_questionnaire(project_id)


@router.post(
    "/{project_id}/wizard",
    response_model=ConfirmedProjectSpec,
    status_code=status.HTTP_200_OK,
    summary="Submit Questionnaire Answers",
    description="Submits user answers to the adaptive questionnaire and produces an updated specification.",
)
def submit_wizard_answers(
    project_id: uuid.UUID,
    submission: WizardAnswerSubmission,
    confirm: bool = Query(False, description="Set to true if user is explicitly confirming specification"),
    service: ProjectService = Depends(get_project_service),
) -> ConfirmedProjectSpec:
    return service.submit_wizard_answers(project_id, submission=submission, confirm=confirm)


@router.post(
    "/{project_id}/confirm",
    response_model=ConfirmedProjectSpec,
    status_code=status.HTTP_200_OK,
    summary="Confirm Project Specification",
    description="Explicitly locks and confirms the project specification with user answers.",
)
def confirm_specification(
    project_id: uuid.UUID,
    submission: Optional[WizardAnswerSubmission] = None,
    service: ProjectService = Depends(get_project_service),
) -> ConfirmedProjectSpec:
    return service.submit_wizard_answers(project_id, submission=submission, confirm=True)


@router.get(
    "/{project_id}/spec",
    response_model=ConfirmedProjectSpec,
    status_code=status.HTTP_200_OK,
    summary="Get Confirmed Specification",
    description="Retrieves the current confirmed or synthesized specification.",
)
def get_specification(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> ConfirmedProjectSpec:
    return service.get_confirmed_specification(project_id)


@router.post(
    "/{project_id}/verdict",
    response_model=SystemVerdictResult,
    status_code=status.HTTP_200_OK,
    summary="Generate System Verdict",
    description="Evaluates the specification and produces an explainable overall verdict: non-agentic, agentic, or hybrid.",
)
def generate_verdict(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> SystemVerdictResult:
    return service.generate_system_verdict(project_id)


@router.get(
    "/{project_id}/verdict",
    response_model=SystemVerdictResult,
    status_code=status.HTTP_200_OK,
    summary="Get System Verdict",
    description="Retrieves the current system verdict for the project.",
)
def get_verdict(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> SystemVerdictResult:
    return service.get_system_verdict(project_id)


# ==============================================================================
# Phase 3: Restricted Execution Sandbox Endpoints
# ==============================================================================

@router.post(
    "/{project_id}/execute",
    response_model=ExecutionRunResult,
    status_code=status.HTTP_200_OK,
    summary="Execute Generated Project in Sandbox",
    description="Runs tests inside a restricted container sandbox with memory, CPU, and network isolation.",
)
def execute_project(
    project_id: uuid.UUID,
    request: Optional[ExecutionRunRequest] = None,
    service: ProjectService = Depends(get_project_service),
) -> ExecutionRunResult:
    req = request or ExecutionRunRequest(project_id=project_id)
    return service.execute_sandbox_run(project_id, req)


@router.get(
    "/{project_id}/execution/{run_id}",
    response_model=ExecutionRunResult,
    status_code=status.HTTP_200_OK,
    summary="Get Execution Run",
    description="Retrieves execution run status, logs, and measured resource statistics.",
)
def get_execution_run(
    project_id: uuid.UUID,
    run_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> ExecutionRunResult:
    return service.get_execution_run(project_id, run_id)


@router.get(
    "/{project_id}/execution",
    response_model=ExecutionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Execution Runs",
    description="Retrieves all past execution runs and logs for a project.",
)
def list_execution_runs(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> ExecutionListResponse:
    return service.list_execution_runs(project_id)


# ==============================================================================
# Phase 3: Test-Guided Code Repair Endpoints
# ==============================================================================

@router.post(
    "/{project_id}/repair",
    response_model=RepairHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Bounded Code Repair",
    description="Executes a bounded code repair loop using static check and test feedback.",
)
def repair_project(
    project_id: uuid.UUID,
    request: Optional[RepairRequest] = None,
    service: ProjectService = Depends(get_project_service),
) -> RepairHistoryResponse:
    req = request or RepairRequest(project_id=project_id)
    return service.repair_project(project_id, req)


@router.get(
    "/{project_id}/repair",
    response_model=RepairHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Repair History and Diffs",
    description="Retrieves the history of proposed, applied, and verified patches with unified diffs.",
)
def get_repair_history(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> RepairHistoryResponse:
    return service.get_repair_history(project_id)


# ==============================================================================
# Phase 3: Connector Subsystem Endpoints
# ==============================================================================

@router.post(
    "/{project_id}/connectors",
    response_model=ConnectorConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Integration Connector",
    description="Registers and validates a REST, MCP, Database, or Mock connector configuration.",
)
def register_connector(
    project_id: uuid.UUID,
    config: ConnectorConfigCreate,
    service: ProjectService = Depends(get_project_service),
) -> ConnectorConfigResponse:
    return service.register_connector(project_id, config)


@router.get(
    "/{project_id}/connectors",
    response_model=ConnectorListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Connectors",
    description="Retrieves all registered connectors for a project with secrets masked.",
)
def list_connectors(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> ConnectorListResponse:
    return service.list_connectors(project_id)


@router.post(
    "/{project_id}/connectors/{connector_id}/test",
    response_model=ConnectorTestResponse,
    status_code=status.HTTP_200_OK,
    summary="Test or Invoke Connector",
    description="Tests connector connectivity or executes mock tool under sandbox security constraints.",
)
def test_connector(
    project_id: uuid.UUID,
    connector_id: uuid.UUID,
    request: ConnectorTestRequest,
    service: ProjectService = Depends(get_project_service),
) -> ConnectorTestResponse:
    return service.test_connector(project_id, connector_id, request)


@router.post(
    "/{project_id}/connectors/{connector_id}/approve",
    response_model=ConnectorConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve Connector Permissions",
    description="Grants explicit human approval for write or sensitive operations on a connector.",
)
def approve_connector(
    project_id: uuid.UUID,
    connector_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> ConnectorConfigResponse:
    return service.approve_connector(project_id, connector_id)


# ==============================================================================
# Phase 3: Audit Trail and Honest Verification Standing Endpoints
# ==============================================================================

@router.get(
    "/{project_id}/audit",
    response_model=ProjectVerificationSummary,
    status_code=status.HTTP_200_OK,
    summary="Get Honest Verification Standing",
    description="Retrieves the current honest verification standing and active limitations for a project.",
)
def get_audit_summary(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> ProjectVerificationSummary:
    return service.get_audit_summary(project_id)


@router.get(
    "/{project_id}/audit/events",
    response_model=List[AuditEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List Audit Events",
    description="Retrieves tamper-evident audit events and logs for a project.",
)
def list_audit_events(
    project_id: uuid.UUID,
    service: ProjectService = Depends(get_project_service),
) -> List[AuditEventResponse]:
    return service.list_audit_events(project_id)

