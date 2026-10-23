from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
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
from backend.app.services.ai_engine import get_ai_engine, AIEngineInterface
from backend.app.services.sandbox_service import SandboxService
from backend.app.services.connector_service import ConnectorService
from backend.app.services.repair_service import RepairService
from backend.app.services.audit_service import AuditService
from backend.app.services.project_service import ProjectService


def get_project_service(
    db: Session = Depends(get_db),
    ai_engine: AIEngineInterface = Depends(get_ai_engine),
) -> ProjectService:
    """Dependency injection provider for ProjectService."""
    project_repo = ProjectRepository(db)
    document_repo = DocumentRepository(db)
    requirement_repo = RequirementRepository(db)
    architecture_repo = ArchitectureRepository(db)
    simulation_repo = SimulationRepository(db)
    generation_repo = GenerationRepository(db)
    execution_repo = ExecutionRepository(db)
    connector_repo = ConnectorRepository(db)
    repair_repo = RepairRepository(db)
    audit_repo = AuditRepository(db)

    storage_service = StorageService()
    sandbox_service = SandboxService(storage_service=storage_service)
    connector_service = ConnectorService(connector_repo=connector_repo)
    repair_service = RepairService(
        project_repo=project_repo,
        generation_repo=generation_repo,
        repair_repo=repair_repo,
        storage_service=storage_service,
        sandbox_service=sandbox_service,
    )
    audit_service = AuditService(
        project_repo=project_repo,
        audit_repo=audit_repo,
        execution_repo=execution_repo,
        generation_repo=generation_repo,
        connector_repo=connector_repo,
        repair_repo=repair_repo,
    )

    return ProjectService(
        project_repo=project_repo,
        document_repo=document_repo,
        requirement_repo=requirement_repo,
        architecture_repo=architecture_repo,
        simulation_repo=simulation_repo,
        generation_repo=generation_repo,
        storage_service=storage_service,
        ai_engine=ai_engine,
        execution_repo=execution_repo,
        connector_repo=connector_repo,
        repair_repo=repair_repo,
        audit_repo=audit_repo,
        sandbox_service=sandbox_service,
        connector_service=connector_service,
        repair_service=repair_service,
        audit_service=audit_service,
    )

