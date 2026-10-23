import uuid
from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from backend.app.db.models import Document


class DocumentRepository:
    """Repository for database operations on Document entities."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        project_id: uuid.UUID,
        original_filename: str,
        stored_filename: str,
        file_type: str,
        file_size: int,
        extracted_text: Optional[str] = None,
        upload_status: str = "success",
    ) -> Document:
        """Create and persist a new Document record."""
        doc = Document(
            id=uuid.uuid4(),
            project_id=project_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_type=file_type,
            file_size=file_size,
            extracted_text=extracted_text,
            upload_status=upload_status,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        """Retrieve document by UUID."""
        stmt = select(Document).where(Document.id == document_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_project_id(self, project_id: uuid.UUID) -> List[Document]:
        """Retrieve all documents belonging to a project."""
        stmt = (
            select(Document)
            .where(Document.project_id == project_id)
            .order_by(Document.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def delete_by_project(self, project_id: uuid.UUID) -> int:
        """Delete all documents for a project."""
        stmt = delete(Document).where(Document.project_id == project_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount
