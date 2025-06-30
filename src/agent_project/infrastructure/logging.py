"""Logging configuration for the application."""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union

from loguru import logger as loguru_logger

from src.agent_project.config import get_settings

# Get application settings
settings = get_settings()

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Log file naming format
LOG_FILE_FORMAT = "agent_template_{time:YYYY-MM-DD}.log"

# Log rotation configuration
LOG_ROTATION = "00:00"  # Rotate at midnight
LOG_RETENTION = "30 days"  # Keep logs for 30 days
LOG_COMPRESSION = "zip"  # Compress rotated logs

# Log format with safe access to extra fields
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level> | "
    "request_id={extra[request_id]!s} | "
    "user_id={extra[user_id]!s} | "
    "pipeline_id={extra[pipeline_id]!s} | "
    "step_id={extra[step_id]!s} | "
    "duration={extra[duration]!s}ms"
)


def setup_logging() -> None:
    """Configure application-wide logging settings."""
    # Remove default logger
    loguru_logger.remove()

    # Determine log level from settings
    console_level = settings.api.log_level
    file_level = "INFO" if settings.api.is_production else settings.api.log_level

    # Add console handler
    loguru_logger.add(
        sys.stderr,
        format=LOG_FORMAT,
        level=console_level,
        enqueue=True,  # Thread-safe logging
        backtrace=True,  # Detailed traceback
        diagnose=True,  # Enable exception diagnosis
    )

    # Add file handler with rotation
    loguru_logger.add(
        str(LOGS_DIR / LOG_FILE_FORMAT),
        format=LOG_FORMAT,
        level=file_level,
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        compression=LOG_COMPRESSION,
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )


def get_context_logger(**kwargs: Union[str, int, float, None]) -> Any:
    """Create a contextualized logger with the provided fields.

    Args:
        **kwargs: Arbitrary context fields to be included in log messages.

    Returns:
        Any: Contextualized logger instance.
    """
    # Define all required fields for the logging format
    default_context: Dict[str, Any] = {
        "request_id": "unknown",
        "user_id": "unknown",
        "pipeline_id": "unknown",
        "step_id": "unknown",
        "duration": 0,
        "event_type": "general",
    }

    # Merge provided kwargs with defaults, keeping kwargs values when both exist
    context = {**default_context, **kwargs}

    # Create a bound logger with the complete context
    return loguru_logger.bind(**context)


class LogContext:
    """Context manager for timing and logging operations."""

    def __init__(self, **kwargs: Union[str, int, float, None]) -> None:
        """Initialize the context with logging fields.

        Args:
            **kwargs: Context fields to be included in log messages.
        """
        self.start_time: Optional[datetime] = None
        self.logger = get_context_logger(**kwargs)
        self.context = kwargs

    def __enter__(self) -> "LogContext":
        """Enter the context and start timing.

        Returns:
            LogContext: The context manager instance.
        """
        self.start_time = datetime.now()
        self.logger.info(f"Starting operation with context: {self.context}")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context, calculate duration, and log any exceptions.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if self.start_time is None:
            duration = 0.0
        else:
            duration = (datetime.now() - self.start_time).total_seconds() * 1000
        context = {**self.context, "duration": int(duration)}

        if exc_type is not None:
            # Log exception with context
            self.logger.bind(**context).error(
                f"Operation failed: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb),
            )
        else:
            # Log success with duration
            self.logger.bind(**context).info(f"Operation completed successfully in {duration:.2f}ms")


class CustomLogger:
    """Custom logger class that wraps loguru logger."""

    def __init__(self) -> None:
        self._logger = loguru_logger
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None

    def start_timer(self) -> None:
        self._start_time = datetime.now()

    def end_timer(self) -> Optional[timedelta]:
        if self._start_time is None:
            return None
        self._end_time = datetime.now()
        return self._end_time - self._start_time

    def get_elapsed_time(self) -> Optional[timedelta]:
        if self._start_time is None:
            return None
        current_time = datetime.now()
        return current_time - self._start_time

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        self._logger.info(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        self._logger.error(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        self._logger.warning(message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        self._logger.debug(message, **kwargs)

    def bind(self, **kwargs: Any) -> Any:
        """Bind contextual information to the logger."""
        return loguru_logger.bind(**kwargs)


class AgentLogger(CustomLogger):
    """Agent-specific logger class that extends the CustomLogger."""

    def __init__(self) -> None:
        super().__init__()

    def log_pipeline_start(self, pipeline_id: str, request_id: str) -> None:
        """Log the start of a pipeline execution.

        Args:
            pipeline_id: Unique identifier for the pipeline run
            request_id: Correlation ID for the request
        """
        # Include all required fields from the LOG_FORMAT
        self.info(
            "Starting pipeline execution",
            pipeline_id=pipeline_id,
            request_id=request_id,
            user_id="unknown",
            step_id="unknown",
            duration=0,
            event_type="pipeline_start",
        )

    def log_pipeline_end(self, pipeline_id: str, request_id: str, duration_ms: float) -> None:
        """Log the end of a pipeline execution.

        Args:
            pipeline_id: Unique identifier for the pipeline run
            request_id: Correlation ID for the request
            duration_ms: Duration of the pipeline execution in milliseconds
        """
        # Include all required fields from the LOG_FORMAT
        self.info(
            "Pipeline execution completed",
            pipeline_id=pipeline_id,
            request_id=request_id,
            user_id="unknown",
            step_id="unknown",
            duration=duration_ms,
            event_type="pipeline_end",
        )

    def log_step_start(self, pipeline_id: str, step_id: str, request_id: str) -> None:
        """Log the start of a pipeline step.

        Args:
            pipeline_id: Unique identifier for the pipeline run
            step_id: Identifier for the specific step
            request_id: Correlation ID for the request
        """
        # Include all required fields from the LOG_FORMAT
        self.info(
            f"Starting pipeline step {step_id}",
            pipeline_id=pipeline_id,
            step_id=step_id,
            request_id=request_id,
            user_id="unknown",
            duration=0,
            event_type="step_start",
        )

    def log_step_end(self, pipeline_id: str, step_id: str, request_id: str, duration_ms: float) -> None:
        """Log the end of a pipeline step.

        Args:
            pipeline_id: Unique identifier for the pipeline run
            step_id: Identifier for the specific step
            request_id: Correlation ID for the request
            duration_ms: Duration of the step execution in milliseconds
        """
        # Include all required fields from the LOG_FORMAT
        self.info(
            f"Pipeline step {step_id} completed",
            pipeline_id=pipeline_id,
            step_id=step_id,
            request_id=request_id,
            user_id="unknown",
            duration=duration_ms,
            event_type="step_end",
        )


# Create global logger instances
logger = CustomLogger()
agent_logger = AgentLogger()

# Initialize logging when module is imported
setup_logging()
