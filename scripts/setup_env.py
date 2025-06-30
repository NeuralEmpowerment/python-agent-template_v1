"""Script to set up the environment variables for the agent template project."""

from pathlib import Path
from typing import Dict

# Default environment variables
ENV_VARS: Dict[str, str] = {
    "OPENAI_API_KEY": "your-api-key-here",
    "OBJC_DISABLE_INITIALIZE_FORK_SAFETY": "YES",
}


def setup_environment() -> None:
    """Set up the environment by creating or updating the .env file.

    This function will:
    1. Create a .env file if it doesn't exist
    2. Add any missing environment variables with default values
    3. Preserve any existing values in the .env file
    """
    env_path = Path(".env")

    # Read existing environment variables if .env exists
    existing_vars = {}
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    existing_vars[key.strip()] = value.strip()

    # Merge existing variables with defaults
    final_vars = ENV_VARS.copy()
    final_vars.update(existing_vars)

    # Write the .env file
    with open(env_path, "w") as f:
        for key, value in final_vars.items():
            f.write(f"{key}={value}\n")


if __name__ == "__main__":
    setup_environment()
