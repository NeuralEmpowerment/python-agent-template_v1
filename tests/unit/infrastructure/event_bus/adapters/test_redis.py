"""Unit tests for Redis EventBus adapter."""

import json
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent_project.correlation import clear_correlation_id, set_correlation_id
from src.agent_project.domain.events.base import DomainEvent
from src.agent_project.infrastructure.event_bus.adapters.redis import RedisEventBus
from src.agent_project.infrastructure.event_bus.ports import EventBusError, PublishError, SubscriptionError


@dataclass(frozen=True)
class TestEvent(DomainEvent):
    """Test event for Redis testing."""

    message: str = "default"


class TestRedisEventBus:
    """Test suite for RedisEventBus."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment."""
        clear_correlation_id()
        self.redis_url = "redis://localhost:6379/0"
        self.key_prefix = "test_events:"

    @pytest.fixture
    def event_bus(self):
        """Create Redis event bus instance."""
        return RedisEventBus(
            redis_url=self.redis_url,
            key_prefix=self.key_prefix,
            max_connections=5,
        )

    @pytest.fixture
    def test_event(self):
        """Create test event."""
        set_correlation_id("test-correlation-123")
        return TestEvent(message="Hello Redis!")

    def test_init(self, event_bus):
        """Test RedisEventBus initialization."""
        assert event_bus.redis_url == self.redis_url
        assert event_bus.key_prefix == self.key_prefix
        assert event_bus.max_connections == 5
        assert event_bus.host == "localhost"
        assert event_bus.port == 6379
        assert event_bus.db == 0
        assert not event_bus._connected
        assert event_bus._handlers == {}

    def test_init_with_custom_url(self):
        """Test initialization with custom Redis URL."""
        custom_url = "redis://redis-server:6380/1"
        event_bus = RedisEventBus(redis_url=custom_url)

        assert event_bus.host == "redis-server"
        assert event_bus.port == 6380
        assert event_bus.db == 1

    async def test_get_channel_name(self, event_bus):
        """Test channel name generation."""
        channel_name = await event_bus._get_channel_name(TestEvent)
        assert channel_name == f"{self.key_prefix}channel:TestEvent"

    async def test_get_stream_name(self, event_bus):
        """Test stream name generation."""
        stream_name = await event_bus._get_stream_name(TestEvent)
        assert stream_name == f"{self.key_prefix}stream:TestEvent"

    async def test_serialize_domain_event(self, event_bus, test_event):
        """Test serialization of domain events."""
        serialized = await event_bus._serialize_event(test_event)
        data = json.loads(serialized)

        assert data["event_type"] == "TestEvent"
        assert data["metadata"]["correlation_id"] == "test-correlation-123"
        assert data["data"]["message"] == "Hello Redis!"

    async def test_serialize_non_domain_event(self, event_bus):
        """Test serialization of non-domain events."""

        class SimpleEvent:
            def __init__(self, value):
                self.value = value

        event = SimpleEvent("test")
        serialized = await event_bus._serialize_event(event)
        data = json.loads(serialized)

        assert data["event_type"] == "SimpleEvent"
        assert data["data"]["value"] == "test"
        assert "correlation_id" in data

    async def test_serialize_error(self, event_bus):
        """Test serialization error handling."""

        # Create an object that can't be serialized
        class UnserializableEvent:
            def __init__(self):
                self.circular_ref = self

        event = UnserializableEvent()

        with pytest.raises(PublishError, match="Failed to serialize event"):
            await event_bus._serialize_event(event)

    async def test_deserialize_event(self, event_bus):
        """Test event deserialization."""
        event_data = {
            "event_type": "TestEvent",
            "metadata": {"correlation_id": "test-123"},
            "data": {"message": "Hello"},
        }
        serialized = json.dumps(event_data)

        result = await event_bus._deserialize_event(serialized)
        assert result == event_data

    async def test_deserialize_error(self, event_bus):
        """Test deserialization error handling."""
        invalid_json = "{"  # Invalid JSON

        with pytest.raises(EventBusError, match="Failed to deserialize event"):
            await event_bus._deserialize_event(invalid_json)

    @patch("src.infrastructure.event_bus.adapters.redis.redis.Redis")
    @patch("src.infrastructure.event_bus.adapters.redis.ConnectionPool")
    async def test_ensure_connection_success(self, mock_pool, mock_redis, event_bus):
        """Test successful connection establishment."""
        # Mock connection pool and Redis client
        mock_pool_instance = AsyncMock()
        mock_pool.return_value = mock_pool_instance

        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis.return_value = mock_redis_instance

        # Test connection
        await event_bus._ensure_connection()

        assert event_bus._connected
        assert event_bus.redis_client is not None
        assert event_bus.pubsub_client is not None
        mock_redis_instance.ping.assert_called_once()

    @patch("src.infrastructure.event_bus.adapters.redis.redis.Redis")
    @patch("src.infrastructure.event_bus.adapters.redis.ConnectionPool")
    async def test_ensure_connection_failure(self, mock_pool, mock_redis, event_bus):
        """Test connection failure handling."""
        # Mock connection failure
        mock_redis.side_effect = Exception("Connection failed")

        with pytest.raises(EventBusError, match="Redis connection failed"):
            await event_bus._ensure_connection()

        assert not event_bus._connected

    @patch("src.infrastructure.event_bus.adapters.redis.redis.Redis")
    @patch("src.infrastructure.event_bus.adapters.redis.ConnectionPool")
    async def test_publish_success(self, mock_pool, mock_redis, event_bus, test_event):
        """Test successful event publishing."""
        # Mock Redis client
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.publish = AsyncMock()
        mock_redis_instance.xadd = AsyncMock()
        mock_redis.return_value = mock_redis_instance

        # Mock connection pool
        mock_pool_instance = AsyncMock()
        mock_pool.return_value = mock_pool_instance

        # Test publish
        await event_bus.publish(test_event)

        # Verify Redis operations
        mock_redis_instance.publish.assert_called_once()
        mock_redis_instance.xadd.assert_called_once()

        # Check published data
        publish_call = mock_redis_instance.publish.call_args
        channel_name = publish_call[0][0]
        message_data = publish_call[0][1]

        assert channel_name == f"{self.key_prefix}channel:TestEvent"
        data = json.loads(message_data)
        assert data["event_type"] == "TestEvent"
        assert data["data"]["message"] == "Hello Redis!"

    @patch("src.infrastructure.event_bus.adapters.redis.redis.Redis")
    async def test_publish_without_connection(self, mock_redis, event_bus, test_event):
        """Test publish without established connection."""
        # Don't establish connection
        event_bus.redis_client = None

        with pytest.raises(PublishError, match="Redis client not initialized"):
            await event_bus.publish(test_event)

    @patch("src.infrastructure.event_bus.adapters.redis.redis.Redis")
    @patch("src.infrastructure.event_bus.adapters.redis.ConnectionPool")
    async def test_publish_redis_error(self, mock_pool, mock_redis, event_bus, test_event):
        """Test publish with Redis error."""
        # Mock Redis client with error
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_instance.publish = AsyncMock(side_effect=Exception("Redis error"))
        mock_redis.return_value = mock_redis_instance

        mock_pool_instance = AsyncMock()
        mock_pool.return_value = mock_pool_instance

        with pytest.raises(PublishError, match="Unexpected error publishing event"):
            await event_bus.publish(test_event)

    @patch("src.infrastructure.event_bus.adapters.redis.redis.Redis")
    @patch("src.infrastructure.event_bus.adapters.redis.ConnectionPool")
    async def test_subscribe_success(self, mock_pool, mock_redis, event_bus):
        """Test successful event subscription."""
        # Mock Redis client
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_redis_instance.pubsub = MagicMock(return_value=mock_pubsub)
        mock_pubsub.subscribe = AsyncMock()
        mock_redis.return_value = mock_redis_instance

        mock_pool_instance = AsyncMock()
        mock_pool.return_value = mock_pool_instance

        # Mock handler
        handler = AsyncMock()

        # Test subscribe
        await event_bus.subscribe(TestEvent, handler)

        # Verify subscription
        assert "TestEvent" in event_bus._handlers
        assert handler in event_bus._handlers["TestEvent"]
        mock_pubsub.subscribe.assert_called_once()

    async def test_subscribe_multiple_handlers(self, event_bus):
        """Test subscribing multiple handlers to same event type."""
        with patch.object(event_bus, "_ensure_connection", new_callable=AsyncMock), patch.object(
            event_bus, "_subscribe_to_channel", new_callable=AsyncMock
        ):
            handler1 = AsyncMock()
            handler2 = AsyncMock()

            await event_bus.subscribe(TestEvent, handler1)
            await event_bus.subscribe(TestEvent, handler2)

            assert len(event_bus._handlers["TestEvent"]) == 2
            assert handler1 in event_bus._handlers["TestEvent"]
            assert handler2 in event_bus._handlers["TestEvent"]

    async def test_subscribe_error(self, event_bus):
        """Test subscription error handling."""
        with patch.object(event_bus, "_ensure_connection", side_effect=Exception("Connection error")):
            handler = AsyncMock()

            with pytest.raises(SubscriptionError, match="Failed to subscribe to event type TestEvent"):
                await event_bus.subscribe(TestEvent, handler)

    async def test_unsubscribe_success(self, event_bus):
        """Test successful event unsubscription."""
        with patch.object(event_bus, "_ensure_connection", new_callable=AsyncMock), patch.object(
            event_bus, "_subscribe_to_channel", new_callable=AsyncMock
        ), patch.object(event_bus, "_unsubscribe_from_channel", new_callable=AsyncMock) as mock_unsub:
            handler = AsyncMock()

            # First subscribe
            await event_bus.subscribe(TestEvent, handler)
            assert handler in event_bus._handlers["TestEvent"]

            # Then unsubscribe
            await event_bus.unsubscribe(TestEvent, handler)

            # Verify handler removed and channel unsubscribed
            assert "TestEvent" not in event_bus._handlers
            mock_unsub.assert_called_once()

    async def test_unsubscribe_nonexistent_handler(self, event_bus):
        """Test unsubscribing non-existent handler."""
        handler = AsyncMock()

        # Should not raise error
        await event_bus.unsubscribe(TestEvent, handler)

    async def test_unsubscribe_partial(self, event_bus):
        """Test unsubscribing one of multiple handlers."""
        with patch.object(event_bus, "_ensure_connection", new_callable=AsyncMock), patch.object(
            event_bus, "_subscribe_to_channel", new_callable=AsyncMock
        ), patch.object(event_bus, "_unsubscribe_from_channel", new_callable=AsyncMock) as mock_unsub:
            handler1 = AsyncMock()
            handler2 = AsyncMock()

            # Subscribe both handlers
            await event_bus.subscribe(TestEvent, handler1)
            await event_bus.subscribe(TestEvent, handler2)

            # Unsubscribe one handler
            await event_bus.unsubscribe(TestEvent, handler1)

            # Verify one handler remains, no channel unsubscription
            assert len(event_bus._handlers["TestEvent"]) == 1
            assert handler2 in event_bus._handlers["TestEvent"]
            mock_unsub.assert_not_called()

    async def test_handle_message_success(self, event_bus):
        """Test successful message handling."""
        # Set up handler
        handler = AsyncMock()
        event_bus._handlers["TestEvent"] = [handler]

        # Mock message
        event_data = {
            "event_type": "TestEvent",
            "metadata": {"correlation_id": "test-123"},
            "data": {"message": "Hello"},
        }
        message = {"channel": f"{self.key_prefix}channel:TestEvent".encode(), "data": json.dumps(event_data).encode()}

        # Test message handling
        await event_bus._handle_message(message)

        # Verify handler called
        handler.assert_called_once_with(event_data)

    async def test_handle_message_with_correlation(self, event_bus):
        """Test message handling with correlation ID setting."""
        handler = AsyncMock()
        event_bus._handlers["TestEvent"] = [handler]

        event_data = {
            "event_type": "TestEvent",
            "metadata": {"correlation_id": "test-correlation-456"},
            "data": {"message": "Hello"},
        }
        message = {"channel": f"{self.key_prefix}channel:TestEvent".encode(), "data": json.dumps(event_data).encode()}

        # Clear existing correlation
        clear_correlation_id()

        # Handle message
        await event_bus._handle_message(message)

        # Verify correlation ID was set
        from src.agent_project.correlation import get_correlation_id

        assert get_correlation_id() == "test-correlation-456"

    async def test_handle_message_handler_error(self, event_bus):
        """Test message handling with handler error."""
        # Handler that raises an error
        handler = AsyncMock(side_effect=Exception("Handler error"))
        event_bus._handlers["TestEvent"] = [handler]

        event_data = {"event_type": "TestEvent", "metadata": {}, "data": {}}
        message = {"channel": f"{self.key_prefix}channel:TestEvent".encode(), "data": json.dumps(event_data).encode()}

        # Should not raise error, just log it
        await event_bus._handle_message(message)

    async def test_close(self, event_bus):
        """Test resource cleanup on close."""
        # Set up some state
        event_bus._running = True
        event_bus._subscriber_task = AsyncMock()
        event_bus.pubsub = AsyncMock()
        event_bus.connection_pool = AsyncMock()
        event_bus._connected = True

        await event_bus.close()

        assert not event_bus._running
        assert not event_bus._connected
        event_bus._subscriber_task.cancel.assert_called_once()
        event_bus.pubsub.close.assert_called_once()
        event_bus.connection_pool.disconnect.assert_called_once()

    async def test_async_context_manager(self, event_bus):
        """Test async context manager usage."""
        with patch.object(event_bus, "_ensure_connection", new_callable=AsyncMock) as mock_connect, patch.object(
            event_bus, "close", new_callable=AsyncMock
        ) as mock_close:
            async with event_bus as bus:
                assert bus is event_bus
                mock_connect.assert_called_once()

            mock_close.assert_called_once()

    def test_repr(self, event_bus):
        """Test string representation."""
        repr_str = repr(event_bus)
        assert "RedisEventBus" in repr_str
        assert self.redis_url in repr_str
        assert self.key_prefix in repr_str
