# 🚀 Agent Template Setup Guide

This guide will help you set up the agent template project with the proper Python environment, Jupyter kernels, and dependencies.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.11 or 3.12 (3.11 recommended)
- **Poetry**: For dependency management
- **Git**: For version control
- **VS Code**: Recommended IDE with Jupyter extension

### Do You Need a Virtual Machine?
**Short answer: No, you don't need a VM!** ✅

This project runs perfectly on:
- ✅ **macOS** (your current setup)
- ✅ **Linux** (Ubuntu, Debian, etc.)
- ✅ **Windows** (with WSL2 recommended)
- ✅ **Docker** (optional containerization)

## 🛠️ Quick Setup

### Step 1: Clone and Navigate
```bash
# If you haven't already
git clone <your-repo-url>
cd agent-template
```

### Step 2: Install Poetry (if not installed)
```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Or via Homebrew (macOS)
brew install poetry

# Or via pip
pip install poetry
```

### Step 3: Set Up Python Environment
```bash
# Install dependencies and create virtual environment
poetry install

# Activate the virtual environment
poetry shell
```

### Step 4: Set Environment Variables
```bash
# Copy example environment file
cp env.example .env

# Edit .env file and add your API keys
# Required:
export OPENAI_API_KEY=your_openai_api_key_here

# Optional (for other LLM providers):
export ANTHROPIC_API_KEY=your_anthropic_key_here
```

### Step 5: Verify Installation
```bash
# Run tests to verify everything works
poetry run pytest tests/unit/ -v

# Try the CLI tool
poetry run python tools/agent_cli.py chat "Hello!"

# Start the API server
poetry run python apps/main.py
```

## 📓 Jupyter Notebook Setup

### Setting Up the Correct Kernel

When you see the "Select Another Kernel" dialog in VS Code:

1. **Choose "Python Environments..."**
2. **Select the Poetry Virtual Environment**:
   ```
   ~/.cache/pypoetry/virtualenvs/agent-template-<hash>/bin/python
   ```
   Or look for: `agent-template (Python 3.11.x)`

### Manual Kernel Setup

If the kernel doesn't appear automatically:

```bash
# Activate poetry environment
poetry shell

# Install IPython kernel
poetry add ipykernel --group dev

# Install the kernel for Jupyter
python -m ipykernel install --user --name agent-template --display-name "Agent Template (Python 3.11)"
```

### Verify Kernel Installation
```bash
# List available kernels
jupyter kernelspec list

# You should see:
#   agent-template    /Users/your-username/.local/share/jupyter/kernels/agent-template
```

### VS Code Jupyter Setup

1. **Install Extensions**:
   - Python extension (ms-python.python)
   - Jupyter extension (ms-toolsai.jupyter)

2. **Select Interpreter**:
   - `Cmd+Shift+P` → "Python: Select Interpreter"
   - Choose the Poetry virtual environment

3. **Open Notebook**:
   - Open `notebooks/01_basic_agent_example.ipynb`
   - Click "Select Kernel" in top-right
   - Choose "Agent Template (Python 3.11)"

## 🔧 Troubleshooting

### Common Issues

#### 1. "OpenAI API Key Not Found"
```bash
# Make sure you've set the environment variable
echo $OPENAI_API_KEY

# If empty, add to your shell profile:
echo 'export OPENAI_API_KEY=your_key_here' >> ~/.zshrc
source ~/.zshrc
```

#### 2. "Poetry Command Not Found"
```bash
# Add Poetry to PATH (macOS/Linux)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Or use the full path
~/.local/bin/poetry install
```

#### 3. "Wrong Python Version"
```bash
# Check Python version
python --version

# Install Python 3.11 via pyenv (recommended)
curl https://pyenv.run | bash
pyenv install 3.11.8
pyenv local 3.11.8

# Then reinstall poetry environment
poetry env remove python
poetry install
```

