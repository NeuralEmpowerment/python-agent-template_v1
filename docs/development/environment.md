---
title: Poetry Environment Management Guide
version: 1.0.0
created: 2025-04-15
updated: 2025-04-15
tags: [poetry, python, virtual-environment, guide]
---

# 🐍 Poetry Environment Management

This document covers detailed information about how Poetry manages virtual environments and how to work with them effectively.

## 📑 Table of Contents

- [🐍 Poetry Environment Management](#-poetry-environment-management)
  - [📑 Table of Contents](#-table-of-contents)
  - [🔍 Understanding Poetry's Environment Management](#-understanding-poetrys-environment-management)
    - [How Poetry Creates Environments](#how-poetry-creates-environments)
  - [⚙️ Environment Configuration](#️-environment-configuration)
  - [🛠️ Working with Environments](#️-working-with-environments)
    - [Activating an Environment](#activating-an-environment)
    - [Viewing Environment Information](#viewing-environment-information)
    - [Running Commands in the Environment](#running-commands-in-the-environment)
    - [Deactivating an Environment](#deactivating-an-environment)
    - [Removing Environments](#removing-environments)
  - [📋 Best Practices](#-best-practices)
  - [❓ Gotchas \& Troubleshooting](#-gotchas--troubleshooting)

## 🔍 Understanding Poetry's Environment Management

Poetry creates isolated virtual environments for your projects by default. This ensures that dependencies for one project don't interfere with dependencies for another project or your system Python installation.

### How Poetry Creates Environments

When you run `poetry install` (or the `./scripts/setup.sh` script), Poetry:

1. Checks if you're already in an activated virtual environment
   - If yes, it uses that environment
   - If no, it creates a new environment or uses a previously created one specific to this project

2. By default, environments are created in a central cache directory:
   - Linux/macOS: `~/.cache/pypoetry/virtualenvs`
   - Windows: `%LOCALAPPDATA%\pypoetry\Cache\virtualenvs`

3. Each environment is named based on the project name and Python version (e.g., `poetry-poe-setup-py3.10`)

4. If configured with `virtualenvs.in-project true`, the environment is created as `.venv` inside your project directory

[↑ Back to Top](#-table-of-contents)

## ⚙️ Environment Configuration

You can customize how Poetry manages environments using the `poetry config` command. Use `--local` to apply settings only to the current project (stored in `poetry.toml`):

```bash
# Store virtual environments in the project directory (as .venv)
poetry config virtualenvs.in-project true --local

# Don't create a virtual environment automatically (use system Python or manually activated venv)
poetry config virtualenvs.create false --local

# Allow system packages to be visible in the virtual environment
poetry config virtualenvs.options.system-site-packages true --local
```

[↑ Back to Top](#-table-of-contents)

## 🛠️ Working with Environments

### Activating an Environment

This is the recommended way to work interactively

```bash
# Bash/Zsh
eval $(poetry env activate)

# Fish shell
eval (poetry env activate)

# PowerShell
Invoke-Expression (poetry env activate)
```

Once activated, your shell prompt will usually change, and commands like `python`, `pip`, and `make` will run from the virtual environment

### Viewing Environment Information

```bash
# Show basic environment info (Python version, path, etc.)
poetry env info

# Show just the path to the virtual environment directory
poetry env info --path

# Show the path to the Python executable within the environment
poetry env info --executable

# List all environments Poetry knows about for this project
poetry env list
```

### Running Commands in the Environment

* If Activated: Run commands directly (e.g., `make test`, `python demo.py`)
* If Not Activated: Use `poetry run`:
    ```bash
    make test
    poetry run python demo.py
    poetry run pytest
    ```

### Deactivating an Environment

If you activated the environment, simply run:

```bash
deactivate
```

### Removing Environments

Useful if an environment gets corrupted or you want to reset

```bash
# Remove the environment associated with the currently active Python version
poetry env remove python

# Remove an environment associated with a specific Python version
poetry env remove python3.9

# Remove an environment by its full name (from `poetry env list`)
poetry env remove poetry-poe-setup-abcdef-py3.9

# Remove ALL environments associated with the current project
poetry env remove --all
```
After removing, run `./scripts/setup.sh` again to recreate the environment

[↑ Back to Top](#-table-of-contents)

## 📋 Best Practices

1. **Use the Lock File**: Always commit `poetry.lock` to version control for reproducible builds
2. **Activate for Development**: For interactive development, activate the environment using `eval $(poetry env activate)`
3. **Use `poetry run` for Scripts/CI**: For automated scripts or CI/CD pipelines, `poetry run` is often more reliable than activation
4. **Consider `virtualenvs.in-project`**: Setting `poetry config virtualenvs.in-project true --local` creates `.venv` in your project, which can simplify discovery for IDEs and tools
5. **Regular Updates**: Run `poetry update` periodically to update dependencies according to `pyproject.toml` constraints
6. **Use Dev Groups**: Keep development-only tools (like `pytest`, `ruff`) in a dev group: `poetry add --group dev <package>`

[↑ Back to Top](#-table-of-contents)

## ❓ Gotchas & Troubleshooting

* **Activation Issues (`eval $(poetry env activate)` fails):**
  * Ensure Poetry created the environment (`poetry env list`). If not, run setup
  * Check your shell configuration. Sometimes shell hooks can interfere
  * Try activating manually: `source $(poetry env info --path)/bin/activate`
* **`python` Command Not Found (with pyenv):**
  * Make sure `pyenv` is initialized (`eval "$(pyenv init -)"`) and a version is active (`pyenv local 3.x.y` or `pyenv shell 3.x.y`)
  * The `setup.sh` tries to handle this, but manual setup might be needed if it fails
  * Tell Poetry which python to use: `poetry env use python3.x`
* **Environment Corruption:** If you get strange errors, the environment might be corrupted
  * Remove it: `poetry env remove --all`
  * Recreate it: `./scripts/setup.sh`
* **Permissions Issues:** On some systems, file permissions in the cache directory (`~/.cache/pypoetry`) can cause problems
  * Check permissions if installation fails unexpectedly
* **Multiple Projects Conflict:** If Poetry seems confused about which project an environment belongs to, ensure you are running commands from the correct project directory. If issues persist, removing the environment (`poetry env remove ...`) and rerunning setup often helps

[↑ Back to Top](#-table-of-contents) 