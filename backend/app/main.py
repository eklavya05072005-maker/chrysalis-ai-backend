"""Chrysalis AI backend entry point.

Provides health checks, CORS middleware, and complete end-to-end routing
for requirements analysis, task classification, architecture search, simulation,
code generation, validation, and package export.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings, get_settings
from backend.app.db.database import check_db_connectivity, init_db
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.projects import router as projects_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
)
logger = logging.getLogger("chrysalis.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    logger.info("Initializing Chrysalis AI Backend...")
    db_ok, msg = check_db_connectivity()
    if db_ok:
        logger.info("Database connection verified successfully.")
    else:
        logger.warning(f"Database connection check warning: {msg}")

    # Ensure schema initialized and storage directories exist
    init_db()
    settings.data_path

    yield

    logger.info("Shutting down Chrysalis AI Backend...")


def create_application() -> FastAPI:
    """Factory function for FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "AI-powered middleware platform that analyzes software requirements "
            "and generates new software incorporating appropriate Agentic AI workflows."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )

    # Global unhandled exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred. Please contact the administrator or check server logs."
            },
        )

    # Root /health endpoint for basic monitoring and backwards compatibility
    @app.get("/health", tags=["System"])
    async def root_health_check():
        db_ok, _ = check_db_connectivity()
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "environment": settings.environment,
            "llm_provider": settings.llm_provider,
            "gemini_model": settings.gemini_model,
            "database_connected": db_ok,
            "version": settings.VERSION,
        }

    # Mount API Routers under /api
    app.include_router(health_router, prefix="/api")
    app.include_router(projects_router, prefix="/api")

    return app


app = create_application()
