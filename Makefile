# =======================================================
# Agent Template - Production-Ready Makefile
# Provides enterprise-grade task management for agent development
# =======================================================

.PHONY: help install dev-start dev-stop dev-status test lint format check clean setup docs docker-build docker-run docker-stop docker-compose-up docker-compose-down

# =======================================================
# 📖 HELP & INFORMATION
# =======================================================

# Default target
help: ## Show this help message
	@echo "Agent Template - Available Commands"
	@echo "=================================="
	@echo ""
	@echo "📚 SETUP & INSTALLATION:"
	@awk 'BEGIN {FS = ":.*##"; category=""} /^# .*SETUP/ { category = " Setup" } /^[a-zA-Z_-]+:.*##/ && category ~ /Setup/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "🚀 DEVELOPMENT:"
	@awk 'BEGIN {FS = ":.*##"; category=""} /^# .*DEVELOPMENT/ { category = " Development" } /^[a-zA-Z_-]+:.*##/ && category ~ /Development/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "🧪 TESTING & QA:"
	@awk 'BEGIN {FS = ":.*##"; category=""} /^# .*TESTING/ { category = " Testing" } /^[a-zA-Z_-]+:.*##/ && category ~ /Testing/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "🐳 DOCKER:"
	@awk 'BEGIN {FS = ":.*##"; category=""} /^# .*DOCKER/ { category = " Docker" } /^[a-zA-Z_-]+:.*##/ && category ~ /Docker/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "🚀 PRODUCTION:"
	@awk 'BEGIN {FS = ":.*##"; category=""} /^# .*PRODUCTION/ { category = " Production" } /^[a-zA-Z_-]+:.*##/ && category ~ /Production/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "🛠️ UTILITIES:"
	@awk 'BEGIN {FS = ":.*##"; category=""} /^# .*UTILITIES/ { category = " Utilities" } /^[a-zA-Z_-]+:.*##/ && category ~ /Utilities/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

info: ## Show environment information
	@echo "Agent Template Environment Information"
	@echo "====================================="
	@echo "Python: $$(python --version)"
	@echo "Poetry: $$(poetry --version)"
	@echo "Working Directory: $$(pwd)"
	@echo "Virtual Environment: $$(poetry env info --path)"
	@poetry run python -c "from src.agent_project.config.settings import get_settings; print(f'Database: {get_settings().database.url}')" 

# =======================================================
# 📚 SETUP & INSTALLATION
# =======================================================

setup: ## Setup development environment (.env file, dependencies)
	@echo "🔧 Setting up development environment..."
	poetry install
	poetry run python scripts/setup_env.py
	@echo "✅ Setup complete!"

install: ## Install dependencies
	@echo "📦 Installing dependencies..."
	poetry install

# =======================================================
# 🚀 DEVELOPMENT SERVICES
# =======================================================

dev-start: ## Start development services
	@echo "🚀 Starting development services..."
	poetry run python scripts/start_services.py --mode=development

dev-stop: ## Stop development services  
	@echo "🛑 Stopping development services..."
	poetry run python scripts/stop_services.py --mode=development

dev-status: ## Check development services status
	@echo "📊 Checking service status..."
	poetry run python scripts/service_status.py --mode=development

dev: setup dev-start ## Quick start: setup + start development
	@echo "🎉 Development environment ready!"

# =======================================================
# 🧪 TESTING & QUALITY ASSURANCE
# =======================================================

test: ## Run test suite
	@echo "🧪 Running tests..."
	poetry run pytest tests/ -v

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	poetry run pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	poetry run pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	poetry run pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

lint: ## Run linting (check only, no fixes)
	@echo "🔍 Running linting checks..."
	poetry run ruff check src/ apps/ scripts/ tests/

lint-fix: ## Run linting with auto-fixes
	@echo "🔧 Running linting with auto-fixes..."
	poetry run ruff check --fix src/ apps/ scripts/ tests/

typecheck: ## Run type checking
	@echo "🔍 Running type checks..."
	poetry run ruff check --select=F401,F821,F841 src/ apps/ scripts/ tests/

validate-domain: ## Validate domain layer purity (no framework dependencies)
	poetry run python scripts/validate_domain.py

