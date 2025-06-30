"""Configuration for pytest."""
import os
import pytest
from pathlib import Path

from src.agent_project.infrastructure.database.sqlalchemy_config import DatabaseConfig


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Save original environment
    original_env = dict(os.environ)
    
    # Set test environment variables
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    # Note: LOG_LEVEL not set globally to allow individual test control
    
    # Ensure OpenAI is not called during tests
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "test-key-placeholder"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_data_dir(tmp_path):
    """Provide isolated temporary directory for each test.
    
    This fixture creates a unique temporary directory for each test,
    ensuring complete isolation for file operations.
    
    Args:
        tmp_path: pytest's built-in temporary directory fixture
        
    Returns:
        Path: Temporary directory path for the test
    """
    return tmp_path


@pytest.fixture
def test_database_dir(tmp_path):
    """Provide isolated temporary directory for database-related tests.
    
    This fixture creates a temporary directory specifically for database
    file operations, separate from other file operations.
    
    Args:
        tmp_path: pytest's built-in temporary directory fixture
        
    Returns:
        Path: Temporary directory path for database files
    """
    db_dir = tmp_path / "database"
    db_dir.mkdir()
    return db_dir


@pytest.fixture
def test_database_config():
    """Provide test-specific database configuration.
    
    This fixture ensures all database tests use in-memory SQLite
    configuration, preventing file system issues in CI environments.
    
    Returns:
        DatabaseConfig: Configuration for in-memory testing database
    """
    return DatabaseConfig(database_url="sqlite:///:memory:")


@pytest.fixture
def test_database_reset():
    """Reset global database state between tests.
    
    This fixture ensures that global database engine and session factory
    are properly cleaned up between tests to prevent state pollution.
    """
    # Import here to avoid circular imports
    from src.agent_project.infrastructure.database import sqlalchemy_config
    
    # Store original state
    original_engine = getattr(sqlalchemy_config, '_engine', None)
    original_session_factory = getattr(sqlalchemy_config, '_session_factory', None)
    
    yield
    
    # Reset global state
    sqlalchemy_config._engine = None
    sqlalchemy_config._session_factory = None
    
    # Close any existing connections
    if original_engine:
        original_engine.dispose()


@pytest.fixture(autouse=True)
def test_environment_isolation():
    """Ensure clean environment for each test.
    
    This fixture automatically runs for every test to ensure:
    - Working directory is restored after test completion
    - Environment variables don't leak between tests
    - Global state is properly cleaned up
    """
    # Save original working directory
    original_cwd = os.getcwd()
    
    # Save original environment (additional to session-level fixture)
    original_env_vars = dict(os.environ)
    
    yield
    
    # Restore working directory
    os.chdir(original_cwd)
    
    # Restore any environment variables that might have been changed during test
    # (This supplements the session-level restoration)
    for key in list(os.environ.keys()):
        if key not in original_env_vars:
            del os.environ[key]
    
    for key, value in original_env_vars.items():
        if os.environ.get(key) != value:
            os.environ[key] = value 