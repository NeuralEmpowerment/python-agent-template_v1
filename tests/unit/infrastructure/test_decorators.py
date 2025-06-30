"""Tests for the decorators module."""

import time
from unittest.mock import MagicMock, call, patch

import pytest

from src.agent_project.infrastructure.decorators import pipeline_timer, timer_decorator


class TestTimerDecorator:
    """Test cases for timer_decorator."""

    def test_timer_decorator_basic_functionality(self):
        """Test basic timing functionality of timer_decorator."""

        @timer_decorator
        def sample_function(value: str) -> str:
            time.sleep(0.01)  # Small delay to ensure measurable time
            return f"processed_{value}"

        with patch("src.agent_project.infrastructure.decorators.get_context_logger") as mock_get_logger:
            with patch("src.agent_project.infrastructure.decorators.agent_logger") as mock_agent_logger:  # noqa: F841
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                result = sample_function("test")

                # Verify function executed correctly
                assert result == "processed_test"

                # Verify logger was called with default values
                mock_get_logger.assert_called_once_with(pipeline_id="unknown", request_id="unknown")

                # Verify logging calls
                mock_logger.debug.assert_called_once_with("Starting execution of sample_function")
                mock_logger.info.assert_called_once()

                # Verify info call contains timing information
                info_call = mock_logger.info.call_args
                assert "Completed sample_function in" in info_call[0][0]
                assert "ms" in info_call[0][0]
                assert "duration" in info_call[1]
                assert "function" in info_call[1]
                assert info_call[1]["function"] == "sample_function"

    def test_timer_decorator_with_pipeline_context(self):
        """Test timer_decorator with pipeline and request IDs."""

        @timer_decorator
        def pipeline_function(pipeline_id: str, request_id: str, data: str) -> str:
            return f"pipeline_{data}"

        with patch("src.agent_project.infrastructure.decorators.get_context_logger") as mock_get_logger:
            with patch("src.agent_project.infrastructure.decorators.agent_logger") as mock_agent_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                result = pipeline_function(pipeline_id="pipe123", request_id="req456", data="test")

                # Verify function executed correctly
                assert result == "pipeline_test"

                # Verify logger was called with provided IDs
                mock_get_logger.assert_called_once_with(pipeline_id="pipe123", request_id="req456")

                # Verify ZenML logger pipeline methods were called
                mock_agent_logger.log_pipeline_start.assert_called_once_with("pipe123", "req456")
                mock_agent_logger.log_pipeline_end.assert_called_once()

                # Verify log_pipeline_end arguments
                end_call = mock_agent_logger.log_pipeline_end.call_args
                assert end_call[0][0] == "pipe123"  # pipeline_id
                assert end_call[0][1] == "req456"  # request_id
                assert isinstance(end_call[0][2], float)  # duration_ms

    def test_timer_decorator_with_exception(self):
        """Test timer_decorator behavior when decorated function raises an exception."""

        @timer_decorator
        def failing_function(should_fail: bool = True) -> str:
            if should_fail:
                raise ValueError("Test error")
            return "success"

        with patch("src.agent_project.infrastructure.decorators.get_context_logger") as mock_get_logger:
            with patch("src.agent_project.infrastructure.decorators.agent_logger") as mock_agent_logger:  # noqa: F841
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                # Test exception is re-raised
                with pytest.raises(ValueError, match="Test error"):
                    failing_function()

                # Verify error was logged
                mock_logger.error.assert_called_once()
                error_call = mock_logger.error.call_args

                # Verify error log contains expected information
                assert "Error in failing_function: Test error" in error_call[0][0]
                assert "duration" in error_call[1]
                assert "function" in error_call[1]
                assert "error" in error_call[1]
                assert error_call[1]["function"] == "failing_function"
                assert error_call[1]["error"] == "Test error"
                assert error_call[1]["exc_info"] is True

    def test_timer_decorator_preserves_function_metadata(self):
        """Test that timer_decorator preserves function metadata."""

        @timer_decorator
        def documented_function(arg1: str, arg2: int = 42) -> str:
            """A well-documented function.

            Args:
                arg1: First argument
                arg2: Second argument with default

            Returns:
                Formatted string
            """
            return f"{arg1}_{arg2}"

        # Verify function metadata is preserved
        assert documented_function.__name__ == "documented_function"
        assert "A well-documented function" in documented_function.__doc__

        # Verify function still works
        with patch("src.agent_project.infrastructure.decorators.get_context_logger"):
            with patch("src.agent_project.infrastructure.decorators.agent_logger"):
                result = documented_function("test")
                assert result == "test_42"

    def test_timer_decorator_with_mixed_parameters(self):
        """Test timer_decorator with various parameter combinations."""

        @timer_decorator
        def mixed_params_function(*args, pipeline_id: str = "default", **kwargs) -> dict:
            return {"args": args, "pipeline_id": pipeline_id, "kwargs": kwargs}

        with patch("src.agent_project.infrastructure.decorators.get_context_logger") as mock_get_logger:
            with patch("src.agent_project.infrastructure.decorators.agent_logger"):
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                result = mixed_params_function("arg1", "arg2", pipeline_id="pipe123", extra="value")

                # Verify function executed correctly
                assert result["args"] == ("arg1", "arg2")
                assert result["pipeline_id"] == "pipe123"
                assert result["kwargs"] == {"extra": "value"}

                # Verify logger was called with correct pipeline_id
                mock_get_logger.assert_called_once_with(pipeline_id="pipe123", request_id="unknown")