validate-commit-msg: ## Validate commit message format (usage: make validate-commit-msg MSG="your message")
	@if [ -z "$(MSG)" ]; then \
		echo "❌ Error: No message provided. Usage: make validate-commit-msg MSG=\"feat(scope): description\""; \
		exit 1; \
	fi
	@if command -v commitlint >/dev/null 2>&1; then \
		echo "$(MSG)" | commitlint; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Commit message format is valid"; \
		else \
			echo "❌ Commit message format is invalid"; \
			exit 1; \
		fi; \
	else \
		echo "⚠️  commitlint not installed. Install with: npm install -g @commitlint/cli @commitlint/config-conventional"; \
		echo "📋 Checking basic format manually..."; \
		if echo "$(MSG)" | grep -qE "^(feat|fix|docs|style|refactor|test|chore|ci|build|perf|revert)(\(.+\))?: .+"; then \
			echo "✅ Basic format looks correct"; \
		else \
			echo "❌ Message should follow: type(scope): description"; \
			exit 1; \
		fi; \
	fi

format: ## Format code
	@echo "🎨 Formatting code..."
	poetry run ruff format src/ apps/ scripts/ tests/

check: ## Run all quality checks (lint + typecheck + test)
	@echo "✅ Running all quality checks..."
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) validate-domain
	$(MAKE) test

check-fix: ## Run quality checks with auto-fixes
	@echo "✅ Running quality checks with auto-fixes..."
	$(MAKE) format
	$(MAKE) lint-fix
	$(MAKE) typecheck
	$(MAKE) validate-domain
	$(MAKE) test-unit
	$(MAKE) test-integration

qa: check-fix ## Quality assurance: comprehensive checks with auto-fixes
	@echo "✅ Quality assurance complete!"

# =======================================================
# 🐳 DOCKER OPERATIONS
# =======================================================

docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t agent-template .

docker-run: ## Run Docker container (detached)
	@echo "🐳 Running Docker container..."
	docker run -d -p 8000:8000 --name agent-template-container agent-template

docker-run-interactive: ## Run Docker container (interactive)
	@echo "🐳 Running Docker container interactively..."
	docker run -it -p 8000:8000 --name agent-template-interactive agent-template

docker-stop: ## Stop Docker container
	@echo "🛑 Stopping Docker container..."
	docker stop agent-template-container || true
	docker stop agent-template-interactive || true

docker-clean: ## Remove Docker containers and images
	@echo "🧹 Cleaning Docker containers and images..."
	docker stop agent-template-container agent-template-interactive || true
	docker rm agent-template-container agent-template-interactive || true
	docker rmi agent-template || true

docker-logs: ## View Docker container logs
	@echo "📋 Viewing Docker logs..."
	docker logs -f agent-template-container

# Docker Compose Commands
docker-compose-up: ## Start services with Docker Compose
	@echo "🐳 Starting services with Docker Compose..."
	docker-compose up --build

docker-compose-up-d: ## Start services with Docker Compose (detached)
	@echo "🐳 Starting services with Docker Compose (background)..."
	docker-compose up -d --build

docker-compose-down: ## Stop Docker Compose services
	@echo "🛑 Stopping Docker Compose services..."
	docker-compose down

docker-compose-logs: ## View Docker Compose logs
	@echo "📋 Viewing Docker Compose logs..."
	docker-compose logs -f

# =======================================================
# 🚀 PRODUCTION DEPLOYMENT
# =======================================================

prod-start: ## Start production services
	@echo "🚀 Starting production services..."
	poetry run python scripts/start_services.py --mode=production

prod-stop: ## Stop production services
	@echo "🛑 Stopping production services..."
	poetry run python scripts/stop_services.py --mode=production

prod-docker: docker-build docker-run ## Build and run production Docker
	@echo "🚀 Production Docker deployment complete!"

# =======================================================
# 🛠️ UTILITIES & MAINTENANCE
# =======================================================

docs: ## Generate API documentation
	@echo "📚 Generating documentation..."
	poetry run python scripts/generate_postman_collection.py

clean: ## Clean up temporary files and caches
	@echo "🧹 Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "✅ Cleanup complete!"

clean-all: clean docker-clean ## Clean everything (files + Docker)
	@echo "🧹 Complete cleanup finished!" 