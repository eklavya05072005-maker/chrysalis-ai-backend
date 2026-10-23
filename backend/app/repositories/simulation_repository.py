import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from backend.app.db.models import SimulationResult


class SimulationRepository:
    """Repository for database operations on SimulationResult entities."""

    def __init__(self, db: Session):
        self.db = db

    def bulk_create(
        self,
        project_id: uuid.UUID,
        simulations_data: List[Dict[str, Any]],
    ) -> List[SimulationResult]:
        """Atomically persist multiple simulation results in a transaction."""
        created_records: List[SimulationResult] = []
        for data in simulations_data:
            sim = SimulationResult(
                id=uuid.uuid4(),
                project_id=project_id,
                architecture_id=data["architecture_id"],
                scenario_name=data["scenario_name"],
                input_data=data.get("input_data", {}),
                expected_outcome=data["expected_outcome"],
                simulated_outcome=data["simulated_outcome"],
                result_status=data.get("result_status", "pass"),
                metrics=data.get("metrics", {}),
            )
            self.db.add(sim)
            created_records.append(sim)

        self.db.commit()
        for s in created_records:
            self.db.refresh(s)
        return created_records

    def get_by_project_id(self, project_id: uuid.UUID) -> List[SimulationResult]:
        """Retrieve all simulation results for a project."""
        stmt = (
            select(SimulationResult)
            .where(SimulationResult.project_id == project_id)
            .order_by(SimulationResult.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_architecture_id(self, architecture_id: uuid.UUID) -> List[SimulationResult]:
        """Retrieve all simulation results for a specific architecture option."""
        stmt = (
            select(SimulationResult)
            .where(SimulationResult.architecture_id == architecture_id)
            .order_by(SimulationResult.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def delete_by_project(self, project_id: uuid.UUID) -> int:
        """Delete all simulation results for a project (for idempotent re-simulation)."""
        stmt = delete(SimulationResult).where(SimulationResult.project_id == project_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount
