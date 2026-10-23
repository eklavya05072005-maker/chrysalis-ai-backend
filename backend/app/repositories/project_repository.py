import uuid
from typing import Optional, List, Tuple
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models import Project


class ProjectRepository:
    """Repository for database operations on Project entities."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, description: Optional[str] = None) -> Project:
        """Create and persist a new Project record."""
        project = Project(
            id=uuid.uuid4(),
            name=name,
            description=description,
            status="uploaded",
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id: uuid.UUID, eager: bool = False) -> Optional[Project]:
        """Retrieve a project by UUID, optionally eagerly loading relationships."""
        stmt = select(Project).where(Project.id == project_id)
        if eager:
            stmt = stmt.options(
                selectinload(Project.documents),
                selectinload(Project.requirements),
                selectinload(Project.architecture_options),
                selectinload(Project.simulation_results),
                selectinload(Project.generated_files),
            )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_projects(self, skip: int = 0, limit: int = 20) -> Tuple[List[Project], int]:
        """List projects with pagination ordered by latest created."""
        total_stmt = select(func.count(Project.id))
        total = self.db.execute(total_stmt).scalar() or 0

        stmt = select(Project).order_by(desc(Project.created_at)).offset(skip).limit(limit)
        items = list(self.db.execute(stmt).scalars().all())

        return items, total

    def update_status(
        self,
        project_id: uuid.UUID,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[Project]:
        """Update lifecycle status and optional error message of a project."""
        project = self.get_by_id(project_id)
        if not project:
            return None

        project.status = status
        project.error_message = error_message
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project_id: uuid.UUID) -> bool:
        """Delete a project and cascade delete all child entities."""
        project = self.get_by_id(project_id)
        if not project:
            return False
        self.db.delete(project)
        self.db.commit()
        return True
