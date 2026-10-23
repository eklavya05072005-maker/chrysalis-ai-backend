import logging
from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool

from backend.app.core.config import settings
from backend.app.db.base import Base

logger = logging.getLogger(__name__)


def _create_resilient_engine():
    """
    Creates an engine according to configuration.
    If PostgreSQL is configured but unreachable (e.g. in offline dev or CI environments),
    transparently falls back to local SQLite to ensure uninterrupted development.
    """
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        kwargs = {"echo": settings.DEBUG, "connect_args": connect_args}
        if ":memory:" in settings.DATABASE_URL:
            kwargs["poolclass"] = StaticPool
        return create_engine(settings.DATABASE_URL, **kwargs)

    # Attempt PostgreSQL connection with a short timeout
    try:
        pg_engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"connect_timeout": 2},
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_timeout=3,
            echo=settings.DEBUG,
        )
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Connected to PostgreSQL database at %s", settings.DATABASE_URL)
        return pg_engine
    except Exception as exc:
        logger.warning(
            "PostgreSQL database unreachable (%s). Automatically falling back to local SQLite database at sqlite:///./data/chrysalis_dev.db",
            exc,
        )
        settings.data_path  # ensure data directory exists
        sqlite_url = "sqlite:///./data/chrysalis_dev.db"
        return create_engine(
            sqlite_url,
            connect_args={"check_same_thread": False},
            echo=settings.DEBUG,
        )


engine = _create_resilient_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def init_db(target_engine=None) -> None:
    """Initialize database tables from ORM metadata."""
    eng = target_engine or engine
    try:
        import backend.app.db.models  # ensure models are registered
        Base.metadata.create_all(bind=eng)
        logger.info("Database schema initialized successfully.")
    except Exception as exc:
        logger.error("Failed to initialize database schema: %s", exc)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a SQLAlchemy database session per request.
    Rolls back any uncommitted transactions on exception and closes the session reliably.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as exc:
        db.rollback()
        logger.error(f"Database session rolled back due to exception: {exc}")
        raise
    finally:
        db.close()


def check_db_connectivity(target_engine=None) -> Tuple[bool, str]:
    """
    Checks if the database is reachable and can execute queries.
    Returns (True, 'connected') or (False, error_details).
    """
    eng = target_engine or engine
    try:
        with eng.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "connected"
    except Exception as exc:
        logger.warning(f"Database connectivity check failed: {exc}")
        return False, str(exc)
