import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session

from backend.app.db.models import ArchitectureOption


class ArchitectureRepository:
    """Repository for database operations on ArchitectureOption entities."""

    def __init__(self, db: Session):
        self.db = db

    def bulk_create(
        self,
        project_id: uuid.UUID,
        architectures_data: List[Dict[str, Any]],
    ) -> List[ArchitectureOption]:
        """Atomically persist multiple architecture options in a transaction."""
        created_records: List[ArchitectureOption] = []
        for data in architectures_data:
            arch = ArchitectureOption(
                id=uuid.uuid4(),
                project_id=project_id,
                name=data["name"],
                description=data["description"],
                components=data.get("components", []),
                connections=data.get("connections", []),
                pros=data.get("pros", []),
                cons=data.get("cons", []),
                risks=data.get("risks", []),
                estimated_cost=str(data.get("estimated_cost", "N/A")),
                estimated_latency=str(data.get("estimated_latency", "N/A")),
                complexity=str(data.get("complexity", "medium")),
                human_approval_required=bool(data.get("human_approval_required", False)),
                is_selected=bool(data.get("is_selected", False)),
            )
            self.db.add(arch)
            created_records.append(arch)

        self.db.commit()
        for a in created_records:
            self.db.refresh(a)
        return created_records

    def get_by_id(self, architecture_id: uuid.UUID) -> Optional[ArchitectureOption]:
        """Retrieve architecture option by UUID."""
        stmt = select(ArchitectureOption).where(ArchitectureOption.id == architecture_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_project_id(self, project_id: uuid.UUID) -> List[ArchitectureOption]:
        """Retrieve all architecture options for a project."""
        stmt = (
            select(ArchitectureOption)
            .where(ArchitectureOption.project_id == project_id)
            .order_by(ArchitectureOption.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_selected(self, project_id: uuid.UUID) -> Optional[ArchitectureOption]:
        """Retrieve the currently selected architecture option for a project."""
        stmt = select(ArchitectureOption).where(
            ArchitectureOption.project_id == project_id,
            ArchitectureOption.is_selected.is_(True),
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def select_architecture(
        self,
        project_id: uuid.UUID,
        architecture_id: uuid.UUID,
    ) -> Optional[ArchitectureOption]:
        """
        Atomically mark the requested architecture as selected and unselect any previous selection.
        """
        target = self.get_by_id(architecture_id)
        if not target or target.project_id != project_id:
            return None

        # Reset all other options for this project
        self.db.execute(
            update(ArchitectureOption)
            .where(ArchitectureOption.project_id == project_id)
            .values(is_selected=False)
        )

        target.is_selected = True
        self.db.commit()
        self.db.refresh(target)
        return target

    def delete_by_project(self, project_id: uuid.UUID) -> int:
        """Delete all architecture options for a project."""
        stmt = delete(ArchitectureOption).where(ArchitectureOption.project_id == project_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount
