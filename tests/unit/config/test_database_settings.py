"""
Unit tests for enhanced DatabaseSettings configuration.

Tests validation, property methods, and configuration behavior
for the unified database settings system.
"""

import pytest
from pydantic import ValidationError

from src.agent_project.config.settings import DatabaseSettings


class TestDatabaseSettingsValidation:
    """Test validation methods for DatabaseSettings."""

    def test_valid_database_settings_creation(self):
        """Test creating valid database settings."""
        settings = DatabaseSettings(
            url="sqlite:///./data/test.db",
            echo=True,
            pool_size=10,
            pool_timeout=60,
            connect_timeout=30,
        )

        assert settings.url == "sqlite:///./data/test.db"
        assert settings.echo is True
        assert settings.pool_size == 10
        assert settings.pool_timeout == 60
        assert settings.connect_timeout == 30

    def test_default_values_with_explicit_settings(self):
        """Test default configuration values with explicit settings."""
        # Create settings without reading from environment
        settings = DatabaseSettings(
            # Don't pass url to test the default
        )

        # Test all the non-URL defaults that should work regardless of environment
        assert settings.echo is False
        assert settings.pool_size == 5
        assert settings.auto_migrate is True
        assert settings.pool_pre_ping is True
        assert settings.pool_timeout == 30
        assert settings.pool_recycle == 3600
        assert settings.max_overflow == 10
        assert settings.connect_timeout == 10
        assert settings.check_same_thread is False

    def test_explicit_database_url_override(self):
        """Test that explicitly provided URL overrides environment."""
        # Test that we can create settings with explicit URL regardless of environment
        settings = DatabaseSettings(url="sqlite:///./data/test_override.db")
        assert settings.url == "sqlite:///./data/test_override.db"

        # Test the validation works with the default URL format
        settings = DatabaseSettings(url="sqlite:///./data/agents.db")
        assert settings.url == "sqlite:///./data/agents.db"

    def test_pool_size_validation_positive(self):
        """Test pool size must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseSettings(pool_size=0)

        assert "Pool size must be positive" in str(exc_info.value)

    def test_pool_size_validation_maximum(self):
        """Test pool size cannot exceed maximum."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseSettings(pool_size=101)

        assert "Pool size cannot exceed 100 connections" in str(exc_info.value)

    def test_pool_timeout_validation_positive(self):
        """Test pool timeout must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseSettings(pool_timeout=0)

        assert "Pool timeout must be positive" in str(exc_info.value)

    def test_pool_timeout_validation_maximum(self):
        """Test pool timeout cannot exceed maximum."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseSettings(pool_timeout=301)

        assert "Pool timeout cannot exceed 300 seconds" in str(exc_info.value)

    def test_connect_timeout_validation_positive(self):
        """Test connection timeout must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseSettings(connect_timeout=0)

        assert "Connection timeout must be positive" in str(exc_info.value)

    def test_connect_timeout_validation_maximum(self):
        """Test connection timeout cannot exceed maximum."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseSettings(connect_timeout=61)

        assert "Connection timeout cannot exceed 60 seconds" in str(exc_info.value)

    def test_database_url_validation_empty(self):
        """Test database URL cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseSettings(url="")

        assert "Database URL cannot be empty" in str(exc_info.value)

    def test_database_url_validation_unsupported_scheme(self):
        """Test database URL must use supported scheme."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseSettings(url="unsupported://localhost/test")

        assert "Database URL must start with one of" in str(exc_info.value)

    @pytest.mark.parametrize(
        "url",
        [
            "sqlite:///./data/test.db",
            "sqlite:///:memory:",
            "postgresql://localhost/test",
            "mysql://localhost/test",
            "memory://",
        ],
    )
    def test_valid_database_urls(self, url):
        """Test various valid database URL formats."""
        settings = DatabaseSettings(url=url)
        assert settings.url == url


