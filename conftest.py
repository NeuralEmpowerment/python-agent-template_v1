"""Configuration for pytest."""
import os
import pytest


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


@pytest.fixture(autouse=True)
def reset_caches():
    """Reset caches before each test to ensure clean state."""
    try:
        from src.agent_project.config.settings import reset_settings_cache
        from src.agent_project.infrastructure.database.sqlalchemy_config import reset_database_connections
        reset_settings_cache()
        reset_database_connections()
    except ImportError:
        # In case the import fails during early test runs
        pass 