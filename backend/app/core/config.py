"""Application settings and environment configuration for Chrysalis AI.

Reads configuration from environment variables and an optional .env file.
Secrets such as API keys are stored as SecretStr to prevent accidental exposure
in logs or tracebacks.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Literal
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core Application Settings
    app_name: str = "Chrysalis AI Engine"
    PROJECT_NAME: str = "Chrysalis AI Backend"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"
    environment: Literal["development", "staging", "production", "test"] = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api"

    # Database Configuration (PostgreSQL with SQLite dev fallback)
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres@localhost:5432/chrysalis_db",
        description="SQLAlchemy database connection string with Psycopg 3 driver or SQLite fallback",
    )

    # Security & CORS
    FRONTEND_ORIGIN: str = Field(
        default="http://localhost:3000",
        description="Frontend URL or comma-separated list of allowed origins",
    )

    # Storage Settings
    DATA_DIR: str = Field(
        default="./data",
        description="Base path for physical file storage",
    )
    MAX_UPLOAD_MB: int = Field(
        default=10,
        description="Maximum allowed PDF file upload size in megabytes",
    )

    # LLM Settings
    llm_provider: Literal["gemini", "mock"] = "gemini"
    gemini_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Google AI Studio API key for Gemini access",
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        description="Configurable Gemini model identifier (e.g., gemini-2.0-flash, gemini-1.5-pro)",
    )
    llm_timeout_seconds: float = Field(
        default=60.0,
        ge=5.0,
        le=300.0,
        description="Timeout for LLM API calls in seconds",
    )
    llm_temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Sampling temperature for deterministic structured generation",
    )
    llm_max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum retry attempts on transient network or rate-limit errors",
    )

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated frontend origins if multiple provided."""
        if "," in self.FRONTEND_ORIGIN:
            return [origin.strip() for origin in self.FRONTEND_ORIGIN.split(",") if origin.strip()]
        return [self.FRONTEND_ORIGIN.strip()]

    @property
    def max_upload_bytes(self) -> int:
        """Convert MAX_UPLOAD_MB to bytes."""
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def data_path(self) -> Path:
        """Return Path object for base DATA_DIR and ensure it exists."""
        p = Path(self.DATA_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "test"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()


# Default singleton settings instance for module-level imports
settings = get_settings()

