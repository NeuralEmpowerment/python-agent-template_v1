"""Tests for the logging module."""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.agent_project.infrastructure.logging import (
    LOG_FILE_FORMAT,
    LOG_FORMAT,
    LOGS_DIR,
    AgentLogger,
    CustomLogger,
    LogContext,
    get_context_logger,
    setup_logging,
)


class TestSetupLogging:
    """Test cases for setup_logging function."""

    @patch("src.agent_project.infrastructure.logging.loguru_logger")
    @patch("src.agent_project.infrastructure.logging.settings")
    def test_setup_logging_development(self, mock_settings, mock_logger):
        """Test logging setup for development environment."""
        # Configure mock settings for development
        mock_settings.api.log_level = "DEBUG"
        mock_settings.api.is_production = False

        setup_logging()

        # Verify logger was removed first
        mock_logger.remove.assert_called_once()

        # Verify logger.add was called twice (console and file)
        assert mock_logger.add.call_count == 2

        # Verify console handler configuration
        console_call = mock_logger.add.call_args_list[0]
        assert console_call[0][0] == sys.stderr
        assert console_call[1]["format"] == LOG_FORMAT
        assert console_call[1]["level"] == "DEBUG"
        assert console_call[1]["enqueue"] is True
        assert console_call[1]["backtrace"] is True
        assert console_call[1]["diagnose"] is True

        # Verify file handler configuration
        file_call = mock_logger.add.call_args_list[1]
        assert str(LOGS_DIR / LOG_FILE_FORMAT) in str(file_call[0][0])
        assert file_call[1]["level"] == "DEBUG"  # Development uses same level as console

    @patch("src.agent_project.infrastructure.logging.loguru_logger")
    @patch("src.agent_project.infrastructure.logging.settings")
    def test_setup_logging_production(self, mock_settings, mock_logger):
        """Test logging setup for production environment."""
        # Configure mock settings for production
        mock_settings.api.log_level = "DEBUG"
        mock_settings.api.is_production = True

        setup_logging()

        # Verify console and file handlers have different levels in production
        console_call = mock_logger.add.call_args_list[0]
        file_call = mock_logger.add.call_args_list[1]

        assert console_call[1]["level"] == "DEBUG"  # Console uses setting level
        assert file_call[1]["level"] == "INFO"  # File uses INFO in production

    @patch("src.agent_project.infrastructure.logging.loguru_logger")
    @patch("src.agent_project.infrastructure.logging.settings")
    def test_setup_logging_info_level(self, mock_settings, mock_logger):
        """Test logging setup with INFO level."""
        mock_settings.api.log_level = "INFO"
        mock_settings.api.is_production = False

        setup_logging()

        # Verify both handlers use INFO level
        console_call = mock_logger.add.call_args_list[0]
        file_call = mock_logger.add.call_args_list[1]

        assert console_call[1]["level"] == "INFO"
        assert file_call[1]["level"] == "INFO"


class TestGetContextLogger:
    """Test cases for get_context_logger function."""

    @patch("src.agent_project.infrastructure.logging.loguru_logger")
    def test_get_context_logger_with_defaults(self, mock_logger):
        """Test get_context_logger with default context values."""
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger

        result = get_context_logger()

        # Verify logger.bind was called with default context
        expected_context = {
            "request_id": "unknown",
            "user_id": "unknown",
            "pipeline_id": "unknown",
            "step_id": "unknown",
            "duration": 0,
            "event_type": "general",
        }
        mock_logger.bind.assert_called_once_with(**expected_context)
        assert result == mock_bound_logger

    @patch("src.agent_project.infrastructure.logging.loguru_logger")
    def test_get_context_logger_with_custom_context(self, mock_logger):
        """Test get_context_logger with custom context values."""
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger

        custom_context = {
            "request_id": "req123",
            "pipeline_id": "pipe456",
            "user_id": "user789",
            "custom_field": "custom_value",
        }

        result = get_context_logger(**custom_context)

        # Verify logger.bind was called with merged context (custom values override defaults)
        expected_context = {
            "request_id": "req123",
            "user_id": "user789",
            "pipeline_id": "pipe456",
            "step_id": "unknown",  # Default value preserved
            "duration": 0,  # Default value preserved
            "event_type": "general",  # Default value preserved
            "custom_field": "custom_value",  # Custom field added
        }
        mock_logger.bind.assert_called_once_with(**expected_context)
        assert result == mock_bound_logger

    @patch("src.agent_project.infrastructure.logging.loguru_logger")
    def test_get_context_logger_with_partial_override(self, mock_logger):
        """Test get_context_logger with partial context override."""
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger

        _result = get_context_logger(request_id="req999", duration=150)  # noqa: F841

        # Verify only specified fields are overridden
        expected_context = {
            "request_id": "req999",  # Overridden
            "user_id": "unknown",  # Default
            "pipeline_id": "unknown",  # Default
            "step_id": "unknown",  # Default
            "duration": 150,  # Overridden
            "event_type": "general",  # Default
        }
        mock_logger.bind.assert_called_once_with(**expected_context)


