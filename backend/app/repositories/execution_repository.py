"""Repository for ExecutionRun database operations."""

from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.db.models import ExecutionRun


class ExecutionRepository:
    """Repository handling persistence of isolated execution runs."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        project_id: uuid.UUID,
        status: str,
        runtime: str,
        exit_code: Optional[int],
        stdout: Optional[str],
        stderr: Optional[str],
        elapsed_time_seconds: float,
        timed_out: bool,
        resource_limit_hit: bool,
        network_isolated: bool,
        checks_performed: List[str],
        message: str,
        run_id: Optional[uuid.UUID] = None,
    ) -> ExecutionRun:
        """Create and persist a new execution run record."""
        run = ExecutionRun(
            id=run_id or uuid.uuid4(),
            project_id=project_id,
            status=status,
            runtime=runtime,
            exit_code=exit_code,
            stdout=stdout or "",
            stderr=stderr or "",
            elapsed_time_seconds=elapsed_time_seconds,
            timed_out=timed_out,
            resource_limit_hit=resource_limit_hit,
            network_isolated=network_isolated,
            checks_performed=checks_performed,
            message=message,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_by_id(self, run_id: uuid.UUID) -> Optional[ExecutionRun]:
        """Retrieve run by ID."""
        stmt = select(ExecutionRun).where(ExecutionRun.id == run_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_project_id(self, project_id: uuid.UUID) -> List[ExecutionRun]:
        """List execution runs for a project ordered by creation time descending."""
        stmt = (
            select(ExecutionRun)
            .where(ExecutionRun.project_id == project_id)
            .order_by(desc(ExecutionRun.created_at))
        )
        return list(self.db.execute(stmt).scalars().all())
