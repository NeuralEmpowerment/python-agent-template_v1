---
title: Agent Template - Clean Architecture for AI Agents
version: 1.0.0
created: 2025-01-07
updated: 2025-01-07
tags: [python, ai, agents, ddd, clean-architecture, template]
---

# 🤖 Agent Template

A production-ready template for building AI agent applications using Clean Architecture and Domain-Driven Design principles.

## 🚀 Features

- **Complete Agent Framework**: Create, manage, and interact with AI agents
- **Multiple Interfaces**: CLI tool, REST API, and Jupyter notebooks
- **Clean Architecture**: Domain-driven design with bounded contexts
- **LLM Integration**: OpenAI, Anthropic, and extensible provider system
- **Conversation Management**: Full conversation lifecycle with memory
- **Template System**: Easily copy bounded contexts for new services
- **Production Ready**: Comprehensive testing, logging, and deployment support

## 📖 Quick Setup

**👋 New to this project?** 

**📚 Complete Setup Guide**: See [SETUP.md](SETUP.md) for detailed environment setup, Jupyter kernel configuration, and troubleshooting.

**⚡ Quick Verification**: Run `poetry run python scripts/verify_setup.py` to check your setup.

## 🛠️ Prerequisites

- Python 3.11+
- Poetry for dependency management
- OpenAI API key (or other LLM provider)

## 📦 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agent-template
```

2. Install Poetry if you haven't already:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install dependencies:
```bash
poetry install
```

## 🔧 Configuration

1. Create a `.env` file in the project root:
```bash
# Required: LLM Provider Configuration
OPENAI_API_KEY=your_api_key_here

# Optional: Agent Configuration
AGENT_DEFAULT_MODEL=gpt-4
AGENT_DEFAULT_TEMPERATURE=0.7

# Optional: Database Configuration
DATABASE_URL=sqlite:///./data/agents.db
```

## 🗄️ Database Configuration

The application uses SQLite by default for conversation and agent persistence. The database is automatically initialized on first run.

### SQLite (Default)

SQLite provides local persistence and is automatically configured:

- **Database file**: `./data/agents.db`
- **Auto-initialization**: Tables created automatically on startup
- **No additional setup required**

### Configuration Options

You can customize the database configuration using environment variables:

```bash
# SQLite configuration (default)
DATABASE_URL=sqlite:///./data/agents.db
DATABASE_ECHO=false  # Set to true for SQL query logging

# Alternative backends
DATABASE_URL=memory://                    # In-memory (no persistence)
DATABASE_URL=postgresql://...             # PostgreSQL
```

## 🏃‍♂️ Running the Application

### CLI Interface
```bash
# Quick chat
poetry run python tools/agent_cli.py chat "Hello, how can you help me?"

# Interactive mode
poetry run python tools/agent_cli.py interactive
```

### REST API
```bash
# Start the FastAPI server
poetry run uvicorn apps.fastapi:app --reload

# Access API documentation
open http://localhost:8000/docs
```

### Jupyter Notebooks
```bash
# Start Jupyter Lab
poetry run jupyter lab

# Or open specific notebook
poetry run jupyter notebook notebooks/01_basic_agent_example.ipynb
```

## 🧪 Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=src

# Run specific test types
poetry run pytest tests/unit
poetry run pytest tests/integration
```

## 📝 Project Structure

```
.
├── src/
│   └── agent_project/          # Main bounded context
│       ├── domain/             # Domain models and business logic
│       ├── application/        # Use cases and application services
│       ├── infrastructure/     # External services and implementations
│       └── config/             # Configuration management
├── apps/
│   ├── fastapi.py             # REST API application
│   └── routes/                # API route definitions
├── tools/
│   └── agent_cli.py           # Command-line interface
├── notebooks/
│   └── 01_basic_agent_example.ipynb  # Getting started notebook
├── tests/
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── conftest.py           # Test configuration
├── scripts/                   # Utility scripts
├── data/                      # Data files and database
├── docs/                      # Documentation
├── pyproject.toml            # Project dependencies and configuration
└── README.md                 # This file
```

## 🎯 Core Concepts

### Agents
Create AI agents with specific roles and capabilities:

```python
from src.agent_project.application.services import AgentService

# Create an agent
agent = await agent_service.create_agent(
    name="Research Assistant",
    role="researcher", 
    system_prompt="You are a research assistant specialized in finding and analyzing information."
)
```

### Conversations
Manage conversation lifecycles:

```python
# Start a conversation
conversation = await agent_service.start_conversation(agent, title="Research Session")

# Send messages
response = await agent_service.send_message(conversation, agent, "What is quantum computing?")
```

### Bounded Contexts
The agent template is designed as a bounded context that can be easily copied and customized:

```bash
# Copy the bounded context for a new domain
scripts/copy_bounded_context.sh marketing_agent
```

## 📚 Documentation

- **[Setup Guide](SETUP.md)** - Detailed environment setup and troubleshooting
- **[Bounded Context Guide](docs/BOUNDED_CONTEXT_GUIDE.md)** - How to copy and customize bounded contexts
- **[Architecture Documentation](src/README.md)** - Technical architecture details
- **[Development Guide](DEVELOPMENT.md)** - Development workflows and practices

## 🔄 Quick Start Examples

### 1. CLI Quick Chat
```bash
poetry run python tools/agent_cli.py chat "Explain machine learning in simple terms"
```

### 2. API Usage
```python
import requests

# Create an agent
response = requests.post("http://localhost:8000/api/v1/agents", json={
    "name": "Helper",
    "role": "assistant",
    "system_prompt": "You are a helpful assistant."
})

agent_id = response.json()["id"]

# Start conversation and chat
conversation_response = requests.post(f"http://localhost:8000/api/v1/agents/{agent_id}/conversations")
conversation_id = conversation_response.json()["id"]

# Send message
chat_response = requests.post(f"http://localhost:8000/api/v1/conversations/{conversation_id}/messages", json={
    "content": "Hello!"
})
```

### 3. Jupyter Notebook
Open `notebooks/01_basic_agent_example.ipynb` for step-by-step examples.

## 🚀 Deployment

### Docker
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Manual Deployment
```bash
# Install dependencies
poetry install --only=main

# Start the API server
poetry run uvicorn apps.fastapi:app --host 0.0.0.0 --port 8000
```

## 🧪 Testing

The project includes comprehensive tests:

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows

```bash
# Run all tests with coverage
poetry run pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the [docs/](docs/) directory
- **Setup Issues**: See [SETUP.md](SETUP.md) troubleshooting section
- **Architecture Questions**: Review [src/README.md](src/README.md)
- **Examples**: Explore [notebooks/](notebooks/) directory

## 🎯 What's Next?

1. **Customize Your Agent**: Modify the system prompts and roles in the domain layer
2. **Add New Capabilities**: Extend the infrastructure layer with new LLM providers or tools
3. **Scale Your Architecture**: Use the bounded context copying to create specialized agent services
4. **Deploy to Production**: Use the provided Docker configuration for deployment

This template provides a solid foundation for building production-ready AI agent applications with clean architecture principles.