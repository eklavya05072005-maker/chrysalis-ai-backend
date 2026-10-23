import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session

from backend.app.db.models import GeneratedFile


class GenerationRepository:
    """Repository for database operations on GeneratedFile entities."""

    def __init__(self, db: Session):
        self.db = db

    def bulk_create(
        self,
        project_id: uuid.UUID,
        files_data: List[Dict[str, Any]],
    ) -> List[GeneratedFile]:
        """Atomically persist generated files metadata in a transaction."""
        created_records: List[GeneratedFile] = []
        for data in files_data:
            gen_file = GeneratedFile(
                id=uuid.uuid4(),
                project_id=project_id,
                relative_path=data["relative_path"],
                filename=data["filename"],
                language=data.get("language", "text"),
                file_size=int(data.get("file_size", 0)),
                validation_status=data.get("validation_status", "pending"),
            )
            self.db.add(gen_file)
            created_records.append(gen_file)

        self.db.commit()
        for f in created_records:
            self.db.refresh(f)
        return created_records

    def get_by_project_id(self, project_id: uuid.UUID) -> List[GeneratedFile]:
        """Retrieve all generated files metadata for a project."""
        stmt = (
            select(GeneratedFile)
            .where(GeneratedFile.project_id == project_id)
            .order_by(GeneratedFile.relative_path.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_validation_status(
        self,
        file_id: uuid.UUID,
        validation_status: str,
    ) -> Optional[GeneratedFile]:
        """Update the validation status of a generated file."""
        stmt = select(GeneratedFile).where(GeneratedFile.id == file_id)
        gen_file = self.db.execute(stmt).scalar_one_or_none()
        if not gen_file:
            return None

        gen_file.validation_status = validation_status
        self.db.commit()
        self.db.refresh(gen_file)
        return gen_file

    def bulk_update_validation(
        self,
        project_id: uuid.UUID,
        status_map: Dict[str, str],
    ) -> int:
        """
        Update validation_status across multiple files by relative_path.
        status_map is {relative_path: "passed" | "failed"}.
        """
        updated_count = 0
        for rel_path, val_status in status_map.items():
            stmt = (
                update(GeneratedFile)
                .where(
                    GeneratedFile.project_id == project_id,
                    GeneratedFile.relative_path == rel_path,
                )
                .values(validation_status=val_status)
            )
            res = self.db.execute(stmt)
            updated_count += res.rowcount

        self.db.commit()
        return updated_count

    def delete_by_project(self, project_id: uuid.UUID) -> int:
        """Delete all generated files metadata for a project (for idempotent re-generation)."""
        stmt = delete(GeneratedFile).where(GeneratedFile.project_id == project_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount
