"""Unit tests for correlation context management."""

import asyncio
import uuid

import pytest

from src.agent_project.correlation import (
    CorrelationContext,
    create_correlation_context,
    get_correlation_context,
    get_correlation_id,
    set_correlation_context,
    set_correlation_id,
)


class TestCorrelationContext:
    """Test cases for CorrelationContext dataclass."""

    def test_create_with_defaults(self):
        """Test creating correlation context with default values."""
        context = CorrelationContext.create()

        assert context.correlation_id is not None
        assert context.request_id is None
        assert context.user_id is None
        # Verify correlation_id is a valid UUID
        uuid.UUID(context.correlation_id)

    def test_create_with_values(self):
        """Test creating correlation context with provided values."""
        request_id = "req-123"
        user_id = "user-456"

        context = CorrelationContext.create(request_id=request_id, user_id=user_id)

        assert context.correlation_id is not None
        assert context.request_id == request_id
        assert context.user_id == user_id
        uuid.UUID(context.correlation_id)

    def test_dataclass_immutability(self):
        """Test that CorrelationContext is immutable."""
        context = CorrelationContext.create()

        with pytest.raises(AttributeError):
            context.correlation_id = "new-id"


class TestCorrelationFunctions:
    """Test cases for correlation context functions."""

    def test_set_and_get_correlation_context(self):
        """Test setting and getting correlation context."""
        context = CorrelationContext.create(request_id="req-123", user_id="user-456")

        set_correlation_context(context)
        retrieved_context = get_correlation_context()

        assert retrieved_context == context
        assert retrieved_context.correlation_id == context.correlation_id
        assert retrieved_context.request_id == "req-123"
        assert retrieved_context.user_id == "user-456"

    def test_get_correlation_id(self):
        """Test getting correlation ID directly."""
        context = CorrelationContext.create()
        set_correlation_context(context)

        correlation_id = get_correlation_id()

        assert correlation_id == context.correlation_id

    def test_set_correlation_id(self):
        """Test setting correlation ID while preserving other context."""
        # Set initial context
        initial_context = CorrelationContext.create(request_id="req-123", user_id="user-456")
        set_correlation_context(initial_context)

        # Set new correlation ID
        new_correlation_id = str(uuid.uuid4())
        set_correlation_id(new_correlation_id)

        # Verify correlation ID changed but other fields preserved
        updated_context = get_correlation_context()
        assert updated_context.correlation_id == new_correlation_id
        assert updated_context.request_id == "req-123"
        assert updated_context.user_id == "user-456"

    def test_create_correlation_context_with_all_params(self):
        """Test creating correlation context with all parameters."""
        request_id = "req-123"
        user_id = "user-456"
        correlation_id = str(uuid.uuid4())

        context = create_correlation_context(request_id=request_id, user_id=user_id, correlation_id=correlation_id)

        assert context.correlation_id == correlation_id
        assert context.request_id == request_id
        assert context.user_id == user_id

    def test_create_correlation_context_generates_id_if_none(self):
        """Test that correlation ID is generated if not provided."""
        context = create_correlation_context(request_id="req-123", user_id="user-456")

        assert context.correlation_id is not None
        assert context.request_id == "req-123"
        assert context.user_id == "user-456"
        # Verify generated ID is valid UUID
        uuid.UUID(context.correlation_id)


class TestAsyncContextPropagation:
    """Test cases for async context propagation."""

    @pytest.mark.asyncio
    async def test_context_propagates_across_async_calls(self):
        """Test that correlation context propagates across async calls."""
        test_correlation_id = str(uuid.uuid4())
        context = CorrelationContext(correlation_id=test_correlation_id, request_id="req-123")

        async def async_task():
            # Context should be available in async task
            retrieved_context = get_correlation_context()
            return retrieved_context.correlation_id

        # Set context and run async task
        set_correlation_context(context)
        result = await async_task()

        assert result == test_correlation_id

    @pytest.mark.asyncio
    async def test_context_isolation_between_async_tasks(self):
        """Test that different async tasks have isolated contexts."""

        async def task_with_context(correlation_id: str) -> str:
            context = CorrelationContext(correlation_id=correlation_id)
            set_correlation_context(context)

            # Simulate some async work
            await asyncio.sleep(0.01)

            return get_correlation_id()

        # Run multiple tasks concurrently with different correlation IDs
        correlation_id_1 = str(uuid.uuid4())
        correlation_id_2 = str(uuid.uuid4())

        results = await asyncio.gather(task_with_context(correlation_id_1), task_with_context(correlation_id_2))

        assert results[0] == correlation_id_1
        assert results[1] == correlation_id_2
        assert results[0] != results[1]

    def test_default_context_available(self):
        """Test that default context is always available."""
        # Even without setting context, should have default
        context = get_correlation_context()

        assert context is not None
        assert context.correlation_id is not None
        # Should be valid UUID
        uuid.UUID(context.correlation_id)
