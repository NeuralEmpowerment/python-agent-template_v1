#!/bin/bash

# Poetry Environment Setup Script
# Created: 2023-04-12
# Updated: 2025-04-16
# Version: 1.1.0
#
# CHANGELOG:
# v1.0.0 (2023-04-12) - Initial version with Poetry setup and environment activation
# v1.1.0 (2025-04-16) - Added explicit activation warning and improved next steps section

# Exit on error
set -e

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print header
echo -e "${GREEN}========================================"
echo -e "Poetry Environment Setup"
echo -e "========================================${NC}"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}Error: Poetry is not installed. Please install it first.${NC}"
    echo -e "You can install Poetry by running:"
    echo -e "${YELLOW}curl -sSL https://install.python-poetry.org | python3 -${NC}"
    exit 1
fi

# Display Poetry version
POETRY_VERSION=$(poetry --version)
echo -e "${GREEN}Using ${POETRY_VERSION}${NC}"

# Check if we're in the right directory (should have pyproject.toml)
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: No pyproject.toml found in current directory.${NC}"
    echo -e "Please run this script from the directory containing pyproject.toml"
    exit 1
fi

# Check for pyenv and set Python version if needed
if command -v pyenv &> /dev/null; then
    echo -e "${YELLOW}Detected pyenv. Setting Python version...${NC}"
    # List available Python versions and use the first one
    PYTHON_VERSIONS=$(pyenv versions --bare | grep -E '^3\.' | head -n 1)
    if [ -n "$PYTHON_VERSIONS" ]; then
        echo -e "${GREEN}Using Python version: ${PYTHON_VERSIONS}${NC}"
        eval "$(pyenv init -)"
        pyenv shell $PYTHON_VERSIONS
    else
        echo -e "${RED}No Python 3.x version found in pyenv. Please install with: pyenv install 3.x.y${NC}"
        exit 1
    fi
fi

# Clean up existing virtual environment if there are issues
echo -e "${YELLOW}Checking for existing environment issues...${NC}"
poetry env list
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Found environment issues. Cleaning up...${NC}"
    poetry env remove --all 2>/dev/null || true
fi

# Install dependencies
echo -e "${YELLOW}Installing project dependencies...${NC}"
poetry install

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    touch .env
    echo -e "${GREEN}Created empty .env file.${NC}"
fi

# Get environment path
ENV_PATH=$(poetry env info --path)

# Display success message and next steps
echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo -e "\n${CYAN}${BOLD}NEXT STEPS:${NC}"
echo -e "${CYAN}------------------------------------------${NC}"
echo -e "${BOLD}1. Activate the environment:${NC}"
echo -e "   ${GREEN}eval \$(poetry env activate)${NC}"
echo -e "   ${YELLOW}⚠️ IMPORTANT: You MUST activate the environment before running any commands${NC}"
echo -e "   ${YELLOW}   without the 'poetry run' prefix. Otherwise, commands will fail.${NC}"
echo -e "   ${YELLOW}   To activate the environment, copy and paste the exact command above.${NC}"
echo -e "${BOLD}2. Run the complete application:${NC}"
echo -e "   ${GREEN}make dev-start${NC}   # If environment activated"
echo -e "   ${GREEN}make dev-start${NC}   # Alternative without activation"
echo -e "${BOLD}3. Or run individual components:${NC}"
echo -e "   ${GREEN}make dev-start${NC}      # Start development services"
echo -e "   ${GREEN}make test${NC}           # Run tests"
echo -e "${BOLD}4. When finished, deactivate:${NC}"
echo -e "   ${GREEN}deactivate${NC}"
echo -e "${CYAN}------------------------------------------${NC}"
echo -e "${YELLOW}See Makefile or run 'make help' for all available commands${NC}"

# Display environment info
echo -e "\n${YELLOW}Environment Info:${NC}"
echo -e "${GREEN}Path: ${ENV_PATH}${NC}"

# Display specific example commands
echo -e "\n${YELLOW}Example commands:${NC}"
echo -e "${GREEN}make dev-start${NC}   # Start development services"
echo -e "${GREEN}make docs${NC}        # Generate documentation"

# Display available tasks
echo -e "\n${YELLOW}Available Tasks:${NC}"
echo -e "${GREEN}Run the following to see available tasks:${NC}"
echo -e "${GREEN}make help${NC}" 