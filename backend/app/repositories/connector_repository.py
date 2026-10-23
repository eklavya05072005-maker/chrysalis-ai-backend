"""Repository for Connector database operations."""

from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from backend.app.db.models import ConnectorModel


class ConnectorRepository:
    """Repository handling persistence of configured connectors."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        project_id: uuid.UUID,
        connector_type: str,
        name: str,
        is_mock: bool,
        is_read_only: bool,
        requires_approval: bool,
        allowed_endpoints: List[str],
        allowed_methods: List[str],
        allowed_tools: List[str],
        timeout_seconds: float,
        rate_limit_per_minute: int,
        max_response_size_kb: int,
        config_data: Dict[str, Any],
        state: str = "configured",
    ) -> ConnectorModel:
        """Create and persist a new connector."""
        connector = ConnectorModel(
            id=uuid.uuid4(),
            project_id=project_id,
            connector_type=connector_type,
            name=name,
            is_mock=is_mock,
            is_read_only=is_read_only,
            requires_approval=requires_approval,
            is_approved=not requires_approval,
            allowed_endpoints=allowed_endpoints,
            allowed_methods=allowed_methods,
            allowed_tools=allowed_tools,
            timeout_seconds=timeout_seconds,
            rate_limit_per_minute=rate_limit_per_minute,
            max_response_size_kb=max_response_size_kb,
            config_data=config_data,
            state=state,
        )
        self.db.add(connector)
        self.db.commit()
        self.db.refresh(connector)
        return connector

    def get_by_id(self, connector_id: uuid.UUID) -> Optional[ConnectorModel]:
        """Retrieve connector by ID."""
        stmt = select(ConnectorModel).where(ConnectorModel.id == connector_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_project_and_name(self, project_id: uuid.UUID, name: str) -> Optional[ConnectorModel]:
        """Retrieve connector by project ID and name."""
        stmt = select(ConnectorModel).where(
            ConnectorModel.project_id == project_id,
            ConnectorModel.name == name,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_project_id(self, project_id: uuid.UUID) -> List[ConnectorModel]:
        """List all connectors for a project."""
        stmt = (
            select(ConnectorModel)
            .where(ConnectorModel.project_id == project_id)
            .order_by(ConnectorModel.created_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_state(self, connector_id: uuid.UUID, state: str) -> Optional[ConnectorModel]:
        """Update connector state."""
        connector = self.get_by_id(connector_id)
        if connector:
            connector.state = state
            self.db.commit()
            self.db.refresh(connector)
        return connector

    def approve(self, connector_id: uuid.UUID) -> Optional[ConnectorModel]:
        """Grant human approval for connector."""
        connector = self.get_by_id(connector_id)
        if connector:
            connector.is_approved = True
            self.db.commit()
            self.db.refresh(connector)
        return connector
