---
title: Makefile Task Runner Guide
version: 1.0.0
created: 2025-06-27
updated: 2025-06-27
tags: [makefile, task-runner, development, build-automation]
---

# 🛠️ Makefile Task Runner Guide

> [!IMPORTANT]
> This project uses a comprehensive Makefile for task automation, providing enterprise compatibility and standardized development workflows. Makefiles work across all platforms and development environments.

## Table of Contents

- [🛠️ Makefile Task Runner Guide](#️-makefile-task-runner-guide)
  - [Table of Contents](#table-of-contents)
  - [🔍 What is the Makefile?](#-what-is-the-makefile)
  - [📋 Available Commands](#-available-commands)
    - [📚 Setup & Installation](#-setup--installation)
    - [🚀 Development Services](#-development-services)
    - [🧪 Testing & Quality Assurance](#-testing--quality-assurance)
    - [🐳 Docker Operations](#-docker-operations)
    - [🚀 Production Deployment](#-production-deployment)
    - [🛠️ Utilities & Maintenance](#️-utilities--maintenance)
  - [⚙️ Getting Started](#️-getting-started)
  - [🔄 Development Workflow](#-development-workflow)
  - [🧪 Quality Assurance](#-quality-assurance)
  - [🐳 Docker Development](#-docker-development)
  - [🚨 Troubleshooting](#-troubleshooting)

[↑ Back to Top](#table-of-contents)

## 🔍 What is the Makefile?

The Makefile is a build automation tool that provides a standardized interface for running development tasks. It replaces complex shell scripts and provides consistent commands across different environments.

**Benefits:**
- **Universal compatibility** - Works on all Unix-like systems (Linux, macOS, WSL)
- **Self-documenting** - Built-in help system with `make help`
- **Enterprise ready** - Standard tool in professional development environments
- **Simple syntax** - Easy to understand and modify
- **Dependency management** - Automatic dependency resolution between tasks

[↑ Back to Top](#table-of-contents)

## 📋 Available Commands

### 📚 Setup & Installation
[↑ Back to Top](#table-of-contents)

**Quick setup for new developers:**
```bash
make setup          # Complete development environment setup
make install        # Install dependencies only
make info          # Show environment information
```

### 🚀 Development Services
[↑ Back to Top](#table-of-contents)

**Start and manage development services:**
```bash
make dev           # Quick start: setup + start development
make dev-start     # Start development services
make dev-stop      # Stop development services  
make dev-status    # Check service status
```

### 🧪 Testing & Quality Assurance
[↑ Back to Top](#table-of-contents)

**Quality assurance and testing commands:**
```bash
# Quality assurance workflow
make qa            # Complete QA: format + lint + test
make check         # Check only: lint + test (no formatting)

# Individual QA commands
make format        # Format code with ruff
make lint          # Lint code with ruff
make test          # Run complete test suite
make test-unit     # Run unit tests only
make test-integration  # Run integration tests only
make test-coverage # Run tests with coverage report
```

### 🐳 Docker Operations
[↑ Back to Top](#table-of-contents)

**Docker development and deployment:**
```bash
# Docker development
make docker-build           # Build Docker image
make docker-run             # Run container (detached)
make docker-run-interactive  # Run container (interactive)
make docker-stop            # Stop containers
make docker-clean           # Clean containers and images
make docker-logs            # View container logs

# Docker Compose
make docker-compose-up      # Start with docker-compose
make docker-compose-up-d    # Start in background
make docker-compose-down    # Stop docker-compose services
make docker-compose-logs    # View compose logs
```

### 🚀 Production Deployment
[↑ Back to Top](#table-of-contents)

**Production deployment commands:**
```bash
make prod-start    # Start production services
make prod-stop     # Stop production services
make prod-docker   # Build and run production Docker
```

### 🛠️ Utilities & Maintenance
[↑ Back to Top](#table-of-contents)

**Maintenance and utility commands:**
```bash
make docs          # Generate API documentation
make clean         # Clean temporary files and caches
make clean-all     # Clean everything (files + Docker)
make help          # Show all available commands with descriptions
```

[↑ Back to Top](#table-of-contents)

## ⚙️ Getting Started

**For new developers starting on the project:**

1. **View available commands:**
   ```bash
   make help
   ```

2. **Complete setup:**
   ```bash
   make setup    # Sets up .env file, installs dependencies
   ```

3. **Start development:**
   ```bash
   make dev      # Combines setup + start development services
   ```

4. **Check environment:**
   ```bash
   make info     # Shows Python, Poetry, database info
   ```

[↑ Back to Top](#table-of-contents)

## 🔄 Development Workflow

**Daily development workflow using Make commands:**

```bash
# 1. Start development session
make dev-start

# 2. During development - run QA frequently
make qa           # Format, lint, and test

# 3. Before committing - ensure everything passes
make qa
git status        # Review changes
git add specific-file.py  # Stage selectively (NEVER use git add .)
git commit -m "feat(component): description"

# 4. End development session
make dev-stop
```

**Quality assurance workflow:**
```bash
# Quick quality check
make check        # Lint + test (no formatting)

# Full quality assurance  
make qa           # Format + lint + test

# Individual commands
make format       # Fix formatting issues
make lint         # Check code quality
make test         # Run test suite
```

[↑ Back to Top](#table-of-contents)

## 🧪 Quality Assurance

**Pre-commit quality assurance (REQUIRED):**

> [!IMPORTANT]
> **All commits must pass `make qa` before being committed**

```bash
# 1. Run complete quality assurance
make qa

# 2. Verify success (exit code 0)
echo $?

# 3. Only commit if QA passes
git add specific-files
git commit -m "message"
```

**QA command breakdown:**
- **`make format`** - Auto-format code with ruff
- **`make lint`** - Check code quality, type safety, imports
- **`make test`** - Run complete test suite
- **`make qa`** - All of the above in sequence

**Testing commands:**
```bash
make test                # All tests
make test-unit          # Unit tests only
make test-integration   # Integration tests only  
make test-coverage      # Tests with coverage report
```

[↑ Back to Top](#table-of-contents)

## 🐳 Docker Development

**Docker-based development workflow:**

```bash
# 1. Build the application image
make docker-build

# 2. Run for development (interactive)
make docker-run-interactive

# 3. Or run in background
make docker-run

# 4. View logs
make docker-logs

# 5. Stop when done
make docker-stop
```

**Docker Compose workflow:**
```bash
# Start all services
make docker-compose-up

# Or start in background
make docker-compose-up-d

# View logs
make docker-compose-logs

# Stop all services
make docker-compose-down
```

[↑ Back to Top](#table-of-contents)

## 🚨 Troubleshooting

**Common issues and solutions:**

**Issue: `make: command not found`**
```bash
# Solution: Install make
# macOS: xcode-select --install
# Ubuntu/Debian: sudo apt install build-essential
# Windows: Use WSL or install make for Windows
```

**Issue: Make command fails**
```bash
# Check what command is actually running
make -n qa          # Dry run - shows commands without executing

# View detailed output
make qa 2>&1 | tee output.log
```

**Issue: Poetry/Python not found**
```bash
# Ensure Poetry is installed and in PATH
poetry --version

# Check environment
make info
```

**Issue: Docker commands fail**
```bash
# Ensure Docker is running
docker --version
docker info

# Clean up if needed
make docker-clean
```

**Issue: Tests fail**
```bash
# Run specific test types
make test-unit              # Check unit tests
make test-integration       # Check integration tests

# View test output with verbose
poetry run pytest tests/ -v
```

**Issue: QA fails**
```bash
# Run individual QA steps
make format     # Fix formatting first
make lint       # Check for remaining issues
make test       # Ensure tests pass
```

> [!TIP]
> Always use `make help` to see the most up-to-date list of available commands and their descriptions.

**Makefile advantages over poethepoet:**
- **No additional dependencies** - Make is standard on Unix systems
- **Better error handling** - Clear exit codes and error messages
- **Enterprise compatibility** - Standard tool in professional environments
- **Easier CI/CD integration** - Works in all containerized environments
- **Self-documenting** - Built-in help system

[↑ Back to Top](#table-of-contents)

---

**Makefile Version:** 1.0.0  
**Last Updated:** 2025-06-27  
**Focus:** Development automation, quality assurance, enterprise compatibility 