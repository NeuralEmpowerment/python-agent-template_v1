"""Decorators for the application."""

import functools
import time
from typing import Any, Callable, TypeVar, cast

from src.agent_project.infrastructure.logging import agent_logger, get_context_logger

# Type variable for function return type
T = TypeVar("T")


def timer_decorator(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to measure and log the execution time of a function.

    Args:
        func: The function to be decorated.

    Returns:
        The wrapped function with timing capabilities.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Extract pipeline_id and request_id from kwargs if available
        pipeline_id = kwargs.get("pipeline_id", "unknown")
        request_id = kwargs.get("request_id", "unknown")

        # Get logger
        logger = get_context_logger(pipeline_id=pipeline_id, request_id=request_id)

        # Start timer
        start_time = time.time()
        logger.debug(f"Starting execution of {func.__name__}")

        # Log pipeline start if pipeline_id is provided
        if pipeline_id != "unknown" and request_id != "unknown":
            agent_logger.log_pipeline_start(pipeline_id, request_id)

        try:
            # Execute the function
            result = func(*args, **kwargs)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log pipeline end if pipeline_id is provided
            if pipeline_id != "unknown" and request_id != "unknown":
                agent_logger.log_pipeline_end(pipeline_id, request_id, duration_ms)

            logger.info(
                f"Completed {func.__name__} in {duration_ms:.2f}ms",
                duration=duration_ms,
                function=func.__name__,
            )

            return result

        except Exception as e:
            # Calculate duration on error
            duration_ms = (time.time() - start_time) * 1000

            # Log the error
            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                duration=duration_ms,
                function=func.__name__,
                error=str(e),
                exc_info=True,
            )

            # Re-raise the exception
            raise

    return cast(Callable[..., T], wrapper)


def pipeline_timer(
    pipeline_id_key: str = "pipeline_id", request_id_key: str = "request_id"
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator factory to measure and log the execution time of a pipeline function.

    Args:
        pipeline_id_key: The key to use to extract the pipeline_id from kwargs.
        request_id_key: The key to use to extract the request_id from kwargs.

    Returns:
        A decorator function.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Extract IDs from kwargs
            pipeline_id = kwargs.get(pipeline_id_key, "unknown")
            request_id = kwargs.get(request_id_key, "unknown")

            # Get logger
            logger = get_context_logger(pipeline_id=pipeline_id, request_id=request_id)

            # Start timer
            start_time = time.time()

            # Log pipeline start
            if pipeline_id != "unknown" and request_id != "unknown":
                agent_logger.log_pipeline_start(pipeline_id, request_id)
                logger.info(f"Starting pipeline execution with id={pipeline_id}")

            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000

                # Log pipeline end
                if pipeline_id != "unknown" and request_id != "unknown":
                    agent_logger.log_pipeline_end(pipeline_id, request_id, duration_ms)
                    logger.info(f"Completed pipeline execution with id={pipeline_id} in {duration_ms:.2f}ms")

                return result

            except Exception as e:
                # Calculate duration on error
                duration_ms = (time.time() - start_time) * 1000

                # Log the error
                logger.error(
                    f"Pipeline execution failed: {str(e)}",
                    pipeline_id=pipeline_id,
                    request_id=request_id,
                    duration=duration_ms,
                    exc_info=True,
                )

                # Re-raise the exception
                raise

        return cast(Callable[..., T], wrapper)

    return decorator
