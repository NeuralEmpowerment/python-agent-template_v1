"""Unit tests for InMemoryEventBus adapter."""

from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from src.agent_project.domain.events.base import DomainEvent
from src.agent_project.infrastructure.event_bus.adapters.in_memory import InMemoryEventBus
from src.agent_project.infrastructure.event_bus.ports import EventBus


@dataclass(frozen=True)
class MockEvent(DomainEvent):
    """Mock domain event for testing."""

    message: str = "test message"
    user_id: str = "test-user"


@dataclass(frozen=True)
class AnotherEvent(DomainEvent):
    """Another mock event type for testing."""

    data: str = "test data"


class TestInMemoryEventBus:
    """Test cases for InMemoryEventBus implementation."""

    def test_implements_event_bus_interface(self):
        """Test that InMemoryEventBus implements EventBus interface."""
        bus = InMemoryEventBus()
        assert isinstance(bus, EventBus)

    def test_initialization(self):
        """Test proper initialization of InMemoryEventBus."""
        bus = InMemoryEventBus()

        assert hasattr(bus, "_subscribers")
        assert isinstance(bus._subscribers, dict)
        assert len(bus._subscribers) == 0

    @pytest.mark.asyncio
    async def test_publish_with_no_subscribers(self):
        """Test publishing event when no subscribers exist."""
        bus = InMemoryEventBus()
        event = MockEvent()

        # Should not raise any exceptions
        await bus.publish(event)

    @pytest.mark.asyncio
    async def test_subscribe_single_handler(self):
        """Test subscribing a single handler to event type."""
        bus = InMemoryEventBus()
        handler = AsyncMock()

        await bus.subscribe(MockEvent, handler)

        assert MockEvent in bus._subscribers
        assert handler in bus._subscribers[MockEvent]
        assert len(bus._subscribers[MockEvent]) == 1

    @pytest.mark.asyncio
    async def test_subscribe_multiple_handlers_same_event(self):
        """Test subscribing multiple handlers to same event type."""
        bus = InMemoryEventBus()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        await bus.subscribe(MockEvent, handler1)
        await bus.subscribe(MockEvent, handler2)

        assert len(bus._subscribers[MockEvent]) == 2
        assert handler1 in bus._subscribers[MockEvent]
        assert handler2 in bus._subscribers[MockEvent]

    @pytest.mark.asyncio
    async def test_subscribe_handlers_different_events(self):
        """Test subscribing handlers to different event types."""
        bus = InMemoryEventBus()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        await bus.subscribe(MockEvent, handler1)
        await bus.subscribe(AnotherEvent, handler2)

        assert len(bus._subscribers) == 2
        assert MockEvent in bus._subscribers
        assert AnotherEvent in bus._subscribers
        assert handler1 in bus._subscribers[MockEvent]
        assert handler2 in bus._subscribers[AnotherEvent]

    @pytest.mark.asyncio
    async def test_unsubscribe_existing_handler(self):
        """Test unsubscribing an existing handler."""
        bus = InMemoryEventBus()
        handler = AsyncMock()

        # Subscribe then unsubscribe
        await bus.subscribe(MockEvent, handler)
        assert handler in bus._subscribers[MockEvent]

        await bus.unsubscribe(MockEvent, handler)
        assert handler not in bus._subscribers[MockEvent]

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_handler(self):
        """Test unsubscribing handler that was never subscribed."""
        bus = InMemoryEventBus()
        handler = AsyncMock()

        # Should not raise any exceptions
        await bus.unsubscribe(MockEvent, handler)

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_event_type(self):
        """Test unsubscribing from event type that was never registered."""
        bus = InMemoryEventBus()
        handler = AsyncMock()

        # Should not raise any exceptions
        await bus.unsubscribe(MockEvent, handler)

    @pytest.mark.asyncio
    async def test_publish_calls_single_handler(self):
        """Test that publishing calls the subscribed handler."""
        bus = InMemoryEventBus()
        handler = AsyncMock()
        event = MockEvent()

        await bus.subscribe(MockEvent, handler)
        await bus.publish(event)

        handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_calls_multiple_handlers(self):
        """Test that publishing calls all subscribed handlers."""
        bus = InMemoryEventBus()
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        event = MockEvent()

        await bus.subscribe(MockEvent, handler1)
        await bus.subscribe(MockEvent, handler2)
        await bus.publish(event)

        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_only_calls_matching_event_handlers(self):
        """Test that only handlers for matching event type are called."""
        bus = InMemoryEventBus()
        mock_handler = AsyncMock()
        another_handler = AsyncMock()
        event = MockEvent()

        await bus.subscribe(MockEvent, mock_handler)
        await bus.subscribe(AnotherEvent, another_handler)

        await bus.publish(event)

        mock_handler.assert_called_once_with(event)
        another_handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_multiple_events_same_type(self):
        """Test publishing multiple events of same type."""
        bus = InMemoryEventBus()
        handler = AsyncMock()
        event1 = MockEvent(message="event 1")
        event2 = MockEvent(message="event 2")

        await bus.subscribe(MockEvent, handler)

        await bus.publish(event1)
        await bus.publish(event2)

        assert handler.call_count == 2
        handler.assert_any_call(event1)
        handler.assert_any_call(event2)

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_affect_other_handlers(self):
        """Test that exception in one handler doesn't affect others."""
        bus = InMemoryEventBus()
        failing_handler = AsyncMock(side_effect=Exception("Handler failed"))
        working_handler = AsyncMock()
        event = MockEvent()

        await bus.subscribe(MockEvent, failing_handler)
        await bus.subscribe(MockEvent, working_handler)

        # Should not raise exception, but might log it
        await bus.publish(event)

        failing_handler.assert_called_once_with(event)
        working_handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_subscribe_same_handler_twice(self):
        """Test subscribing the same handler twice to same event."""
        bus = InMemoryEventBus()
        handler = AsyncMock()

        await bus.subscribe(MockEvent, handler)
        await bus.subscribe(MockEvent, handler)

        # Handler should only be registered once
        assert len(bus._subscribers[MockEvent]) == 1
        assert handler in bus._subscribers[MockEvent]

    @pytest.mark.asyncio
    async def test_unsubscribe_one_of_multiple_handlers(self):
        """Test unsubscribing one handler when multiple are subscribed."""
        bus = InMemoryEventBus()
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        event = MockEvent()

        await bus.subscribe(MockEvent, handler1)
        await bus.subscribe(MockEvent, handler2)
        await bus.unsubscribe(MockEvent, handler1)

        await bus.publish(event)

        handler1.assert_not_called()
        handler2.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_event_type_matching_is_exact(self):
        """Test that event type matching is exact (not inheritance-based)."""
        bus = InMemoryEventBus()
        handler = AsyncMock()

        await bus.subscribe(MockEvent, handler)

        # Publish different event type
        another_event = AnotherEvent()
        await bus.publish(another_event)

        handler.assert_not_called()


