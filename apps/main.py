"""Main entry point for the Agent Template application."""

from datetime import datetime
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# Import application modules
from apps.routes.agent_routes import router as agent_router
from apps.routes.examples import router as examples_router
from apps.routes.pipeline_routes import router as pipeline_router
from src.agent_project.config import (
    get_settings,
    log_component_status,
    log_startup_info,
    print_startup_banner,
)
from src.agent_project.infrastructure.logging import get_context_logger, setup_logging
from src.agent_project.infrastructure.middleware import (
    RequestIDMiddleware,
    RequestLoggerMiddleware,
)

# Get application settings
settings = get_settings()

# Create FastAPI app with enhanced documentation
app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check endpoints to verify the API is running correctly",
        },
        {
            "name": "config",
            "description": "Configuration and system status endpoints",
        },
        {
            "name": "agents",
            "description": "Endpoints for AI agent creation, management, and interaction",
        },
    ],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root route redirecting to docs
@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect root route to API documentation."""
    return RedirectResponse(url="/docs")


# Health check endpoint
@app.get(
    "/health",
    tags=["health"],
    summary="Application health check",
    response_description="Health status of the API",
)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint to verify the API is running."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Configuration status endpoint
@app.get(
    "/config/status",
    tags=["config"],
    summary="Configuration status check",
    response_description="Configuration validation and component status",
)
async def config_status() -> Dict[str, Any]:
    """Configuration status endpoint to check system configuration and component health."""
    try:
        # Validate configuration
        settings.validate_configuration()

        # Get startup info
        info = settings.get_startup_info()

        # Check component health
        component_status: Dict[str, Any] = {}

        # Storage component
        if settings.storage.backend.value == "local":
            from pathlib import Path

            try:
                Path(settings.storage.local_path).mkdir(parents=True, exist_ok=True)
                component_status["storage"] = {
                    "status": "healthy",
                    "backend": "local",
                    "path": settings.storage.local_path,
                }
            except Exception as e:
                component_status["storage"] = {
                    "status": "unhealthy",
                    "backend": "local",
                    "error": str(e),
                }
        else:
            component_status["storage"] = {
                "status": "configured",
                "backend": "supabase",
                "bucket": settings.storage.supabase_bucket,
            }

        # Database component
        if settings.database.url.startswith("sqlite:"):
            from pathlib import Path

            try:
                db_path = settings.database.url.replace("sqlite:///", "")
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                component_status["database"] = {
                    "status": "healthy",
                    "type": "sqlite",
                    "path": db_path,
                    "auto_migrate": settings.database.auto_migrate,
                }
            except Exception as e:
                component_status["database"] = {
                    "status": "unhealthy",
                    "type": "sqlite",
                    "error": str(e),
                }
        else:
            component_status["database"] = {
                "status": "configured",
                "type": "postgresql",
                "auto_migrate": settings.database.auto_migrate,
            }

        # OpenAI/Agent component
        if settings.openai.api_key and settings.openai.api_key != "your-api-key-here":
            component_status["agents"] = {
                "status": "healthy",
                "openai_configured": True,
            }
        else:
            component_status["agents"] = {
                "status": "misconfigured",
                "openai_configured": False,
                "message": "OpenAI API key not configured - agent functionality limited",
            }

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "configuration": info,
            "components": component_status,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration validation failed: {str(e)}")


# Configuration and logging setup

# 🚨 PRODUCTION SAFETY: Validate configuration at module level (fail-fast)
try:
    settings.validate_configuration()
except Exception as e:
    print(f"❌ CRITICAL: Configuration validation failed at startup: {e}")
    print("Please fix your configuration before starting the application.")
    exit(1)

# Set up logging
setup_logging()
logger = get_context_logger()

# Add middleware (order matters - RequestID first, then RequestLogger)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggerMiddleware)

# Include routers
app.include_router(pipeline_router)
app.include_router(examples_router)
app.include_router(agent_router)


# Add startup and shutdown events
# TODO: on_event is deprecated
@app.on_event("startup")
async def startup_event() -> None:
    """Application startup event with configuration validation and banner display."""
    try:
        # Print startup banner to console
        print_startup_banner(settings)

        # Log detailed startup information
        log_startup_info(settings, logger)

        # Validate configuration and check component status
        log_component_status(settings, logger)

        logger.info("🚀 Application startup completed successfully")

    except Exception as e:
        logger.error(f"❌ Application startup failed: {e}")
        logger.error("Please check your configuration and try again")
        # Re-raise to prevent startup with invalid configuration
        raise


# TODO: on_event is deprecated
@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Application shutdown event."""
    logger.info("🛑 Application shutting down gracefully")


# Run the application
if __name__ == "__main__":
    # Validate configuration before starting the server
    try:
        settings.validate_configuration()
        logger.info("✓ Pre-startup configuration validation passed")
    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        logger.error("Please fix your configuration before starting the server")
        exit(1)

    uvicorn.run(
        "apps.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.is_development,
        log_level=settings.api.log_level.lower(),
    )
