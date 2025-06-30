"""Tests for the constants module."""


from src.agent_project.config.constants import (
    DEFAULT_API_DESCRIPTION,
    DEFAULT_API_TITLE,
    DEFAULT_API_VERSION,
    DEFAULT_HOST,
    DEFAULT_LOG_LEVEL,
    DEFAULT_PORT,
    ENV_DEVELOPMENT,
    ENV_PRODUCTION,
    ENV_TESTING,
)


class TestApplicationConstants:
    """Test cases for application-related constants."""

    def test_default_api_title(self):
        """Test DEFAULT_API_TITLE constant."""
        assert DEFAULT_API_TITLE == "Agent Template API"
        assert isinstance(DEFAULT_API_TITLE, str)
        assert len(DEFAULT_API_TITLE) > 0

    def test_default_api_description(self):
        """Test DEFAULT_API_DESCRIPTION constant."""
        assert DEFAULT_API_DESCRIPTION == "RESTful API for AI agent creation, management, and interaction"
        assert isinstance(DEFAULT_API_DESCRIPTION, str)
        assert len(DEFAULT_API_DESCRIPTION) > 0

    def test_default_api_version(self):
        """Test DEFAULT_API_VERSION constant."""
        assert DEFAULT_API_VERSION == "0.1.0"
        assert isinstance(DEFAULT_API_VERSION, str)
        # Check semantic versioning format
        version_parts = DEFAULT_API_VERSION.split(".")
        assert len(version_parts) == 3
        for part in version_parts:
            assert part.isdigit()


class TestEnvironmentConstants:
    """Test cases for environment-related constants."""

    def test_environment_development(self):
        """Test ENV_DEVELOPMENT constant."""
        assert ENV_DEVELOPMENT == "development"
        assert isinstance(ENV_DEVELOPMENT, str)

    def test_environment_production(self):
        """Test ENV_PRODUCTION constant."""
        assert ENV_PRODUCTION == "production"
        assert isinstance(ENV_PRODUCTION, str)

    def test_environment_testing(self):
        """Test ENV_TESTING constant."""
        assert ENV_TESTING == "testing"
        assert isinstance(ENV_TESTING, str)

    def test_environment_constants_uniqueness(self):
        """Test that all environment constants are unique."""
        environments = [ENV_DEVELOPMENT, ENV_PRODUCTION, ENV_TESTING]
        assert len(environments) == len(set(environments))

    def test_environment_constants_lowercase(self):
        """Test that environment constants are lowercase."""
        assert ENV_DEVELOPMENT.islower()
        assert ENV_PRODUCTION.islower()
        assert ENV_TESTING.islower()


# ZenML constants tests removed - not needed for agent template


class TestServerConstants:
    """Test cases for server-related constants."""

    def test_default_host(self):
        """Test DEFAULT_HOST constant."""
        assert DEFAULT_HOST == "0.0.0.0"
        assert isinstance(DEFAULT_HOST, str)
        # Basic IPv4 format check
        host_parts = DEFAULT_HOST.split(".")
        assert len(host_parts) == 4
        for part in host_parts:
            assert part.isdigit()
            assert 0 <= int(part) <= 255

    def test_default_port(self):
        """Test DEFAULT_PORT constant."""
        assert DEFAULT_PORT == 8000
        assert isinstance(DEFAULT_PORT, int)
        assert 1 <= DEFAULT_PORT <= 65535

    def test_default_log_level(self):
        """Test DEFAULT_LOG_LEVEL constant."""
        assert DEFAULT_LOG_LEVEL == "INFO"
        assert isinstance(DEFAULT_LOG_LEVEL, str)
        # Check it's a valid log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert DEFAULT_LOG_LEVEL in valid_log_levels


class TestConstantsIntegration:
    """Test cases for constants integration and consistency."""

    def test_all_constants_defined(self):
        """Test that all expected constants are defined and importable."""
        # This test ensures all constants can be imported without errors
        constants_to_check = [
            DEFAULT_API_TITLE,
            DEFAULT_API_DESCRIPTION,
            DEFAULT_API_VERSION,
            ENV_DEVELOPMENT,
            ENV_PRODUCTION,
            ENV_TESTING,
            DEFAULT_HOST,
            DEFAULT_PORT,
            DEFAULT_LOG_LEVEL,
        ]

        # Verify all constants are not None
        for constant in constants_to_check:
            assert constant is not None

    def test_string_constants_not_empty(self):
        """Test that string constants are not empty."""
        string_constants = [
            DEFAULT_API_TITLE,
            DEFAULT_API_DESCRIPTION,
            DEFAULT_API_VERSION,
            ENV_DEVELOPMENT,
            ENV_PRODUCTION,
            ENV_TESTING,
            DEFAULT_HOST,
            DEFAULT_LOG_LEVEL,
        ]

        for constant in string_constants:
            assert isinstance(constant, str)
            assert len(constant.strip()) > 0

    def test_port_constants_consistency(self):
        """Test that port-related constants are consistent."""
        # Port constant should be valid port number
        port_int = DEFAULT_PORT

        assert isinstance(port_int, int)

        # Should be in valid port range
        assert 1 <= port_int <= 65535

    def test_environment_constants_completeness(self):
        """Test that environment constants cover all typical environments."""
        environments = [ENV_DEVELOPMENT, ENV_PRODUCTION, ENV_TESTING]

        # Check we have the three main environments
        assert "development" in environments
        assert "production" in environments
        assert "testing" in environments

        # Verify consistency in naming (all lowercase)
        for env in environments:
            assert env.islower()
            assert " " not in env  # No spaces
            assert env.isalpha()  # Only letters
