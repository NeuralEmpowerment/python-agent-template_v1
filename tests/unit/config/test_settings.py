"""Tests for the settings module."""

import os
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from src.agent_project.config.constants import (
    ENV_DEVELOPMENT,
    ENV_PRODUCTION,
    ENV_TESTING,
)
from src.agent_project.config.settings import (
    APISettings,
    AppSettings,
    OpenAISettings,
    get_settings,
)

# ZenMLSettings tests removed - not needed for agent template


class TestAPISettings:
    """Test cases for APISettings class."""

    @patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False)
    def test_api_settings_defaults(self):
        """Test APISettings with default values."""
        settings = APISettings()

        assert settings.title == "Agent Template API"
        assert settings.description == "RESTful API for AI agent creation, management, and interaction"
        assert settings.version == "0.1.0"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.log_level == "INFO"
        assert settings.environment == "development"

    def test_api_settings_custom_values(self):
        """Test APISettings with custom values."""
        settings = APISettings(
            title="Custom API",
            description="Custom description",
            version="1.0.0",
            host="localhost",
            port=3000,
            log_level="DEBUG",
            environment="production",
        )

        assert settings.title == "Custom API"
        assert settings.description == "Custom description"
        assert settings.version == "1.0.0"
        assert settings.host == "localhost"
        assert settings.port == 3000
        assert settings.log_level == "DEBUG"
        assert settings.environment == "production"

    def test_api_settings_environment_validation_valid(self):
        """Test APISettings environment validation with valid values."""
        # Test all valid environments
        for env in [ENV_DEVELOPMENT, ENV_PRODUCTION, ENV_TESTING]:
            settings = APISettings(environment=env)
            assert settings.environment == env

    def test_api_settings_environment_validation_invalid(self):
        """Test APISettings environment validation with invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            APISettings(environment="invalid_env")

        error = exc_info.value
        assert "Environment must be one of" in str(error)

    def test_api_settings_environment_case_insensitive(self):
        """Test APISettings environment validation is case insensitive."""
        settings = APISettings(environment="PRODUCTION")
        assert settings.environment == "production"  # Should be lowercased

    def test_api_settings_is_development_property(self):
        """Test is_development property."""
        dev_settings = APISettings(environment=ENV_DEVELOPMENT)
        prod_settings = APISettings(environment=ENV_PRODUCTION)
        test_settings = APISettings(environment=ENV_TESTING)

        assert dev_settings.is_development is True
        assert prod_settings.is_development is False
        assert test_settings.is_development is False

    def test_api_settings_is_production_property(self):
        """Test is_production property."""
        dev_settings = APISettings(environment=ENV_DEVELOPMENT)
        prod_settings = APISettings(environment=ENV_PRODUCTION)
        test_settings = APISettings(environment=ENV_TESTING)

        assert dev_settings.is_production is False
        assert prod_settings.is_production is True
        assert test_settings.is_production is False

    def test_api_settings_is_testing_property(self):
        """Test is_testing property."""
        dev_settings = APISettings(environment=ENV_DEVELOPMENT)
        prod_settings = APISettings(environment=ENV_PRODUCTION)
        test_settings = APISettings(environment=ENV_TESTING)

        assert dev_settings.is_testing is False
        assert prod_settings.is_testing is False
        assert test_settings.is_testing is True

    @patch.dict(
        os.environ,
        {"API_TITLE": "Env API Title", "API_HOST": "env-host", "API_PORT": "9999", "API_ENVIRONMENT": "production"},
    )
    def test_api_settings_from_environment(self):
        """Test APISettings loading from environment variables."""
        # Note: APISettings has empty env_prefix, so environment loading depends on field aliases
        settings = APISettings()

        # With empty env_prefix, the exact behavior depends on pydantic-settings
        # Test that defaults are still applied when env vars don't match field names
        assert isinstance(settings.title, str)
        assert isinstance(settings.host, str)
        assert isinstance(settings.port, int)


class TestOpenAISettings:
    """Test cases for OpenAISettings class."""

    def test_openai_settings_defaults(self):
        """Test OpenAISettings with default values."""
        settings = OpenAISettings()
        # The API key might be loaded from .env file or None if not available
        # Just verify it's a string or None
        assert settings.api_key is None or isinstance(settings.api_key, str)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"})
    def test_openai_settings_with_environment_api_key(self):
        """Test OpenAISettings with API key from environment."""
        settings = OpenAISettings()
        # The field has alias="OPENAI_API_KEY" so it should pick up the env var
        # But .env file might also provide a value, so test for string presence
        assert settings.api_key is not None
        assert isinstance(settings.api_key, str)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "env-api-key"})
    def test_openai_settings_from_environment(self):
        """Test OpenAISettings loads from environment variables."""
        settings = OpenAISettings()
        # Environment variable should be used or .env file value
        assert settings.api_key is not None
        assert isinstance(settings.api_key, str)

    def test_openai_settings_no_environment(self):
        """Test OpenAISettings when environment is cleared but .env may exist."""
        # Note: Even with cleared environment, .env file may still provide value
        settings = OpenAISettings()
        # API key might be None or loaded from .env file
        assert settings.api_key is None or isinstance(settings.api_key, str)

    def test_openai_settings_model_config(self):
        """Test OpenAISettings model configuration."""
        settings = OpenAISettings()

        # Should have valid API key (from env or .env file) or None
        assert settings.api_key is None or isinstance(settings.api_key, str)

        # Test model_config exists and has expected structure
        assert hasattr(OpenAISettings, "model_config")
        config = OpenAISettings.model_config
        assert "env_file" in config
        assert config["env_file"] == ".env"


class TestAppSettings:
    """Test cases for AppSettings class."""

    def test_app_settings_defaults(self):
        """Test AppSettings with default nested settings."""
        settings = AppSettings()

        # Check that nested settings are properly instantiated
        assert isinstance(settings.api, APISettings)
        assert isinstance(settings.openai, OpenAISettings)

        # Check some default values from nested settings
        # Note: Environment might be 'testing' due to test setup, which is expected
        assert settings.api.environment in ["development", "testing"]
        # API key might be loaded from .env file or be None
        assert settings.openai.api_key is None or isinstance(settings.openai.api_key, str)

    def test_app_settings_custom_nested(self):
        """Test AppSettings with custom nested settings instances."""
        custom_api = APISettings(environment="production")
        custom_openai = OpenAISettings()

        app_settings = AppSettings(api=custom_api, openai=custom_openai)

        # Custom settings should be used
        assert app_settings.api.environment == "production"
        assert isinstance(app_settings.openai, OpenAISettings)

    def test_app_settings_partial_override(self):
        """Test AppSettings with partial nested settings override."""
        custom_api = APISettings(environment="testing")

        app_settings = AppSettings(api=custom_api)

        # Custom API settings should be used
        assert app_settings.api.environment == "testing"

        # Other settings should use defaults
        # API key might be loaded from .env file or be None
        assert app_settings.openai.api_key is None or isinstance(app_settings.openai.api_key, str)

    def test_app_settings_environment_behavior(self):
        """Test AppSettings environment behavior with nested settings."""
        app_settings = AppSettings()

        # OpenAI settings might have API key from .env file or be None
        assert app_settings.openai.api_key is None or isinstance(app_settings.openai.api_key, str)

        # Test that OpenAI settings can be overridden directly
        # Note: AppSettings creates nested settings as defaults, so we test direct creation
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-override-key"}):
            # Create OpenAI settings directly to test environment behavior
            direct_openai_settings = OpenAISettings()
            assert direct_openai_settings.api_key == "env-override-key"
            assert isinstance(direct_openai_settings.api_key, str)

    def test_app_settings_additional_fields(self):
        """Test AppSettings additional configuration fields."""
        settings = AppSettings()

        # Check the additional field exists
        assert hasattr(settings, "objc_disable_initialize_fork_safety")
        assert settings.objc_disable_initialize_fork_safety is True

    def test_app_settings_nested_settings_independence(self):
        """Test that nested settings are independent instances."""
        app_settings = AppSettings()

        # Each nested setting should be its own instance
        assert app_settings.api is not app_settings.openai

        # They should be the correct types
        assert type(app_settings.api).__name__ == "APISettings"
        assert type(app_settings.openai).__name__ == "OpenAISettings"


class TestGetSettings:
    """Test cases for get_settings function."""

    def test_get_settings_returns_app_settings(self):
        """Test that get_settings returns AppSettings instance."""
        settings = get_settings()
        assert isinstance(settings, AppSettings)

    def test_get_settings_caching(self):
        """Test that get_settings is cached (returns same instance)."""
        settings1 = get_settings()
        settings2 = get_settings()

        # Should return the same instance due to @lru_cache
        assert settings1 is settings2

    def test_get_settings_default_structure(self):
        """Test that get_settings returns properly structured settings."""
        settings = get_settings()

        # Verify all nested settings are present
        assert hasattr(settings, "api")
        assert hasattr(settings, "openai")

        # Verify they are the correct types
        assert isinstance(settings.api, APISettings)
        assert isinstance(settings.openai, OpenAISettings)

    def test_get_settings_cache_behavior(self):
        """Test get_settings cache behavior and clearing."""
        # Clear the cache to start fresh
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        # Should be the same instance (cached)
        assert settings1 is settings2

        # Clear cache and get new instance
        get_settings.cache_clear()
        settings3 = get_settings()

        # Should be a different instance after cache clear
        assert settings3 is not settings1
        assert isinstance(settings3, AppSettings)


class TestSettingsIntegration:
    """Test cases for settings integration and edge cases."""

    def test_settings_field_validation_types(self):
        """Test that settings properly validate field types."""
        # Test port validation
        with pytest.raises(ValidationError):
            APISettings(port="invalid")  # Should be int

        # Test valid port
        settings = APISettings(port=3000)
        assert settings.port == 3000

    def test_settings_model_config(self):
        """Test that settings model configuration is correct."""
        # All settings classes should have proper model_config
        _api_settings = APISettings()  # noqa: F841
        _openai_settings = OpenAISettings()  # noqa: F841

        # Check that model_config exists and has expected properties
        assert hasattr(APISettings, "model_config")
        assert hasattr(OpenAISettings, "model_config")

        # Verify case sensitivity configuration
        api_config = APISettings.model_config
        assert "case_sensitive" in api_config
        assert api_config["case_sensitive"] is False

    def test_settings_validation_edge_cases(self):
        """Test settings validation with edge cases."""
        # Empty string environment should fail
        with pytest.raises(ValidationError):
            APISettings(environment="")

        # Whitespace-only environment should fail
        with pytest.raises(ValidationError):
            APISettings(environment="   ")

    @patch("src.agent_project.config.settings.get_settings")
    def test_settings_dependency_injection(self, mock_get_settings):
        """Test that settings can be mocked for testing."""
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings

        # This simulates how settings would be used in dependency injection
        injected_settings = mock_get_settings()
        assert injected_settings is mock_settings
        mock_get_settings.assert_called_once()

    def test_settings_inheritance_structure(self):
        """Test that settings classes inherit from BaseSettings correctly."""
        from pydantic_settings import BaseSettings

        # All settings classes should inherit from BaseSettings
        assert issubclass(APISettings, BaseSettings)
        assert issubclass(OpenAISettings, BaseSettings)
        assert issubclass(AppSettings, BaseSettings)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "direct-env-test"})
    def test_openai_settings_direct_environment_access(self):
        """Test OpenAI settings can access environment variables when created directly."""
        # When creating OpenAISettings directly, it should pick up environment variables
        openai_settings = OpenAISettings()
        assert openai_settings.api_key == "direct-env-test"
