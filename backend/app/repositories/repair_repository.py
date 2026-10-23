"""Repository for RepairLog database operations."""

from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.db.models import RepairLog


class RepairRepository:
    """Repository handling persistence of code repair iteration logs."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        project_id: uuid.UUID,
        attempt_number: int,
        initial_status: str,
        failure_diagnostics: List[str],
        patches: List[Dict[str, Any]],
        rerun_status: str,
        checks_rerun: List[str],
        success: bool,
        summary: str,
    ) -> RepairLog:
        """Create and persist a repair log record."""
        log = RepairLog(
            id=uuid.uuid4(),
            project_id=project_id,
            attempt_number=attempt_number,
            initial_status=initial_status,
            failure_diagnostics=failure_diagnostics,
            patches=patches,
            rerun_status=rerun_status,
            checks_rerun=checks_rerun,
            success=success,
            summary=summary,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_by_project_id(self, project_id: uuid.UUID) -> List[RepairLog]:
        """List repair logs for a project ordered by creation time descending."""
        stmt = (
            select(RepairLog)
            .where(RepairLog.project_id == project_id)
            .order_by(desc(RepairLog.created_at))
        )
        return list(self.db.execute(stmt).scalars().all())
