"""Tests for the environment setup script."""

import os

import pytest

from scripts.setup_env import ENV_VARS, setup_environment


@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path


def test_setup_environment_creates_env_file(test_data_dir):
    """Test that setup_environment creates a new .env file with all variables."""
    env_file = test_data_dir / ".env"

    # Change working directory to test directory
    original_cwd = os.getcwd()
    os.chdir(test_data_dir)

    try:
        # Run setup
        setup_environment()

        # Check that .env file was created
        assert env_file.exists()

        # Read contents and verify all variables are present
        env_contents = env_file.read_text()
        for key, value in ENV_VARS.items():
            assert f"{key}={value}" in env_contents

    finally:
        # Restore working directory
        os.chdir(original_cwd)


def test_setup_environment_preserves_existing_values(test_data_dir):
    """Test that setup_environment preserves existing values in .env file."""
    env_file = test_data_dir / ".env"

    # Create .env file with custom value
    custom_api_key = "custom_test_key_123"
    env_file.write_text(f"OPENAI_API_KEY={custom_api_key}\n")

    # Change working directory to test directory
    original_cwd = os.getcwd()
    os.chdir(test_data_dir)

    try:
        # Run setup
        setup_environment()

        # Read contents and verify custom value is preserved
        env_contents = env_file.read_text()
        assert f"OPENAI_API_KEY={custom_api_key}" in env_contents

        # Verify other variables were added
        for key, value in ENV_VARS.items():
            if key != "OPENAI_API_KEY":
                assert f"{key}={value}" in env_contents

    finally:
        # Restore working directory
        os.chdir(original_cwd)
