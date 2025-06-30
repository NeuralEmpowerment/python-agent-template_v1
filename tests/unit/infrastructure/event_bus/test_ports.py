"""Unit tests for event bus port interface."""

from abc import ABC
from unittest.mock import AsyncMock

import pytest

from src.agent_project.infrastructure.event_bus.ports import (
    EventBus,
    EventBusError,
    PublishError,
    SubscriptionError,
)


class ConcreteEventBus(EventBus):
    """Concrete implementation for testing abstract interface."""

    def __init__(self):
        self.published_events = []
        self.subscriptions = {}
        self.should_fail_publish = False
        self.should_fail_subscribe = False

    async def publish(self, event):
        if self.should_fail_publish:
            raise PublishError("Simulated publish failure")
        self.published_events.append(event)

    async def subscribe(self, event_type, handler):
        if self.should_fail_subscribe:
            raise SubscriptionError("Simulated subscription failure")
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append(handler)

    async def unsubscribe(self, event_type, handler):
        if event_type in self.subscriptions:
            if handler in self.subscriptions[event_type]:
                self.subscriptions[event_type].remove(handler)


class MockEvent:
    """Mock event for testing."""

    def __init__(self, data: str):
        self.data = data

    def __eq__(self, other):
        return isinstance(other, MockEvent) and self.data == other.data


class TestEventBusInterface:
    """Test cases for EventBus abstract interface."""

    def test_eventbus_is_abstract(self):
        """Test that EventBus cannot be instantiated directly."""
        with pytest.raises(TypeError):
            EventBus()

    def test_eventbus_is_abc(self):
        """Test that EventBus inherits from ABC."""
        assert issubclass(EventBus, ABC)

    def test_concrete_implementation_works(self):
        """Test that concrete implementation can be instantiated."""
        bus = ConcreteEventBus()
        assert isinstance(bus, EventBus)

    @pytest.mark.asyncio
    async def test_publish_method_signature(self):
        """Test that publish method has correct signature."""
        bus = ConcreteEventBus()
        event = MockEvent("test data")

        # Should not raise any exceptions
        await bus.publish(event)

        assert len(bus.published_events) == 1
        assert bus.published_events[0] == event

    @pytest.mark.asyncio
    async def test_subscribe_method_signature(self):
        """Test that subscribe method has correct signature."""
        bus = ConcreteEventBus()
        handler = AsyncMock()

        # Should not raise any exceptions
        await bus.subscribe(MockEvent, handler)

        assert MockEvent in bus.subscriptions
        assert handler in bus.subscriptions[MockEvent]

    @pytest.mark.asyncio
    async def test_unsubscribe_method_signature(self):
        """Test that unsubscribe method has correct signature."""
        bus = ConcreteEventBus()
        handler = AsyncMock()

        # Subscribe first
        await bus.subscribe(MockEvent, handler)
        assert handler in bus.subscriptions[MockEvent]

        # Then unsubscribe
        await bus.unsubscribe(MockEvent, handler)
        assert handler not in bus.subscriptions[MockEvent]


class TestEventBusExceptions:
    """Test cases for event bus exception classes."""

    def test_eventbus_error_hierarchy(self):
        """Test exception hierarchy."""
        assert issubclass(EventBusError, Exception)
        assert issubclass(PublishError, EventBusError)
        assert issubclass(SubscriptionError, EventBusError)

    def test_eventbus_error_instantiation(self):
        """Test that exceptions can be instantiated with messages."""
        error = EventBusError("Test error")
        assert str(error) == "Test error"

        publish_error = PublishError("Publish failed")
        assert str(publish_error) == "Publish failed"

        subscription_error = SubscriptionError("Subscription failed")
        assert str(subscription_error) == "Subscription failed"

    @pytest.mark.asyncio
    async def test_publish_error_propagation(self):
        """Test that PublishError is properly raised."""
        bus = ConcreteEventBus()
        bus.should_fail_publish = True
        event = MockEvent("test")

        with pytest.raises(PublishError) as exc_info:
            await bus.publish(event)

        assert "Simulated publish failure" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_subscription_error_propagation(self):
        """Test that SubscriptionError is properly raised."""
        bus = ConcreteEventBus()
        bus.should_fail_subscribe = True
        handler = AsyncMock()

        with pytest.raises(SubscriptionError) as exc_info:
            await bus.subscribe(MockEvent, handler)

        assert "Simulated subscription failure" in str(exc_info.value)


class TestEventBusBehavior:
    """Test cases for expected event bus behavior."""

    @pytest.mark.asyncio
    async def test_multiple_events_published(self):
        """Test publishing multiple events."""
        bus = ConcreteEventBus()
        events = [MockEvent("event 1"), MockEvent("event 2"), MockEvent("event 3")]

        for event in events:
            await bus.publish(event)

        assert len(bus.published_events) == 3
        assert bus.published_events == events

    @pytest.mark.asyncio
    async def test_multiple_handlers_subscription(self):
        """Test subscribing multiple handlers to same event type."""
        bus = ConcreteEventBus()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        await bus.subscribe(MockEvent, handler1)
        await bus.subscribe(MockEvent, handler2)

        assert len(bus.subscriptions[MockEvent]) == 2
        assert handler1 in bus.subscriptions[MockEvent]
        assert handler2 in bus.subscriptions[MockEvent]

    @pytest.mark.asyncio
    async def test_different_event_types_subscription(self):
        """Test subscribing to different event types."""
        bus = ConcreteEventBus()
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        class AnotherEvent:
            pass

        await bus.subscribe(MockEvent, handler1)
        await bus.subscribe(AnotherEvent, handler2)

        assert MockEvent in bus.subscriptions
        assert AnotherEvent in bus.subscriptions
        assert len(bus.subscriptions) == 2

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_handler(self):
        """Test unsubscribing handler that was never subscribed."""
        bus = ConcreteEventBus()
        handler = AsyncMock()

        # Should not raise any exceptions
        await bus.unsubscribe(MockEvent, handler)

        # Subscriptions should remain empty
        assert not bus.subscriptions.get(MockEvent, [])