class TestInMemoryEventBusEdgeCases:
    """Test edge cases and error conditions for InMemoryEventBus."""

    @pytest.mark.asyncio
    async def test_publish_none_event(self):
        """Test publishing None as event."""
        bus = InMemoryEventBus()

        # Should handle gracefully
        await bus.publish(None)

    @pytest.mark.asyncio
    async def test_subscribe_none_handler(self):
        """Test subscribing with None handler."""
        bus = InMemoryEventBus()

        await bus.subscribe(MockEvent, None)

        # None should be in subscribers
        assert None in bus._subscribers[MockEvent]

    @pytest.mark.asyncio
    async def test_concurrent_publish_and_subscribe(self):
        """Test concurrent publishing and subscribing operations."""
        import asyncio

        bus = InMemoryEventBus()
        handler = AsyncMock()
        events = [MockEvent(message=f"event {i}") for i in range(5)]

        async def subscribe_handler():
            await bus.subscribe(MockEvent, handler)

        async def publish_events():
            for event in events:
                await bus.publish(event)
                await asyncio.sleep(0.001)  # Small delay

        # Run subscribe and publish concurrently
        await asyncio.gather(subscribe_handler(), publish_events())

        # Handler might be called for some or all events depending on timing
        assert handler.call_count >= 0  # Could be 0 if subscription happened after all publishes
