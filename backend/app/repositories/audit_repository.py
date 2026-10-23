"""Repository for AuditEvent database operations."""

from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.db.models import AuditEventModel


class AuditRepository:
    """Repository handling persistence of system audit events."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        project_id: uuid.UUID,
        event_type: str,
        actor: str = "system",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEventModel:
        """Create and persist an audit event."""
        event = AuditEventModel(
            id=uuid.uuid4(),
            project_id=project_id,
            event_type=event_type,
            actor=actor,
            details=details or {},
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_by_project_id(self, project_id: uuid.UUID, limit: int = 50) -> List[AuditEventModel]:
        """List audit events for a project ordered by creation time descending."""
        stmt = (
            select(AuditEventModel)
            .where(AuditEventModel.project_id == project_id)
            .order_by(desc(AuditEventModel.created_at))
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
