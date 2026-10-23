import io
import logging
from typing import Tuple, List, Dict, Any
from pypdf import PdfReader
from fastapi import HTTPException, UploadFile, status

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for handling PDF document validation and text extraction."""

    @staticmethod
    def validate_pdf_upload(file: UploadFile, content: bytes) -> None:
        """
        Validates:
        1. File size is within MAX_UPLOAD_MB.
        2. Filename has .pdf extension.
        3. File magic header starts with %PDF.
        """
        if len(content) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_MB}MB.",
            )

        filename = (file.filename or "").lower()
        if not filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF documents are supported (.pdf extension required).",
            )

        # Validate PDF magic header '%PDF'
        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file format. The file does not have a valid PDF header.",
            )

    @staticmethod
    def extract_text_from_pdf(content: bytes) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extracts readable text and page metadata from PDF bytes using pypdf.
        Returns:
            full_text (str): Combined text from all pages with page markers.
            pages (List[dict]): Page-by-page text mapping with page numbers.
        Raises:
            HTTPException 400 if PDF is corrupted or unreadable.
        """
        try:
            stream = io.BytesIO(content)
            reader = PdfReader(stream)
            total_pages = len(reader.pages)

            pages_data: List[Dict[str, Any]] = []
            extracted_parts: List[str] = []

            for idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                clean_page_text = page_text.strip()
                pages_data.append({"page": idx, "text": clean_page_text})
                if clean_page_text:
                    extracted_parts.append(f"--- Page {idx} ---\n{clean_page_text}")

            full_text = "\n\n".join(extracted_parts).strip()
            if not full_text:
                full_text = "[Notice: PDF contains no extractable text. May be scanned or image-based.]"

            return full_text, pages_data
        except Exception as exc:
            logger.error(f"Failed to extract text from PDF: {exc}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to read or parse PDF: {str(exc)}",
            )
