"""Routes package for FastAPI endpoints."""

from .examples import router as examples_router
from .pipeline_routes import router as pipeline_router

__all__ = ["examples_router", "pipeline_router"]