class TestDatabaseSettingsProperties:
    """Test property methods for DatabaseSettings."""

    def test_is_sqlite_property(self):
        """Test SQLite database detection."""
        sqlite_settings = DatabaseSettings(url="sqlite:///./data/test.db")
        postgres_settings = DatabaseSettings(url="postgresql://localhost/test")

        assert sqlite_settings.is_sqlite is True
        assert postgres_settings.is_sqlite is False

    def test_is_postgresql_property(self):
        """Test PostgreSQL database detection."""
        postgres_settings = DatabaseSettings(url="postgresql://localhost/test")
        sqlite_settings = DatabaseSettings(url="sqlite:///./data/test.db")

        assert postgres_settings.is_postgresql is True
        assert sqlite_settings.is_postgresql is False

    def test_is_mysql_property(self):
        """Test MySQL database detection."""
        mysql_settings = DatabaseSettings(url="mysql://localhost/test")
        sqlite_settings = DatabaseSettings(url="sqlite:///./data/test.db")

        assert mysql_settings.is_mysql is True
        assert sqlite_settings.is_mysql is False

    def test_is_memory_property(self):
        """Test memory database detection."""
        memory_settings = DatabaseSettings(url="memory://")
        sqlite_settings = DatabaseSettings(url="sqlite:///./data/test.db")

        assert memory_settings.is_memory is True
        assert sqlite_settings.is_memory is False

    def test_connection_args_sqlite(self):
        """Test connection args for SQLite database."""
        settings = DatabaseSettings(
            url="sqlite:///./data/test.db",
            check_same_thread=True,
            connect_timeout=20,
        )

        expected_args = {
            "check_same_thread": True,
            "timeout": 20,
        }

        assert settings.connection_args == expected_args

    def test_connection_args_postgresql(self):
        """Test connection args for PostgreSQL database."""
        settings = DatabaseSettings(url="postgresql://localhost/test")

        # PostgreSQL should have empty connection args
        assert settings.connection_args == {}

    def test_connection_args_memory(self):
        """Test connection args for memory database."""
        settings = DatabaseSettings(url="memory://")

        # Memory databases should have empty connection args
        assert settings.connection_args == {}

    def test_engine_kwargs_sqlite(self):
        """Test engine kwargs for SQLite database."""
        settings = DatabaseSettings(
            url="sqlite:///./data/test.db",
            echo=True,
            pool_pre_ping=False,
            check_same_thread=True,
        )

        kwargs = settings.engine_kwargs

        # SQLite should not include pooling settings
        assert kwargs["echo"] is True
        assert kwargs["pool_pre_ping"] is False
        assert kwargs["connect_args"]["check_same_thread"] is True
        assert "pool_size" not in kwargs
        assert "pool_timeout" not in kwargs

    def test_engine_kwargs_postgresql(self):
        """Test engine kwargs for PostgreSQL database."""
        settings = DatabaseSettings(
            url="postgresql://localhost/test",
            echo=True,
            pool_size=20,
            pool_timeout=60,
            pool_recycle=7200,
            max_overflow=15,
        )

        kwargs = settings.engine_kwargs

        # PostgreSQL should include all pooling settings
        assert kwargs["echo"] is True
        assert kwargs["pool_size"] == 20
        assert kwargs["pool_timeout"] == 60
        assert kwargs["pool_recycle"] == 7200
        assert kwargs["max_overflow"] == 15
        assert kwargs["connect_args"] == {}

    def test_engine_kwargs_memory(self):
        """Test engine kwargs for memory database."""
        settings = DatabaseSettings(
            url="memory://",
            echo=False,
            pool_pre_ping=True,
        )

        kwargs = settings.engine_kwargs

        # Memory databases should not include pooling settings
        assert kwargs["echo"] is False
        assert kwargs["pool_pre_ping"] is True
        assert kwargs["connect_args"] == {}
        assert "pool_size" not in kwargs
        assert "pool_timeout" not in kwargs


class TestDatabaseSettingsIntegration:
    """Test integration scenarios for DatabaseSettings."""

    def test_environment_variable_loading(self, monkeypatch):
        """Test loading settings from environment variables."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/testdb")
        monkeypatch.setenv("DATABASE_ECHO", "true")
        monkeypatch.setenv("DATABASE_POOL_SIZE", "15")
        monkeypatch.setenv("DATABASE_POOL_TIMEOUT", "45")

        settings = DatabaseSettings()

        assert settings.url == "postgresql://localhost/testdb"
        assert settings.echo is True
        assert settings.pool_size == 15
        assert settings.pool_timeout == 45

    def test_configuration_for_different_environments(self):
        """Test configuration suitable for different environments."""
        # Development configuration
        dev_settings = DatabaseSettings(
            url="sqlite:///./data/dev.db",
            echo=True,
            pool_size=1,
        )

        assert dev_settings.is_sqlite
        assert dev_settings.echo

        # Production configuration
        prod_settings = DatabaseSettings(
            url="postgresql://prod-host/app",
            echo=False,
            pool_size=20,
            pool_timeout=30,
            pool_recycle=3600,
        )

        assert prod_settings.is_postgresql
        assert not prod_settings.echo
        assert prod_settings.pool_size == 20

    def test_settings_serialization(self):
        """Test that settings can be serialized/deserialized."""
        original_settings = DatabaseSettings(
            url="postgresql://localhost/test",
            echo=True,
            pool_size=10,
        )

        # Convert to dict and back
        settings_dict = original_settings.model_dump()
        recreated_settings = DatabaseSettings(**settings_dict)

        assert recreated_settings.url == original_settings.url
        assert recreated_settings.echo == original_settings.echo
        assert recreated_settings.pool_size == original_settings.pool_size
