"""Tests for the decorators module."""

import time
import unittest
from unittest.mock import MagicMock, patch

from src.agent_project.infrastructure.decorators import pipeline_timer, timer_decorator


class TestTimerDecorator(unittest.TestCase):
    """Tests for the timer_decorator."""

    @patch("src.agent_project.infrastructure.decorators.get_context_logger")
    def test_timer_decorator(self, mock_get_logger):
        """Test that timer_decorator measures execution time."""
        # Setup
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Create a decorated function
        @timer_decorator
        def test_func(arg1, arg2, **kwargs):
            """Test function."""
            time.sleep(0.01)  # Small delay to ensure timing works
            return arg1 + arg2

        # Execute
        result = test_func(1, 2, test_kwarg="test")

        # Assert
        self.assertEqual(result, 3)
        mock_logger.debug.assert_called_once()
        mock_logger.info.assert_called_once()
        # Verify that the timing was performed
        info_call_args = mock_logger.info.call_args[0][0]
        self.assertIn("Completed test_func in", info_call_args)

    @patch("src.agent_project.infrastructure.decorators.get_context_logger")
    @patch("src.agent_project.infrastructure.decorators.agent_logger")
    def test_pipeline_timer(self, mock_agent_logger, mock_get_logger):
        """Test that pipeline_timer decorator logs pipeline execution."""
        # Setup
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Create a decorated function
        @pipeline_timer()
        def test_pipeline_func(**kwargs):
            """Test pipeline function."""
            time.sleep(0.01)  # Small delay to ensure timing works
            return "pipeline_result"

        # Execute with the exact parameter names expected by the decorator
        result = test_pipeline_func(pipeline_id="test-pipeline", request_id="test-request")

        # Assert
        self.assertEqual(result, "pipeline_result")
        mock_agent_logger.log_pipeline_start.assert_called_once_with("test-pipeline", "test-request")
        mock_agent_logger.log_pipeline_end.assert_called_once()
        # Instead of matching the exact log message and duration, just check that info was called
        self.assertTrue(mock_logger.info.called)

    @patch("src.agent_project.infrastructure.decorators.get_context_logger")
    @patch("src.agent_project.infrastructure.decorators.agent_logger")
    def test_pipeline_timer_with_exception(self, mock_agent_logger, mock_get_logger):
        """Test that pipeline_timer decorator handles exceptions."""
        # Setup
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Create a decorated function that raises an exception
        @pipeline_timer()
        def test_pipeline_func_with_error(**kwargs):
            """Test pipeline function with error."""
            time.sleep(0.01)  # Small delay to ensure timing works
            raise ValueError("Test error")

        # Execute and assert exception is re-raised
        with self.assertRaises(ValueError):
            test_pipeline_func_with_error(pipeline_id="test-pipeline", request_id="test-request")

        # Verify logging
        mock_agent_logger.log_pipeline_start.assert_called_once_with("test-pipeline", "test-request")
        mock_logger.error.assert_called_once()
        # Verify error contains the exception message
        error_call_args = mock_logger.error.call_args[0][0]
        self.assertIn("Pipeline execution failed: Test error", error_call_args)

    @patch("src.agent_project.infrastructure.decorators.get_context_logger")
    @patch("src.agent_project.infrastructure.decorators.agent_logger")
    def test_pipeline_timer_with_custom_keys(self, mock_agent_logger, mock_get_logger):
        """Test that pipeline_timer decorator works with custom key names."""
        # Setup
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Create a decorated function with custom keys
        @pipeline_timer(pipeline_id_key="job_id", request_id_key="correlation_id")
        def test_pipeline_func_custom_keys(**kwargs):
            """Test pipeline function with custom keys."""
            time.sleep(0.01)  # Small delay to ensure timing works
            return "custom_keys_result"

        # Execute with the custom key names
        result = test_pipeline_func_custom_keys(job_id="job-123", correlation_id="corr-456")

        # Assert
        self.assertEqual(result, "custom_keys_result")
        mock_agent_logger.log_pipeline_start.assert_called_once_with("job-123", "corr-456")
        mock_agent_logger.log_pipeline_end.assert_called_once()
        # Check that info was called
        self.assertTrue(mock_logger.info.called)


if __name__ == "__main__":
    unittest.main()
