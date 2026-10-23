import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    original_filename: str
    file_type: str
    file_size: int
    upload_status: str = "success"


class DocumentCreate(DocumentBase):
    project_id: uuid.UUID
    stored_filename: str
    extracted_text: Optional[str] = None


class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    stored_filename: str
    extracted_text: Optional[str] = None
    created_at: datetime
