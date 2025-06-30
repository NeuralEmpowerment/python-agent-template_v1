"""SQLAlchemy configuration module."""

from typing import Any

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from src.agent_project.config.settings import get_settings

# Create base class for declarative models
Base = declarative_base()

# Global engine instance
_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Get or create the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database.url, **settings.database.engine_kwargs)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(bind=engine)
    return _session_factory


def get_session() -> Session:
    """Get a new database session."""
    session_factory = get_session_factory()
    return session_factory()


def create_tables() -> None:
    """Create all tables in the database."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """Drop all tables in the database."""
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)


def reset_database() -> None:
    """Drop and recreate all tables."""
    drop_tables()
    create_tables()


class DatabaseConfig:
    """Database configuration class for dependency injection."""

    def __init__(self, database_url: str, **kwargs: Any) -> None:
        """Initialize database configuration."""
        self.database_url = database_url
        self.kwargs = kwargs


def initialize_database(config: DatabaseConfig | None = None) -> None:
    """Initialize the database with the given configuration."""
    global _engine, _session_factory

    if config:
        _engine = create_engine(config.database_url, **config.kwargs)
        _session_factory = sessionmaker(bind=_engine)
    else:
        # Use settings-based configuration
        _engine = get_engine()
        _session_factory = get_session_factory()

    # Create tables
    create_tables()


def check_database_connectivity() -> None:
    """Check database connectivity by attempting a simple query."""
    try:
        engine = get_engine()
        with engine.connect() as connection:
            # Simple test query that works on all databases
            connection.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError(f"Database connectivity test failed: {e}") from e
