"""Integration tests for LoggingEventBus that test actual behavior."""

from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from src.agent_project.correlation import clear_correlation_id, set_correlation_id
from src.agent_project.domain.events.base import DomainEvent
from src.agent_project.infrastructure.event_bus.adapters.in_memory import InMemoryEventBus
from src.agent_project.infrastructure.event_bus.adapters.logging import LoggingEventBus
from src.agent_project.infrastructure.event_bus.ports import EventBus, PublishError, SubscriptionError


@dataclass(frozen=True)
class MockEvent(DomainEvent):
    """Mock domain event for testing."""

    message: str = "test message"
    user_id: str = "test-user"


@dataclass(frozen=True)
class AnotherEvent(DomainEvent):
    """Another mock event type for testing."""

    data: str = "test data"


class TestLoggingEventBusIntegration:
    """Integration tests for LoggingEventBus with real inner bus."""

    def test_implements_event_bus_interface(self):
        """Test that LoggingEventBus implements EventBus interface."""
        inner_bus = InMemoryEventBus()
        bus = LoggingEventBus(inner_bus)
        assert isinstance(bus, EventBus)

    def test_initialization_with_inner_bus(self):
        """Test proper initialization with inner bus."""
        inner_bus = InMemoryEventBus()
        bus = LoggingEventBus(inner_bus)

        assert hasattr(bus, "_inner_bus")
        assert bus._inner_bus is inner_bus

    def test_initialization_without_inner_bus(self):
        """Test initialization without inner bus (None)."""
        bus = LoggingEventBus(None)

        assert hasattr(bus, "_inner_bus")
        assert bus._inner_bus is None

    @pytest.mark.asyncio
    async def test_publish_calls_inner_bus(self):
        """Test that publish calls the inner bus."""
        inner_bus = InMemoryEventBus()
        bus = LoggingEventBus(inner_bus)
        handler = AsyncMock()
        event = MockEvent()

        # Subscribe handler to verify event reaches inner bus
        await inner_bus.subscribe(MockEvent, handler)
        await bus.publish(event)

        # Handler should be called, proving inner bus was used
        handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_without_inner_bus(self):
        """Test publish when no inner bus is provided."""
        bus = LoggingEventBus(None)
        event = MockEvent()

        # Should not raise exception
        await bus.publish(event)

    @pytest.mark.asyncio
    async def test_publish_handles_inner_bus_exception(self):
        """Test that publish re-raises exceptions from inner bus."""
        inner_bus = AsyncMock(spec=EventBus)
        inner_bus.publish.side_effect = PublishError("Inner bus failed")
        bus = LoggingEventBus(inner_bus)
        event = MockEvent()

        with pytest.raises(PublishError, match="Inner bus failed"):
            await bus.publish(event)

    @pytest.mark.asyncio
    async def test_subscribe_calls_inner_bus(self):
        """Test that subscribe calls the inner bus."""
        inner_bus = InMemoryEventBus()
        bus = LoggingEventBus(inner_bus)
        handler = AsyncMock()

        await bus.subscribe(MockEvent, handler)

        # Verify handler was registered in inner bus
        assert inner_bus.get_subscriber_count(MockEvent) == 1

    @pytest.mark.asyncio
    async def test_subscribe_without_inner_bus(self):
        """Test subscribe when no inner bus is provided."""
        bus = LoggingEventBus(None)
        handler = AsyncMock()

        # Should not raise exception
        await bus.subscribe(MockEvent, handler)

    @pytest.mark.asyncio
    async def test_subscribe_handles_inner_bus_exception(self):
        """Test that subscribe re-raises exceptions from inner bus."""
        inner_bus = AsyncMock(spec=EventBus)
        inner_bus.subscribe.side_effect = SubscriptionError("Subscription failed")
        bus = LoggingEventBus(inner_bus)
        handler = AsyncMock()

        with pytest.raises(SubscriptionError, match="Subscription failed"):
            await bus.subscribe(MockEvent, handler)

    @pytest.mark.asyncio
    async def test_unsubscribe_calls_inner_bus(self):
        """Test that unsubscribe calls the inner bus."""
        inner_bus = InMemoryEventBus()
        bus = LoggingEventBus(inner_bus)
        handler = AsyncMock()

        # First subscribe
        await bus.subscribe(MockEvent, handler)
        assert inner_bus.get_subscriber_count(MockEvent) == 1

        # Then unsubscribe
        await bus.unsubscribe(MockEvent, handler)
        assert inner_bus.get_subscriber_count(MockEvent) == 0

    @pytest.mark.asyncio
    async def test_unsubscribe_without_inner_bus(self):
        """Test unsubscribe when no inner bus is provided."""
        bus = LoggingEventBus(None)
        handler = AsyncMock()

        # Should not raise exception
        await bus.unsubscribe(MockEvent, handler)

    @pytest.mark.asyncio
    async def test_unsubscribe_handles_inner_bus_exception(self):
        """Test that unsubscribe re-raises exceptions from inner bus."""
        inner_bus = AsyncMock(spec=EventBus)
        inner_bus.unsubscribe.side_effect = SubscriptionError("Unsubscription failed")
        bus = LoggingEventBus(inner_bus)
        handler = AsyncMock()

        with pytest.raises(SubscriptionError, match="Unsubscription failed"):
            await bus.unsubscribe(MockEvent, handler)