#### 4. "Kernel Not Found in VS Code"
```bash
# Restart VS Code completely
# Then try kernel setup again

# Or manually select interpreter:
# Cmd+Shift+P → "Python: Select Interpreter"
# Choose: ~/.cache/pypoetry/virtualenvs/agent-template-*/bin/python
```

#### 5. "Import Errors in Notebook"
```bash
# Make sure you're using the right kernel
# The kernel should show "Agent Template (Python 3.11)" in top-right

# If still issues, restart kernel:
# Kernel → Restart Kernel
```

## 🚀 Alternative Setup Methods

### Method 1: Docker (Isolated Environment)

```bash
# Build Docker image
docker build -t agent-template .

# Run with environment variables
docker run -e OPENAI_API_KEY=your_key_here -p 8000:8000 agent-template
```

### Method 2: Conda (Alternative to Poetry)

```bash
# Create conda environment
conda create -n agent-template python=3.11
conda activate agent-template

# Install dependencies
pip install -r requirements.txt  # You'd need to generate this from poetry

# Install Jupyter kernel
python -m ipykernel install --user --name agent-template
```

### Method 3: System Python (Not Recommended)

```bash
# Only if you must use system Python
pip install -r requirements.txt
python -m ipykernel install --user --name agent-template
```

## 🧪 Verification Checklist

After setup, verify everything works:

- [ ] **Poetry Environment**: `poetry run python --version` shows Python 3.11+
- [ ] **Dependencies**: `poetry run python -c "import openai; print('✅ OpenAI imported')"`
- [ ] **Environment Variables**: `echo $OPENAI_API_KEY` shows your key
- [ ] **Tests Pass**: `poetry run pytest tests/unit/ -q` shows all green
- [ ] **CLI Works**: `poetry run python tools/agent_cli.py chat "test"`
- [ ] **Jupyter Kernel**: Notebook shows "Agent Template" kernel
- [ ] **Imports Work**: Can import `from src.agent_project.domain.entities import Agent`

## 🎯 Quick Start Commands

Once setup is complete:

```bash
# Activate environment
poetry shell

# Interactive chat
python tools/agent_cli.py interactive

# Quick API test
python tools/agent_cli.py chat "What can you help me with?"

# Start web server
python apps/main.py

# Run example notebook
jupyter lab notebooks/01_basic_agent_example.ipynb

# Run all tests
pytest tests/unit/ -v
```

## 📚 Next Steps

1. **Explore the Example Notebook**: `notebooks/01_basic_agent_example.ipynb`
2. **Try the CLI Tool**: `python tools/agent_cli.py interactive`
3. **Start the API**: `python apps/main.py` then visit http://localhost:8000/docs
4. **Create New Bounded Context**: `./scripts/copy_bounded_context.sh agent_project my_new_service`
5. **Read the Architecture Guide**: `docs/BOUNDED_CONTEXT_GUIDE.md`

## 🆘 Getting Help

### Documentation
- **Architecture**: `src/README.md`
- **Bounded Context Guide**: `docs/BOUNDED_CONTEXT_GUIDE.md`
- **Project Plan**: `PROJECT-PLAN_20250107_Agent-Template-Restructuring.md`

### Common Commands Reference
```bash
# Development
poetry install          # Install dependencies
poetry shell            # Activate environment
poetry add package-name # Add new dependency

# Testing
pytest tests/unit/      # Run unit tests
make check              # Run linting and type checks

# Agent Operations
python tools/agent_cli.py interactive    # Interactive chat
python apps/main.py                      # Start API server
jupyter lab notebooks/                   # Start Jupyter

# Bounded Context Management
./scripts/copy_bounded_context.sh source target  # Copy bounded context
```

---

🎉 **You're all set!** Your agent template is ready for development. The environment is isolated, dependencies are managed, and you have multiple ways to interact with your agents (CLI, API, notebooks).

**No VM needed** - this runs beautifully on your local machine! 🚀 