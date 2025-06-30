"""
Application settings module.

This module contains the settings classes for the application, using Pydantic Settings' BaseSettings
for environment variable loading, validation, and documentation.
"""

from enum import Enum
from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from src.agent_project.config.constants import (
    DEFAULT_API_DESCRIPTION,
    DEFAULT_API_TITLE,
    DEFAULT_API_VERSION,
    DEFAULT_HOST,
    DEFAULT_LOG_LEVEL,
    DEFAULT_PORT,
    # ZenML constants removed
    ENV_DEVELOPMENT,
    ENV_PRODUCTION,
    ENV_TESTING,
)

# Transcription settings removed - no longer needed for agent template


class StorageBackend(str, Enum):
    """Available storage backends."""

    LOCAL = "local"
    SUPABASE = "supabase"


class DatabaseSettings(BaseSettings):
    """
    Database configuration settings.

    These settings control database connection and behavior, including
    SQLAlchemy-specific connection pooling and timeout configurations.
    """

    url: str = Field(
        default="sqlite:///./data/agents.db",
        description="Database connection URL",
    )

    pool_size: int = Field(
        default=5,
        description="Database connection pool size",
    )

    echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy query logging",
    )

    auto_migrate: bool = Field(
        default=True,
        description="Automatically apply database migrations on startup",
    )

    # SQLAlchemy-specific connection settings
    pool_pre_ping: bool = Field(
        default=True,
        description="Enable connection health checks before use",
    )

    pool_timeout: int = Field(
        default=30,
        description="Pool checkout timeout in seconds",
    )

    pool_recycle: int = Field(
        default=3600,
        description="Connection recycle time in seconds (1 hour)",
    )

    max_overflow: int = Field(
        default=10,
        description="Maximum connections beyond pool_size",
    )

    # Connection-specific settings
    connect_timeout: int = Field(
        default=10,
        description="Database connection timeout in seconds",
    )

    check_same_thread: bool = Field(
        default=False,
        description="SQLite check_same_thread parameter",
    )

    @field_validator("pool_size")
    @classmethod
    def validate_pool_size(cls, v: int) -> int:
        """Validate pool size is reasonable."""
        if v <= 0:
            raise ValueError("Pool size must be positive")
        if v > 100:
            raise ValueError("Pool size cannot exceed 100 connections")
        return v

    @field_validator("pool_timeout")
    @classmethod
    def validate_pool_timeout(cls, v: int) -> int:
        """Validate pool timeout is reasonable."""
        if v <= 0:
            raise ValueError("Pool timeout must be positive")
        if v > 300:  # 5 minutes max
            raise ValueError("Pool timeout cannot exceed 300 seconds")
        return v

    @field_validator("connect_timeout")
    @classmethod
    def validate_connect_timeout(cls, v: int) -> int:
        """Validate connection timeout is reasonable."""
        if v <= 0:
            raise ValueError("Connection timeout must be positive")
        if v > 60:  # 1 minute max
            raise ValueError("Connection timeout cannot exceed 60 seconds")
        return v

    @field_validator("url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v:
            raise ValueError("Database URL cannot be empty")

        # Check for supported database schemes
        supported_schemes = ["sqlite", "postgresql", "mysql", "memory"]
        if not any(v.startswith(f"{scheme}://") for scheme in supported_schemes):
            raise ValueError(f"Database URL must start with one of: {supported_schemes}")

        return v

    @property
    def is_sqlite(self) -> bool:
        """Check if database is SQLite."""
        return self.url.startswith("sqlite:")

    @property
    def is_postgresql(self) -> bool:
        """Check if database is PostgreSQL."""
        return self.url.startswith("postgresql:")

    @property
    def is_mysql(self) -> bool:
        """Check if database is MySQL."""
        return self.url.startswith("mysql:")

    @property
    def is_memory(self) -> bool:
        """Check if database is in-memory."""
        return self.url.startswith("memory:")

    @property
    def connection_args(self) -> Dict[str, Any]:
        """Get database-specific connection arguments."""
        if self.is_sqlite:
            return {
                "check_same_thread": self.check_same_thread,
                "timeout": self.connect_timeout,
            }
        elif self.is_memory:
            # Memory databases are treated as lightweight, no special args needed
            return {}
        return {}

    @property
    def engine_kwargs(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine creation arguments."""
        kwargs = {
            "echo": self.echo,
            "pool_pre_ping": self.pool_pre_ping,
            "connect_args": self.connection_args,
        }

        # Only add pooling settings for non-SQLite and non-memory databases
        if not self.is_sqlite and not self.is_memory:
            kwargs.update(
                {
                    "pool_size": self.pool_size,
                    "pool_timeout": self.pool_timeout,
                    "pool_recycle": self.pool_recycle,
                    "max_overflow": self.max_overflow,
                }
            )

        return kwargs

    model_config = {
        "env_prefix": "DATABASE_",
        "case_sensitive": False,
        "env_file": ".env",
        "extra": "ignore",
    }


class StorageSettings(BaseSettings):
    """
    File storage configuration settings.

    These settings control how files are stored and managed for the agent template.
    """

    backend: StorageBackend = Field(
        default=StorageBackend.LOCAL,
        description="Storage backend to use",
    )

    local_path: str = Field(
        default="./data/uploads",
        description="Local storage directory path",
    )

    max_file_size_mb: int = Field(
        default=25,
        description="Maximum file size in MB",
    )

    allowed_formats: List[str] = Field(
        default=["txt", "json", "csv", "pdf", "md"],
        description="Allowed file formats",
    )

    # Supabase storage settings
    supabase_bucket: str = Field(
        default="agent-files",
        description="Supabase storage bucket name",
    )

    model_config = {
        "env_prefix": "STORAGE_",
        "case_sensitive": False,
        "env_file": ".env",
        "extra": "ignore",
    }


# TranscriptionSettings removed - not needed for agent template


class SupabaseSettings(BaseSettings):
    """
    Supabase configuration settings.

    These settings are required when using Supabase as storage or database backend.
    """

    url: Optional[str] = Field(
        default=None,
        description="Supabase project URL",
    )

    key: Optional[str] = Field(
        default=None,
        description="Supabase anon/public API key",
    )

    service_role_key: Optional[str] = Field(
        default=None,
        description="Supabase service role key (for admin operations)",
    )

    jwt_secret: Optional[str] = Field(
        default=None,
        description="Supabase JWT secret",
    )

    def validate_for_usage(self) -> None:
        """Validate that required Supabase settings are present when needed."""
        if not self.url:
            raise ValueError(
                "SUPABASE_URL is required when using Supabase backend. "
                "Get this from your Supabase project dashboard."
            )
        if not self.key:
            raise ValueError(
                "SUPABASE_KEY is required when using Supabase backend. "
                "Use the 'anon/public' key from your Supabase project dashboard."
            )

    model_config = {
        "env_prefix": "SUPABASE_",
        "case_sensitive": False,
        "env_file": ".env",
        "extra": "ignore",
    }


# ZenMLSettings removed - not needed for agent template


class APISettings(BaseSettings):
    """
    FastAPI-specific settings.

    These settings control the FastAPI application configuration.
    """

    title: str = Field(
        default=DEFAULT_API_TITLE,
        description="API title used in documentation",
    )

    description: str = Field(
        default=DEFAULT_API_DESCRIPTION,
        description="API description used in documentation",
    )

    version: str = Field(default=DEFAULT_API_VERSION, description="API version")

    host: str = Field(default=DEFAULT_HOST, description="Host to bind the API server to")

    port: int = Field(default=DEFAULT_PORT, description="Port to bind the API server to")

    log_level: str = Field(
        default=DEFAULT_LOG_LEVEL,
        description="Logging level for the API",
    )

    environment: str = Field(
        default=ENV_DEVELOPMENT,
        description="Environment (development, production, testing)",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """
        Validate the environment value.

        Args:
            v: The environment value to validate

        Returns:
            str: The validated environment value

        Raises:
            ValueError: If the environment is not one of the allowed values
        """
        allowed_environments = [ENV_DEVELOPMENT, ENV_PRODUCTION, ENV_TESTING]
        if v.lower() not in allowed_environments:
            raise ValueError(f"Environment must be one of {allowed_environments}")
        return v.lower()

    @property
    def is_development(self) -> bool:
        """
        Check if the environment is development.

        Returns:
            bool: True if the environment is development, False otherwise
        """
        return self.environment.lower() == ENV_DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """
        Check if the environment is production.

        Returns:
            bool: True if the environment is production, False otherwise
        """
        return self.environment.lower() == ENV_PRODUCTION

    @property
    def is_testing(self) -> bool:
        """
        Check if the environment is testing.

        Returns:
            bool: True if the environment is testing, False otherwise
        """
        return self.environment.lower() == ENV_TESTING

    model_config = {
        "env_prefix": "",
        "case_sensitive": False,
        "env_file": ".env",
        "extra": "ignore",
    }


class OpenAISettings(BaseSettings):
    """
    OpenAI-specific settings.

    These settings control the OpenAI API configuration.
    """

    api_key: Optional[str] = Field(default=None, description="OpenAI API key", alias="OPENAI_API_KEY")

    model_config = {
        "env_prefix": "",
        "case_sensitive": False,
        "env_file": ".env",
        "extra": "ignore",
    }


class AppSettings(BaseSettings):
    """
    Main application settings.

    This class combines all other settings classes and provides a single point of access
    for all application settings.
    """

    api: APISettings = APISettings()
    openai: OpenAISettings = OpenAISettings()

    # Additional application-wide settings can be added here
    objc_disable_initialize_fork_safety: bool = Field(
        default=True,
        description="Disable fork safety on macOS (needed for multiprocessing)",
    )

    database: DatabaseSettings = DatabaseSettings()
    storage: StorageSettings = StorageSettings()
    supabase: SupabaseSettings = SupabaseSettings()

    def validate_configuration(self) -> None:
        """
        Validate the complete configuration for common issues.

        Raises:
            ValueError: If configuration is invalid with helpful error messages
        """
        # Validate OpenAI configuration for agents
        if not self.openai.api_key:
            # Only warn in development, but don't fail - allows testing without API key
            if self.api.environment.lower() in ("production", "staging"):
                raise ValueError(
                    "OPENAI_API_KEY is required in production/staging environments. "
                    "Get your API key from https://platform.openai.com/api-keys"
                )

        # Validate Supabase configuration
        if self.storage.backend == StorageBackend.SUPABASE or "supabase" in self.database.url.lower():
            self.supabase.validate_for_usage()

        # Validate storage directory for local backend
        if self.storage.backend == StorageBackend.LOCAL:
            from pathlib import Path

            storage_path = Path(self.storage.local_path)
            try:
                storage_path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                raise ValueError(
                    f"Cannot create storage directory '{self.storage.local_path}'. "
                    "Check permissions or set STORAGE_LOCAL_PATH to a writable directory."
                )

        # Validate database directory for SQLite
        if self.database.url.startswith("sqlite:"):
            from pathlib import Path

            # Extract path from SQLite URL
            db_path = self.database.url.replace("sqlite:///", "")
            db_dir = Path(db_path).parent
            try:
                db_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                raise ValueError(
                    f"Cannot create database directory '{db_dir}'. "
                    "Check permissions or set DATABASE_URL to a writable location."
                )

        # Test actual database connectivity (works with any configured database type)
        try:
            from src.agent_project.infrastructure.database.sqlalchemy_config import (
                test_database_connectivity,
            )

            test_database_connectivity()
        except Exception as e:
            raise ValueError(f"Database connectivity test failed: {e}")

    def get_startup_info(self) -> Dict[str, Any]:
        """Get startup information for logging."""
        return {
            "environment": self.api.environment,
            "database": {
                "type": ("SQLite (verified)" if self.database.url.startswith("sqlite:") else "PostgreSQL (verified)"),
                "url": (self.database.url.split("@")[-1] if "@" in self.database.url else self.database.url),
                "auto_migrate": self.database.auto_migrate,
            },
            "storage": {
                "backend": self.storage.backend.value,
                "path": (
                    self.storage.local_path
                    if self.storage.backend == StorageBackend.LOCAL
                    else f"Supabase:{self.storage.supabase_bucket}"
                ),
                "max_file_size_mb": self.storage.max_file_size_mb,
            },
            "agents": {
                "openai_configured": bool(self.openai.api_key),
                "environment": self.api.environment,
            },
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "log_level": self.api.log_level,
            },
        }

    model_config = {
        "env_prefix": "",
        "case_sensitive": False,
        "env_file": ".env",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> AppSettings:
    """
    Get the application settings.

    This function is cached to avoid loading the settings multiple times.

    Returns:
        AppSettings: The application settings
    """
    return AppSettings()
