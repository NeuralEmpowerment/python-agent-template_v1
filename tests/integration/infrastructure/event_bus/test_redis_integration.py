"""Integration tests for Redis EventBus with real Redis instance."""

import asyncio
import json
from dataclasses import dataclass

import pytest
from testcontainers.redis import RedisContainer

from src.agent_project.correlation import clear_correlation_id, set_correlation_id
from src.agent_project.domain.events.base import DomainEvent
from src.agent_project.infrastructure.event_bus.adapters.redis import RedisEventBus


@dataclass(frozen=True)
class TaskProcessedEvent(DomainEvent):
    """Test event for task processing."""

    task_id: str = "default"
    status: str = "pending"


@dataclass(frozen=True)
class ConversationCompletedEvent(DomainEvent):
    """Test event for conversation completion."""

    conversation_id: str = "default"
    response: str = "default"
    confidence: float = 0.0


@pytest.fixture(scope="session")
def redis_container():
    """Start Redis container for integration tests."""
    with RedisContainer("redis:7-alpine") as container:
        yield container


@pytest.fixture
def redis_url(redis_container):
    """Get Redis URL from container."""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    return f"redis://{host}:{port}"


@pytest.fixture
async def event_bus(redis_url):
    """Create Redis EventBus for testing."""
    bus = RedisEventBus(
        redis_url=redis_url,
        key_prefix="integration_test:",
        max_connections=5,
    )

    yield bus

    # Cleanup
    await bus.close()


