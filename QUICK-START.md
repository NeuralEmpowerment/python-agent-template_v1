---
title: Quick Start Guide
version: 1.0.0
created: 2025-06-27
updated: 2025-06-27
tags: [quick-start, commands, agent-template]
---

# 🚀 Agent Template Quick Start

Get up and running with the Agent Template in minutes.

## 📑 Table of Contents

- [🚀 Agent Template Quick Start](#-agent-template-quick-start)
  - [📑 Table of Contents](#-table-of-contents)
  - [⚡ Quick Setup](#-quick-setup)
  - [🔄 Running the Application](#-running-the-application)
    - [Development Mode](#development-mode)
    - [Direct Commands](#direct-commands)
  - [🔧 Development Commands](#-development-commands)
  - [🐳 Docker Commands](#-docker-commands)
    - [Development with Docker](#development-with-docker)
    - [Production Docker](#production-docker)
  - [🧪 Testing](#-testing)
  - [💡 Essential URLs](#-essential-urls)
  - [🛠️ Troubleshooting](#️-troubleshooting)
    - [Common Issues](#common-issues)
    - [Getting Help](#getting-help)

## ⚡ Quick Setup

```bash
# 1. Install dependencies
poetry install

# 2. Set up environment
cp env.example .env
# Edit .env with your OpenAI API key

# 3. Start the application
make dev-start
```

## 🔄 Running the Application

### Development Mode

```bash
# Start services
make dev-start

# Check status
make dev-status

# Stop services
make dev-stop
```

### Direct Commands

```bash
# Start with Python directly
poetry run python scripts/start_services.py --mode=development

# Stop services
poetry run python scripts/stop_services.py
```

## 🔧 Development Commands

| Command | Description |
|---------|-------------|
| `make dev` | Setup + start (one command to rule them all) |
| `make dev-start` | Start development services |
| `make dev-stop` | Stop development services |
| `make dev-status` | Check service status |
| `make test` | Run all tests |
| `make qa` | Run quality checks (format, lint, test) |

## 🐳 Docker Commands

### Development with Docker

```bash
# Build and run with docker-compose
docker-compose up --build

# Run in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f
```

### Production Docker

```bash
# Build production image
make docker-build

# Run production container
make docker-run

# Or with docker directly
docker build -t agent-template .
docker run -p 8000:8000 agent-template
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run only unit tests
poetry run python -m pytest tests/unit/

# Run with coverage
poetry run python -m pytest tests/ --cov=src/
```

## 💡 Essential URLs

Once running, access these URLs:

- **API Health**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Configuration Status**: http://localhost:8000/config/status

## 🛠️ Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check what's running on port 8000
lsof -i :8000

# Force stop and restart
make dev-stop
make dev-start
```

**OpenAI API issues:**
```bash
# Check configuration
curl http://localhost:8000/config/status
```

**Permission issues:**
```bash
# Make sure data directory is writable
mkdir -p data/uploads
chmod 755 data/
```

### Getting Help

- **Full Documentation**: See `DEVELOPMENT.md`
- **All Make Commands**: Run `make help`
- **Service Status**: Use `make dev-status`

---

**🎯 That's it!** You now have a working agent template. Start building your AI agents! 🤖 