class TestLogContext:
    """Test cases for LogContext class."""

    def test_log_context_initialization(self):
        """Test LogContext initialization."""
        context = LogContext(request_id="req123", pipeline_id="pipe456")

        assert context.start_time is None
        assert context.context == {"request_id": "req123", "pipeline_id": "pipe456"}

    @patch("src.agent_project.infrastructure.logging.get_context_logger")
    def test_log_context_enter_exit_success(self, mock_get_logger):
        """Test LogContext as context manager with successful operation."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger

        test_context = {"request_id": "req123", "event": "test"}

        with LogContext(**test_context) as ctx:
            # Verify enter behavior
            assert ctx.start_time is not None
            assert isinstance(ctx.start_time, datetime)

            # Verify initial logging
            mock_logger.info.assert_called_once_with(f"Starting operation with context: {test_context}")

            # Simulate some work
            import time

            time.sleep(0.01)

        # Verify exit behavior - success path
        mock_logger.bind.assert_called_once()
        bind_call = mock_logger.bind.call_args[1]

        # Verify context contains original fields plus duration
        assert "request_id" in bind_call
        assert "event" in bind_call
        assert "duration" in bind_call
        assert bind_call["request_id"] == "req123"
        assert bind_call["event"] == "test"
        assert isinstance(bind_call["duration"], int)
        assert bind_call["duration"] > 0  # Should have some duration

        # Verify success logging
        mock_bound_logger.info.assert_called_once()
        success_call = mock_bound_logger.info.call_args[0][0]
        assert "Operation completed successfully" in success_call
        assert "ms" in success_call

    @patch("src.agent_project.infrastructure.logging.get_context_logger")
    def test_log_context_enter_exit_with_exception(self, mock_get_logger):
        """Test LogContext as context manager with exception."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger

        test_context = {"request_id": "req123"}
        test_exception = ValueError("Test error")

        with pytest.raises(ValueError):
            with LogContext(**test_context):
                raise test_exception

        # Verify exception logging
        mock_bound_logger.error.assert_called_once()
        error_call = mock_bound_logger.error.call_args

        assert "Operation failed: Test error" in error_call[0][0]
        assert "exc_info" in error_call[1]
        # The exc_info should be a tuple, just verify it's the right structure
        exc_info = error_call[1]["exc_info"]
        assert len(exc_info) == 3
        assert exc_info[0] == ValueError
        assert str(exc_info[1]) == "Test error"
        assert exc_info[2] is not None  # Traceback object

    @patch("src.agent_project.infrastructure.logging.get_context_logger")
    def test_log_context_without_start_time(self, mock_get_logger):
        """Test LogContext when start_time is None (edge case)."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger

        context = LogContext(test="value")
        # Manually set start_time to None to test edge case
        context.start_time = None

        # Call __exit__ directly
        context.__exit__(None, None, None)

        # Verify duration is 0 when start_time is None
        bind_call = mock_logger.bind.call_args[1]
        assert bind_call["duration"] == 0


class TestCustomLogger:
    """Test cases for CustomLogger class."""

    def test_custom_logger_initialization(self):
        """Test CustomLogger initialization."""
        logger = CustomLogger()

        assert logger._start_time is None
        assert logger._end_time is None
        assert hasattr(logger, "_logger")

    def test_start_timer(self):
        """Test start_timer method."""
        logger = CustomLogger()

        before = datetime.now()
        logger.start_timer()
        after = datetime.now()

        assert logger._start_time is not None
        assert before <= logger._start_time <= after

    def test_end_timer_with_start_time(self):
        """Test end_timer method when start_time is set."""
        logger = CustomLogger()
        logger.start_timer()

        # Small delay to ensure measurable time
        import time

        time.sleep(0.01)

        result = logger.end_timer()

        assert result is not None
        assert isinstance(result, timedelta)
        assert result.total_seconds() > 0
        assert logger._end_time is not None

    def test_end_timer_without_start_time(self):
        """Test end_timer method when start_time is None."""
        logger = CustomLogger()

        result = logger.end_timer()

        assert result is None

    def test_get_elapsed_time_with_start_time(self):
        """Test get_elapsed_time method when start_time is set."""
        logger = CustomLogger()
        logger.start_timer()

        import time

        time.sleep(0.01)

        result = logger.get_elapsed_time()

        assert result is not None
        assert isinstance(result, timedelta)
        assert result.total_seconds() > 0

    def test_get_elapsed_time_without_start_time(self):
        """Test get_elapsed_time method when start_time is None."""
        logger = CustomLogger()

        result = logger.get_elapsed_time()

        assert result is None

    @patch("src.agent_project.infrastructure.logging.loguru_logger")
    def test_logging_methods(self, mock_logger):
        """Test all logging methods delegate to loguru_logger."""
        logger = CustomLogger()

        # Test each logging method
        logger.info("Info message", extra="data")
        logger.error("Error message", error="details")
        logger.warning("Warning message", context="test")
        logger.debug("Debug message", debug=True)

        # Verify all calls were made to loguru_logger
        mock_logger.info.assert_called_once_with("Info message", extra="data")
        mock_logger.error.assert_called_once_with("Error message", error="details")
        mock_logger.warning.assert_called_once_with("Warning message", context="test")
        mock_logger.debug.assert_called_once_with("Debug message", debug=True)

    @patch("src.agent_project.infrastructure.logging.loguru_logger")
    def test_bind_method(self, mock_logger):
        """Test bind method delegates to loguru_logger."""
        logger = CustomLogger()
        mock_bound_logger = MagicMock()
        mock_logger.bind.return_value = mock_bound_logger

        result = logger.bind(request_id="req123", context="test")

        mock_logger.bind.assert_called_once_with(request_id="req123", context="test")
        assert result == mock_bound_logger


class TestAgentLogger:
    """Test cases for AgentLogger class."""

    def test_agent_logger_inheritance(self):
        """Test AgentLogger inherits from CustomLogger."""
        logger = AgentLogger()

        assert isinstance(logger, CustomLogger)
        assert hasattr(logger, "start_timer")
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")

    @patch("src.agent_project.infrastructure.logging.loguru_logger")
    def test_log_pipeline_start(self, mock_logger):
        """Test log_pipeline_start method."""
        logger = AgentLogger()

        logger.log_pipeline_start("pipe123", "req456")

        # Verify info logging was called with correct parameters
        mock_logger.info.assert_called_once_with(
            "Starting pipeline execution",
            pipeline_id="pipe123",
            request_id="req456",
            user_id="unknown",
            step_id="unknown",
            duration=0,
            event_type="pipeline_start",
        )

    @patch("src.agent_project.infrastructure.logging.loguru_logger")
    def test_log_pipeline_end(self, mock_logger):
        """Test log_pipeline_end method."""
        logger = AgentLogger()

        logger.log_pipeline_end("pipe123", "req456", 1500.5)

        # Verify info logging was called with correct parameters
        mock_logger.info.assert_called_once_with(
            "Pipeline execution completed",
            pipeline_id="pipe123",
            request_id="req456",
            user_id="unknown",
            step_id="unknown",
            duration=1500.5,
            event_type="pipeline_end",
        )

    @patch("src.agent_project.infrastructure.logging.loguru_logger")
    def test_log_step_start(self, mock_logger):
        """Test log_step_start method."""
        logger = AgentLogger()

        logger.log_step_start("pipe123", "step456", "req789")

        # Verify info logging was called with correct parameters
        mock_logger.info.assert_called_once_with(
            "Starting pipeline step step456",
            pipeline_id="pipe123",
            step_id="step456",
            request_id="req789",
            user_id="unknown",
            duration=0,
            event_type="step_start",
        )

    @patch("src.agent_project.infrastructure.logging.loguru_logger")
    def test_log_step_end(self, mock_logger):
        """Test log_step_end method."""
        logger = AgentLogger()

        logger.log_step_end("pipe123", "step456", "req789", 750.25)

        # Verify info logging was called with correct parameters
        mock_logger.info.assert_called_once_with(
            "Pipeline step step456 completed",
            pipeline_id="pipe123",
            step_id="step456",
            request_id="req789",
            user_id="unknown",
            duration=750.25,
            event_type="step_end",
        )


class TestLoggingConstants:
    """Test cases for logging constants and configuration."""

    def test_logs_directory_creation(self):
        """Test that LOGS_DIR is created and is a Path object."""
        assert isinstance(LOGS_DIR, Path)
        assert LOGS_DIR.name == "logs"
        # Directory should exist (created during import)
        assert LOGS_DIR.exists()

    def test_log_format_structure(self):
        """Test that LOG_FORMAT contains expected placeholders."""
        expected_placeholders = [
            "{time:YYYY-MM-DD HH:mm:ss.SSS}",
            "{level: <8}",  # Corrected format with padding
            "{name}",
            "{function}",
            "{line}",
            "{message}",
            "request_id={extra[request_id]!s}",
            "user_id={extra[user_id]!s}",
            "pipeline_id={extra[pipeline_id]!s}",
            "step_id={extra[step_id]!s}",
            "duration={extra[duration]!s}ms",
        ]

        for placeholder in expected_placeholders:
            assert placeholder in LOG_FORMAT

    def test_log_file_format(self):
        """Test LOG_FILE_FORMAT structure."""
        assert "agent_template_" in LOG_FILE_FORMAT
        assert "{time:YYYY-MM-DD}" in LOG_FILE_FORMAT
        assert ".log" in LOG_FILE_FORMAT