class TestRedisEventBusIntegration:
    """Integration tests for Redis EventBus."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment."""
        clear_correlation_id()

    async def test_publish_and_receive_single_event(self, event_bus):
        """Test publishing and receiving a single event."""
        set_correlation_id("integration-test-123")

        # Create test event
        event = TaskProcessedEvent(task_id="task-123", status="completed")

        # Set up handler to capture received events
        received_events = []

        async def handler(event_data):
            received_events.append(event_data)

        # Subscribe to events
        await event_bus.subscribe(TaskProcessedEvent, handler)

        # Give subscription time to establish
        await asyncio.sleep(0.1)

        # Publish event
        await event_bus.publish(event)

        # Wait for event to be received
        await asyncio.sleep(0.2)

        # Verify event was received
        assert len(received_events) == 1

        received_event = received_events[0]
        assert received_event["event_type"] == "TaskProcessedEvent"
        assert received_event["data"]["task_id"] == "task-123"
        assert received_event["data"]["status"] == "completed"
        assert received_event["metadata"]["correlation_id"] == "integration-test-123"

    async def test_publish_multiple_events(self, event_bus):
        """Test publishing multiple events of same type."""
        received_events = []

        async def handler(event_data):
            received_events.append(event_data)

        await event_bus.subscribe(TaskProcessedEvent, handler)
        await asyncio.sleep(0.1)

        # Publish multiple events
        events = [TaskProcessedEvent(task_id=f"task-{i}", status="completed") for i in range(3)]

        for event in events:
            await event_bus.publish(event)

        # Wait for all events to be received
        await asyncio.sleep(0.3)

        # Verify all events received
        assert len(received_events) == 3

        for i, received_event in enumerate(received_events):
            assert received_event["data"]["task_id"] == f"task-{i}"
            assert received_event["data"]["status"] == "completed"

    async def test_multiple_event_types(self, event_bus):
        """Test handling multiple event types."""
        audio_events = []
        transcription_events = []

        async def audio_handler(event_data):
            audio_events.append(event_data)

        async def transcription_handler(event_data):
            transcription_events.append(event_data)

        # Subscribe to different event types
        await event_bus.subscribe(TaskProcessedEvent, audio_handler)
        await event_bus.subscribe(ConversationCompletedEvent, transcription_handler)
        await asyncio.sleep(0.1)

        # Publish events of different types
        audio_event = TaskProcessedEvent(task_id="task-456", status="processing")
        transcription_event = ConversationCompletedEvent(
            conversation_id="conv-789", response="Hello world", confidence=0.95
        )

        await event_bus.publish(audio_event)
        await event_bus.publish(transcription_event)

        await asyncio.sleep(0.3)

        # Verify events received by correct handlers
        assert len(audio_events) == 1
        assert len(transcription_events) == 1

        assert audio_events[0]["event_type"] == "TaskProcessedEvent"
        assert audio_events[0]["data"]["task_id"] == "task-456"

        assert transcription_events[0]["event_type"] == "ConversationCompletedEvent"
        assert transcription_events[0]["data"]["conversation_id"] == "conv-789"
        assert transcription_events[0]["data"]["text"] == "Hello world"

    async def test_multiple_handlers_same_event(self, event_bus):
        """Test multiple handlers for the same event type."""
        handler1_events = []
        handler2_events = []

        async def handler1(event_data):
            handler1_events.append(event_data)

        async def handler2(event_data):
            handler2_events.append(event_data)

        # Subscribe both handlers to same event type
        await event_bus.subscribe(TaskProcessedEvent, handler1)
        await event_bus.subscribe(TaskProcessedEvent, handler2)
        await asyncio.sleep(0.1)

        # Publish event
        event = TaskProcessedEvent(task_id="task-multi", status="completed")
        await event_bus.publish(event)

        await asyncio.sleep(0.2)

        # Verify both handlers received the event
        assert len(handler1_events) == 1
        assert len(handler2_events) == 1

        assert handler1_events[0]["data"]["task_id"] == "task-multi"
        assert handler2_events[0]["data"]["task_id"] == "task-multi"

    async def test_unsubscribe_handler(self, event_bus):
        """Test unsubscribing a handler."""
        received_events = []

        async def handler(event_data):
            received_events.append(event_data)

        # Subscribe and publish first event
        await event_bus.subscribe(TaskProcessedEvent, handler)
        await asyncio.sleep(0.1)

        event1 = TaskProcessedEvent(task_id="task-before", status="completed")
        await event_bus.publish(event1)
        await asyncio.sleep(0.2)

        assert len(received_events) == 1

        # Unsubscribe handler
        await event_bus.unsubscribe(TaskProcessedEvent, handler)
        await asyncio.sleep(0.1)

        # Publish second event (should not be received)
        event2 = TaskProcessedEvent(task_id="task-after", status="completed")
        await event_bus.publish(event2)
        await asyncio.sleep(0.2)

        # Verify only first event was received
        assert len(received_events) == 1
        assert received_events[0]["data"]["task_id"] == "task-before"

    async def test_correlation_id_propagation(self, event_bus):
        """Test correlation ID propagation through Redis."""
        received_correlation_ids = []

        async def handler(event_data):
            # Capture the correlation ID from the context
            from src.agent_project.correlation import get_correlation_id

            received_correlation_ids.append(get_correlation_id())

        await event_bus.subscribe(TaskProcessedEvent, handler)
        await asyncio.sleep(0.1)

        # Set specific correlation ID and publish event
        set_correlation_id("test-correlation-999")
        event = TaskProcessedEvent(task_id="task-corr", status="completed")
        await event_bus.publish(event)

        await asyncio.sleep(0.2)

        # Verify correlation ID was propagated
        assert len(received_correlation_ids) == 1
        assert received_correlation_ids[0] == "test-correlation-999"

    async def test_connection_resilience(self, event_bus):
        """Test event bus resilience to connection issues."""
        received_events = []

        async def handler(event_data):
            received_events.append(event_data)

        await event_bus.subscribe(TaskProcessedEvent, handler)
        await asyncio.sleep(0.1)

        # Publish event before any connection issues
        event1 = TaskProcessedEvent(task_id="task-resilient-1", status="completed")
        await event_bus.publish(event1)
        await asyncio.sleep(0.2)

        # Force reconnection by marking as disconnected
        event_bus._connected = False

        # Publish another event (should trigger reconnection)
        event2 = TaskProcessedEvent(task_id="task-resilient-2", status="completed")
        await event_bus.publish(event2)
        await asyncio.sleep(0.2)

        # Both events should be received
        assert len(received_events) == 2
        assert received_events[0]["data"]["task_id"] == "task-resilient-1"
        assert received_events[1]["data"]["task_id"] == "task-resilient-2"

    async def test_event_persistence_in_streams(self, event_bus):
        """Test that events are persisted in Redis streams."""
        # Publish an event
        event = TaskProcessedEvent(task_id="task-stream", status="completed")
        await event_bus.publish(event)

        # Verify event exists in Redis stream
        stream_name = await event_bus._get_stream_name(TaskProcessedEvent)

        # Read from stream directly using Redis client
        await event_bus._ensure_connection()
        stream_data = await event_bus.redis_client.xread({stream_name: "0-0"})

        assert len(stream_data) == 1
        assert stream_name.encode() in stream_data[0]

        # Verify event data in stream
        stream_entries = stream_data[0][1]
        assert len(stream_entries) == 1

        event_entry = stream_entries[0][1]
        event_json = event_entry[b"event"].decode()
        event_data = json.loads(event_json)

        assert event_data["event_type"] == "TaskProcessedEvent"
        assert event_data["data"]["task_id"] == "task-stream"

    async def test_async_context_manager(self, redis_url):
        """Test using Redis EventBus as async context manager."""
        received_events = []

        async def handler(event_data):
            received_events.append(event_data)

        # Use as context manager
        async with RedisEventBus(redis_url=redis_url, key_prefix="context_test:") as bus:
            await bus.subscribe(TaskProcessedEvent, handler)
            await asyncio.sleep(0.1)

            event = TaskProcessedEvent(task_id="task-context", status="completed")
            await bus.publish(event)
            await asyncio.sleep(0.2)

        # Event should be received
        assert len(received_events) == 1
        assert received_events[0]["data"]["task_id"] == "task-context"

    async def test_concurrent_publishing(self, event_bus):
        """Test concurrent event publishing."""
        received_events = []

        async def handler(event_data):
            received_events.append(event_data)

        await event_bus.subscribe(TaskProcessedEvent, handler)
        await asyncio.sleep(0.1)

        # Publish events concurrently
        async def publish_event(task_id: str):
            event = TaskProcessedEvent(task_id=task_id, status="completed")
            await event_bus.publish(event)

        # Create concurrent tasks
        tasks = [publish_event(f"task-concurrent-{i}") for i in range(5)]

        await asyncio.gather(*tasks)
        await asyncio.sleep(0.3)

        # All events should be received
        assert len(received_events) == 5

        # Verify all file IDs are present
        received_task_ids = {event["data"]["task_id"] for event in received_events}
        expected_task_ids = {f"task-concurrent-{i}" for i in range(5)}
        assert received_task_ids == expected_task_ids

    async def test_error_handling_in_handlers(self, event_bus):
        """Test error handling when handlers raise exceptions."""
        received_events = []
        error_count = 0

        async def good_handler(event_data):
            received_events.append(event_data)

        async def bad_handler(event_data):
            nonlocal error_count
            error_count += 1
            raise Exception("Handler error")

        # Subscribe both handlers
        await event_bus.subscribe(TaskProcessedEvent, good_handler)
        await event_bus.subscribe(TaskProcessedEvent, bad_handler)
        await asyncio.sleep(0.1)

        # Publish event
        event = TaskProcessedEvent(task_id="task-error", status="completed")
        await event_bus.publish(event)
        await asyncio.sleep(0.2)

        # Good handler should still receive event despite bad handler error
        assert len(received_events) == 1
        assert error_count == 1
        assert received_events[0]["data"]["task_id"] == "task-error"
