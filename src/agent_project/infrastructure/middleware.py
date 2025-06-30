"""Middleware classes for the application."""

import time
from typing import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.agent_project.infrastructure.logging import get_context_logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that adds a unique request ID to each request.

    This ID is added to the request state and returned in the X-Request-ID header.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        request.state.logger = get_context_logger(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware that logs request and response information.

    This middleware logs the request method, path, status code, and duration.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start_time = time.time()

        # Get the logger from the request state, or create a new one
        logger = getattr(request.state, "logger", get_context_logger(request_id=str(uuid4())))

        # Log the request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client=request.client.host if request.client else "unknown",
            event_type="request_start",
        )

        # Process the request
        try:
            response = await call_next(request)

            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000

            # Log the response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=int(duration_ms),
                event_type="request_end",
            )

            return response

        except Exception as e:
            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000

            # Log the error
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration=int(duration_ms),
                event_type="request_error",
                exc_info=True,
            )

            # Re-raise the exception
            raise
