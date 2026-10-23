from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any, Optional

from backend.app.core.config import settings
from backend.app.db.database import check_db_connectivity

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    database: Dict[str, Any]
    version: str
    app_name: str
    environment: str
    llm_provider: str
    gemini_model: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns the operational status of Chrysalis AI backend, database connectivity, and configured AI models.",
)
def get_health() -> HealthResponse:
    db_connected, db_message = check_db_connectivity()

    overall_status = "healthy" if db_connected else "degraded"

    return HealthResponse(
        status=overall_status,
        database={
            "status": "connected" if db_connected else "disconnected",
            "message": db_message,
        },
        version=settings.VERSION,
        app_name=settings.app_name,
        environment=settings.environment,
        llm_provider=settings.llm_provider,
        gemini_model=settings.gemini_model,
    )
