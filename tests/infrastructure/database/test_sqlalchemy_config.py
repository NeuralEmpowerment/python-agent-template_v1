"""Tests for SQLAlchemy configuration module."""

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from src.agent_project.infrastructure.database.sqlalchemy_config import (
    DatabaseConfig,
    check_database_connectivity,
    create_tables,
    drop_tables,
    get_engine,
    get_session,
    get_session_factory,
    initialize_database,
    reset_database,
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

    def test_get_engine(self, test_database_config, test_database_reset):
        """Test getting database engine."""
        # Initialize with test configuration
        initialize_database(test_database_config)
        engine = get_engine()
        assert isinstance(engine, Engine)

    def test_get_session_factory(self, test_database_config, test_database_reset):
        """Test getting session factory."""
        # Initialize with test configuration
        initialize_database(test_database_config)
        factory = get_session_factory()
        assert factory is not None

    def test_get_session(self, test_database_config, test_database_reset):
        """Test getting database session."""
        # Initialize with test configuration
        initialize_database(test_database_config)
        session = get_session()
        assert isinstance(session, Session)
        session.close()

    def test_database_connectivity(self, test_database_config, test_database_reset):
        """Test database connectivity."""
        # Initialize with test configuration
        initialize_database(test_database_config)
        # Should not raise any exceptions
        check_database_connectivity()


class TestDatabaseManagement:
    """Tests for database table management."""

    def test_create_tables(self, test_database_config, test_database_reset):
        """Test creating database tables."""
        # Initialize with test configuration
        initialize_database(test_database_config)
        # Should not raise any exceptions
        create_tables()

    def test_drop_tables(self, test_database_config, test_database_reset):
        """Test dropping database tables."""
        # Initialize with test configuration
        initialize_database(test_database_config)
        # Should not raise any exceptions
        drop_tables()

    def test_reset_database(self, test_database_config, test_database_reset):
        """Test resetting database."""
        # Initialize with test configuration
        initialize_database(test_database_config)
        # Should not raise any exceptions
        reset_database()

    def test_initialize_database_without_config(self, test_database_config, test_database_reset):
        """Test database initialization without config."""
        # First set up test configuration, then test without passing config
        initialize_database(test_database_config)
        # Should not raise any exceptions - will use already initialized engine
        initialize_database()

    def test_initialize_database_with_config(self, test_database_reset):
        """Test database initialization with config."""
        config = DatabaseConfig(database_url="sqlite:///:memory:")
        initialize_database(config)

        # Test that database is accessible
        with get_session() as session:
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1


class TestDatabaseIntegration:
    """Integration tests for database functionality."""

    def test_full_database_lifecycle(self, test_database_config, test_database_reset):
        """Test complete database lifecycle."""
        # Initialize with test configuration
        initialize_database(test_database_config)

        # Test connectivity
        check_database_connectivity()

        # Test session usage
        with get_session() as session:
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1

        # Test table operations
        create_tables()
        drop_tables()
        reset_database()