class TestLoggingEventBusWithCorrelation:
    """Test LoggingEventBus with correlation context."""

    @pytest.mark.asyncio
    async def test_publish_with_correlation_context(self):
        """Test that publish works with correlation context."""
        inner_bus = InMemoryEventBus()
        bus = LoggingEventBus(inner_bus)
        handler = AsyncMock()

        correlation_id = "test-correlation-123"
        set_correlation_id(correlation_id)

        try:
            # Create event after setting correlation context
            event = MockEvent()

            await inner_bus.subscribe(MockEvent, handler)
            await bus.publish(event)

            # Event should reach handler with correlation context preserved
            handler.assert_called_once_with(event)
            assert event.correlation_id == correlation_id
        finally:
            clear_correlation_id()

    @pytest.mark.asyncio
    async def test_multiple_events_same_correlation(self):
        """Test publishing multiple events with same correlation ID."""
        inner_bus = InMemoryEventBus()
        bus = LoggingEventBus(inner_bus)
        handler = AsyncMock()

        correlation_id = "shared-correlation-123"
        set_correlation_id(correlation_id)

        try:
            await inner_bus.subscribe(MockEvent, handler)

            event1 = MockEvent(message="event 1")
            event2 = MockEvent(message="event 2")

            await bus.publish(event1)
            await bus.publish(event2)

            # Both events should be handled
            assert handler.call_count == 2
            handler.assert_any_call(event1)
            handler.assert_any_call(event2)
        finally:
            clear_correlation_id()


class TestLoggingEventBusEdgeCases:
    """Test edge cases for LoggingEventBus."""

    @pytest.mark.asyncio
    async def test_publish_none_event(self):
        """Test publishing None as event."""
        inner_bus = InMemoryEventBus()
        bus = LoggingEventBus(inner_bus)

        # Should handle gracefully
        await bus.publish(None)

    @pytest.mark.asyncio
    async def test_subscribe_none_handler(self):
        """Test subscribing with None handler."""
        inner_bus = InMemoryEventBus()
        bus = LoggingEventBus(inner_bus)

        # Should handle gracefully
        await bus.subscribe(MockEvent, None)

    @pytest.mark.asyncio
    async def test_full_event_flow_with_logging(self):
        """Test complete event flow through logging decorator."""
        inner_bus = InMemoryEventBus()
        bus = LoggingEventBus(inner_bus)

        # Track events received
        received_events = []

        async def event_handler(event):
            received_events.append(event)

        # Subscribe handler
        await bus.subscribe(MockEvent, event_handler)

        # Publish events
        event1 = MockEvent(message="First event")
        event2 = MockEvent(message="Second event", user_id="user-456")

        await bus.publish(event1)
        await bus.publish(event2)

        # Verify events were received
        assert len(received_events) == 2
        assert received_events[0] == event1
        assert received_events[1] == event2

        # Unsubscribe and verify no more events
        await bus.unsubscribe(MockEvent, event_handler)

        event3 = MockEvent(message="Third event")
        await bus.publish(event3)

        # Should still be only 2 events
        assert len(received_events) == 2
