import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from backend.app.db.models import Requirement


class RequirementRepository:
    """Repository for database operations on Requirement entities."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        project_id: uuid.UUID,
        title: str,
        description: str,
        requirement_type: str,
        priority: str,
        confidence_score: float,
        source_page: Optional[int] = None,
        evidence_text: Optional[str] = None,
    ) -> Requirement:
        """Create a single Requirement record."""
        req = Requirement(
            id=uuid.uuid4(),
            project_id=project_id,
            title=title,
            description=description,
            requirement_type=requirement_type,
            priority=priority,
            confidence_score=confidence_score,
            source_page=source_page,
            evidence_text=evidence_text,
        )
        self.db.add(req)
        self.db.commit()
        self.db.refresh(req)
        return req

    def bulk_create(
        self,
        project_id: uuid.UUID,
        requirements_data: List[Dict[str, Any]],
    ) -> List[Requirement]:
        """Atomically persist multiple requirements for a project in a transaction."""
        created_records: List[Requirement] = []
        for data in requirements_data:
            req = Requirement(
                id=uuid.uuid4(),
                project_id=project_id,
                title=data["title"],
                description=data["description"],
                requirement_type=data["requirement_type"],
                priority=data["priority"],
                confidence_score=float(data["confidence_score"]),
                source_page=data.get("source_page"),
                evidence_text=data.get("evidence_text"),
            )
            self.db.add(req)
            created_records.append(req)

        self.db.commit()
        for r in created_records:
            self.db.refresh(r)
        return created_records

    def get_by_project_id(self, project_id: uuid.UUID) -> List[Requirement]:
        """Retrieve all requirements for a project ordered by creation time."""
        stmt = (
            select(Requirement)
            .where(Requirement.project_id == project_id)
            .order_by(Requirement.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def delete_by_project(self, project_id: uuid.UUID) -> int:
        """Delete all existing requirements for a project (for idempotent re-analysis)."""
        stmt = delete(Requirement).where(Requirement.project_id == project_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount
