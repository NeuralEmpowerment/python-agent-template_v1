# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==${POETRY_VERSION}

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY README.md ./

# Install dependencies
RUN poetry install --only=main --no-root --no-interaction --no-ansi

# Copy application code
COPY src/ ./src/
COPY apps/ ./apps/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p logs data/uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint to run the FastAPI application
CMD ["python", "-m", "uvicorn", "apps.main:app", "--host", "0.0.0.0", "--port", "8000"] 