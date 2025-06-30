"""Tests for SQLAlchemy configuration module."""

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from src.agent_project.infrastructure.database.sqlalchemy_config import (
    DatabaseConfig,
    create_tables,
    drop_tables,
    get_engine,
    get_session,
    get_session_factory,
    initialize_database,
    reset_database,
    test_database_connectivity,
)


class TestDatabaseConfig:
    """Tests for DatabaseConfig class."""

    def test_database_config_creation(self):
        """Test creating DatabaseConfig instance."""
        config = DatabaseConfig(database_url="sqlite:///:memory:")
        assert config.database_url == "sqlite:///:memory:"
        assert config.kwargs == {}

    def test_database_config_with_kwargs(self):
        """Test creating DatabaseConfig with additional kwargs."""
        config = DatabaseConfig(database_url="sqlite:///:memory:", echo=True, pool_pre_ping=False)
        assert config.database_url == "sqlite:///:memory:"
        assert config.kwargs == {"echo": True, "pool_pre_ping": False}


class TestEngineAndSession:
    """Tests for engine and session management."""

    def test_get_engine(self):
        """Test getting database engine."""
        engine = get_engine()
        assert isinstance(engine, Engine)

    def test_get_session_factory(self):
        """Test getting session factory."""
        factory = get_session_factory()
        assert factory is not None

    def test_get_session(self):
        """Test getting database session."""
        session = get_session()
        assert isinstance(session, Session)
        session.close()

    def test_database_connectivity(self):
        """Test database connectivity."""
        # Should not raise any exceptions
        test_database_connectivity()


class TestDatabaseManagement:
    """Tests for database table management."""

    def test_create_tables(self):
        """Test creating database tables."""
        # Should not raise any exceptions
        create_tables()

    def test_drop_tables(self):
        """Test dropping database tables."""
        # Should not raise any exceptions
        drop_tables()

    def test_reset_database(self):
        """Test resetting database."""
        # Should not raise any exceptions
        reset_database()

    def test_initialize_database_without_config(self):
        """Test database initialization without config."""
        # Should not raise any exceptions
        initialize_database()

    def test_initialize_database_with_config(self):
        """Test database initialization with config."""
        config = DatabaseConfig(database_url="sqlite:///:memory:")
        initialize_database(config)

        # Test that database is accessible
        with get_session() as session:
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1


class TestDatabaseIntegration:
    """Integration tests for database functionality."""

    def test_full_database_lifecycle(self):
        """Test complete database lifecycle."""
        # Initialize with in-memory database
        config = DatabaseConfig(database_url="sqlite:///:memory:")
        initialize_database(config)

        # Test connectivity
        test_database_connectivity()

        # Test session usage
        with get_session() as session:
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1

        # Test table operations
        create_tables()
        drop_tables()
        reset_database()