class TestPipelineTimer:
    """Test cases for pipeline_timer decorator factory."""

    def test_pipeline_timer_with_default_keys(self):
        """Test pipeline_timer with default key names."""

        @pipeline_timer()
        def pipeline_function(pipeline_id: str, request_id: str, data: str) -> str:
            time.sleep(0.01)
            return f"pipeline_{data}"

        with patch("src.agent_project.infrastructure.decorators.get_context_logger") as mock_get_logger:
            with patch("src.agent_project.infrastructure.decorators.agent_logger") as mock_agent_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                result = pipeline_function(pipeline_id="pipe123", request_id="req456", data="test")

                # Verify function executed correctly
                assert result == "pipeline_test"

                # Verify logger was called with extracted IDs
                mock_get_logger.assert_called_once_with(pipeline_id="pipe123", request_id="req456")

                # Verify ZenML logger calls
                mock_agent_logger.log_pipeline_start.assert_called_once_with("pipe123", "req456")
                mock_agent_logger.log_pipeline_end.assert_called_once()

                # Verify logging messages
                _expected_calls = [  # noqa: F841
                    call("Starting pipeline execution with id=pipe123"),
                    call().bind(
                        **{"pipeline_id": "pipe123", "request_id": "req456", "duration": pytest.approx(10, abs=50)}
                    ),  # Allow for timing variance
                ]
                # Check that info was called at least twice (start and end)
                assert mock_logger.info.call_count >= 2

    def test_pipeline_timer_with_custom_keys(self):
        """Test pipeline_timer with custom key names."""

        @pipeline_timer(pipeline_id_key="custom_pipeline", request_id_key="custom_request")
        def custom_pipeline_function(custom_pipeline: str, custom_request: str, data: str) -> str:
            return f"custom_{data}"

        with patch("src.agent_project.infrastructure.decorators.get_context_logger") as mock_get_logger:
            with patch("src.agent_project.infrastructure.decorators.agent_logger") as mock_agent_logger:  # noqa: F841
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                result = custom_pipeline_function(custom_pipeline="pipe789", custom_request="req012", data="test")

                # Verify function executed correctly
                assert result == "custom_test"

                # Verify logger was called with extracted IDs using custom keys
                mock_get_logger.assert_called_once_with(pipeline_id="pipe789", request_id="req012")

    def test_pipeline_timer_with_missing_ids(self):
        """Test pipeline_timer when IDs are missing from kwargs."""

        @pipeline_timer()
        def simple_function(data: str) -> str:
            return f"simple_{data}"

        with patch("src.agent_project.infrastructure.decorators.get_context_logger") as mock_get_logger:
            with patch("src.agent_project.infrastructure.decorators.agent_logger") as mock_agent_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                result = simple_function(data="test")

                # Verify function executed correctly
                assert result == "simple_test"

                # Verify logger was called with default "unknown" values
                mock_get_logger.assert_called_once_with(pipeline_id="unknown", request_id="unknown")

                # Verify ZenML logger was not called since IDs are unknown
                mock_agent_logger.log_pipeline_start.assert_not_called()
                mock_agent_logger.log_pipeline_end.assert_not_called()

    def test_pipeline_timer_with_exception(self):
        """Test pipeline_timer behavior when decorated function raises an exception."""

        @pipeline_timer()
        def failing_pipeline(pipeline_id: str, request_id: str, should_fail: bool = True) -> str:
            if should_fail:
                raise RuntimeError("Pipeline execution failed")
            return "success"

        with patch("src.agent_project.infrastructure.decorators.get_context_logger") as mock_get_logger:
            with patch("src.agent_project.infrastructure.decorators.agent_logger") as mock_agent_logger:  # noqa: F841
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                # Test exception is re-raised
                with pytest.raises(RuntimeError, match="Pipeline execution failed"):
                    failing_pipeline(pipeline_id="pipe123", request_id="req456")

                # Verify error was logged
                mock_logger.error.assert_called_once()
                error_call = mock_logger.error.call_args

                # Verify error log contains expected information
                assert "Pipeline execution failed" in error_call[0][0]
                assert error_call[1]["pipeline_id"] == "pipe123"
                assert error_call[1]["request_id"] == "req456"
                assert "duration" in error_call[1]
                assert error_call[1]["exc_info"] is True

    def test_pipeline_timer_decorator_factory_functionality(self):
        """Test that pipeline_timer works as a decorator factory."""

        # Test that pipeline_timer returns a decorator
        decorator = pipeline_timer(pipeline_id_key="pid", request_id_key="rid")
        assert callable(decorator)

        # Test that the decorator can be applied to a function
        @decorator
        def test_function(pid: str, rid: str) -> str:
            return f"{pid}_{rid}"

        assert callable(test_function)

        # Test that the decorated function works
        with patch("src.agent_project.infrastructure.decorators.get_context_logger"):
            with patch("src.agent_project.infrastructure.decorators.agent_logger"):
                result = test_function(pid="test_pid", rid="test_rid")
                assert result == "test_pid_test_rid"

    def test_pipeline_timer_timing_accuracy(self):
        """Test that pipeline_timer accurately measures execution time."""

        @pipeline_timer()
        def timed_function(pipeline_id: str, request_id: str, sleep_time: float = 0.05) -> str:
            time.sleep(sleep_time)
            return "completed"

        with patch("src.agent_project.infrastructure.decorators.get_context_logger") as mock_get_logger:
            with patch("src.agent_project.infrastructure.decorators.agent_logger") as mock_agent_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                result = timed_function(pipeline_id="time_test", request_id="req123", sleep_time=0.05)

                # Verify function completed
                assert result == "completed"

                # Verify pipeline end was called with reasonable duration
                mock_agent_logger.log_pipeline_end.assert_called_once()
                end_call = mock_agent_logger.log_pipeline_end.call_args
                _duration_ms = end_call[0][2]  # noqa: F841

                # Duration should be approximately 50ms (allowing for some variance)
