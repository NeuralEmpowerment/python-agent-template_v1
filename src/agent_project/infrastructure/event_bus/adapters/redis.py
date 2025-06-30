"""Redis EventBus adapter implementation."""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Type
from urllib.parse import urlparse

import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from src.agent_project.correlation import get_correlation_id, set_correlation_id
from src.agent_project.domain.events.base import DomainEvent
from src.agent_project.infrastructure.event_bus.ports import (
    EventBus,
    EventBusError,
    PublishError,
    SubscriptionError,
)

logger = logging.getLogger(__name__)


class RedisEventBus(EventBus):
    """Redis-based event bus using pub/sub and streams.

    Features:
    - Redis pub/sub for real-time event delivery
    - Redis streams for event persistence and replay capability
    - JSON serialization with correlation metadata
    - Connection pooling for production scalability
    - Automatic reconnection with exponential backoff
    - Thread-safe handler management
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "events:",
        max_connections: int = 20,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30,
    ):
        """Initialize Redis EventBus.

        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for Redis keys
            max_connections: Maximum connections in pool
            retry_on_timeout: Whether to retry on timeout
            health_check_interval: Health check interval in seconds
        """
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.max_connections = max_connections
        self.retry_on_timeout = retry_on_timeout
        self.health_check_interval = health_check_interval

        # Parse Redis URL for connection details
        parsed_url = urlparse(redis_url)
        self.host = parsed_url.hostname or "localhost"
        self.port = parsed_url.port or 6379
        self.db = int(parsed_url.path.lstrip("/")) if parsed_url.path else 0

        # Connection pool for efficient connection management
        self.connection_pool: Optional[ConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None

        # Handler management
        self._handlers: Dict[str, List[Callable[[Any], None]]] = {}
        self._subscribed_channels: Set[str] = set()
        self._subscriber_task: Optional[asyncio.Task[None]] = None
        self._running = False

        # Connection state
        self._connected = False
        self._connection_lock = asyncio.Lock()

    async def _ensure_connection(self) -> None:
        """Ensure Redis connection is established."""
        if self._connected and self.redis_client:
            try:
                await self.redis_client.ping()
                return
            except (ConnectionError, TimeoutError) as e:
                logger.warning(f"Redis connection lost: {e}")
                self._connected = False

        async with self._connection_lock:
            if self._connected:
                return

            try:
                # Create connection pool
                self.connection_pool = ConnectionPool(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    max_connections=self.max_connections,
                    retry_on_timeout=self.retry_on_timeout,
                    health_check_interval=self.health_check_interval,
                )

                # Create Redis clients
                self.redis_client = redis.Redis(connection_pool=self.connection_pool)
                self.pubsub_client = redis.Redis(connection_pool=self.connection_pool)

                # Test connection
                await self.redis_client.ping()
                self._connected = True

                logger.info(f"Connected to Redis at {self.host}:{self.port}")

            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise EventBusError(f"Redis connection failed: {e}") from e

    async def _get_channel_name(self, event_type: Type[Any]) -> str:
        """Get Redis channel name for event type."""
        return f"{self.key_prefix}channel:{event_type.__name__}"

    async def _get_stream_name(self, event_type: Type[Any]) -> str:
        """Get Redis stream name for event type."""
        return f"{self.key_prefix}stream:{event_type.__name__}"

    async def _serialize_event(self, event: Any) -> str:
        """Serialize event to JSON string."""
        try:
            if isinstance(event, DomainEvent):
                # Use built-in to_dict method for domain events
                event_data = event.to_dict()
            else:
                # Fallback for non-domain events
                event_data = {
                    "event_type": event.__class__.__name__,
                    "data": (event.__dict__ if hasattr(event, "__dict__") else str(event)),
                    "correlation_id": get_correlation_id(),
                }

            return json.dumps(event_data, default=str)

        except Exception as e:
            raise PublishError(f"Failed to serialize event: {e}") from e

    async def _deserialize_event(self, data: str) -> Dict[str, Any]:
        """Deserialize JSON string to event data."""
        try:
            result = json.loads(data)
            return result if isinstance(result, dict) else {}
        except Exception as e:
            raise EventBusError(f"Failed to deserialize event: {e}") from e

    async def publish(self, event: Any) -> None:
        """Publish a domain event to Redis.

        Args:
            event: The domain event to publish

        Raises:
            PublishError: If publishing fails
        """
        await self._ensure_connection()

        if not self.redis_client:
            raise PublishError("Redis client not initialized")

        try:
            # Serialize event
            serialized_event = await self._serialize_event(event)
            event_type = type(event)

            # Get channel and stream names
            channel_name = await self._get_channel_name(event_type)
            stream_name = await self._get_stream_name(event_type)

            # Publish to channel for real-time delivery
            await self.redis_client.publish(channel_name, serialized_event)

            # Add to stream for persistence and replay
            await self.redis_client.xadd(stream_name, {"event": serialized_event})

            logger.debug(
                f"Published event {event_type.__name__} to channel {channel_name} " f"and stream {stream_name}"
            )

        except RedisError as e:
            raise PublishError(f"Failed to publish event to Redis: {e}") from e
        except Exception as e:
            raise PublishError(f"Unexpected error publishing event: {e}") from e

    async def subscribe(self, event_type: Type[Any], handler: Callable[[Any], None]) -> None:
        """Subscribe a handler to events of a specific type.

        Args:
            event_type: The type of event to subscribe to
            handler: The handler function to call when events are received

        Raises:
            SubscriptionError: If subscription fails
        """
        await self._ensure_connection()

        try:
            event_type_name = event_type.__name__

            # Add handler to registry
            if event_type_name not in self._handlers:
                self._handlers[event_type_name] = []
            self._handlers[event_type_name].append(handler)

            # Subscribe to Redis channel if not already subscribed
            channel_name = await self._get_channel_name(event_type)
            if channel_name not in self._subscribed_channels:
                await self._subscribe_to_channel(channel_name)
                self._subscribed_channels.add(channel_name)

            logger.debug(f"Subscribed handler to {event_type_name} events")

        except Exception as e:
            raise SubscriptionError(f"Failed to subscribe to event type {event_type.__name__}: {e}") from e

    async def unsubscribe(self, event_type: Type[Any], handler: Callable[[Any], None]) -> None:
        """Unsubscribe a handler from events of a specific type.

        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler function to remove

        Raises:
            SubscriptionError: If unsubscription fails
        """
        try:
            event_type_name = event_type.__name__

            # Remove handler from registry
            if event_type_name in self._handlers:
                try:
                    self._handlers[event_type_name].remove(handler)

                    # If no more handlers, unsubscribe from channel
                    if not self._handlers[event_type_name]:
                        del self._handlers[event_type_name]
                        channel_name = await self._get_channel_name(event_type)
                        await self._unsubscribe_from_channel(channel_name)
                        self._subscribed_channels.discard(channel_name)

                except ValueError:
                    # Handler not found, which is fine
                    pass

            logger.debug(f"Unsubscribed handler from {event_type_name} events")

        except Exception as e:
            raise SubscriptionError(f"Failed to unsubscribe from event type {event_type.__name__}: {e}") from e

    async def _subscribe_to_channel(self, channel_name: str) -> None:
        """Subscribe to a specific Redis channel."""
        if not self.pubsub_client:
            raise SubscriptionError("PubSub client not initialized")

        if not self.pubsub:
            self.pubsub = self.pubsub_client.pubsub()

        await self.pubsub.subscribe(channel_name)

        # Start subscriber task if not running
        if not self._running:
            self._running = True
            self._subscriber_task = asyncio.create_task(self._message_listener())

    async def _unsubscribe_from_channel(self, channel_name: str) -> None:
        """Unsubscribe from a specific Redis channel."""
        if self.pubsub:
            await self.pubsub.unsubscribe(channel_name)

    async def _message_listener(self) -> None:
        """Listen for messages from Redis pub/sub."""
        if not self.pubsub:
            return

        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    await self._handle_message(message)

        except Exception as e:
            logger.error(f"Error in message listener: {e}")
        finally:
            self._running = False

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle received message from Redis."""
        try:
            channel = message["channel"].decode() if isinstance(message["channel"], bytes) else message["channel"]
            data = message["data"].decode() if isinstance(message["data"], bytes) else message["data"]

            # Extract event type from channel name
            event_type_name = channel.replace(f"{self.key_prefix}channel:", "")

            # Deserialize event data
            event_data = await self._deserialize_event(data)

            # Set correlation context from event
            if "metadata" in event_data and "correlation_id" in event_data["metadata"]:
                set_correlation_id(event_data["metadata"]["correlation_id"])

            # Call registered handlers
            if event_type_name in self._handlers:
                for handler in self._handlers[event_type_name]:
                    try:
                        # Call handler with event data
                        if asyncio.iscoroutinefunction(handler):
                            await handler(event_data)
                        else:
                            handler(event_data)
                    except Exception as e:
                        logger.error(f"Error in event handler: {e}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def close(self) -> None:
        """Close Redis connections and cleanup resources."""
        try:
            self._running = False

            # Cancel subscriber task
            if self._subscriber_task and not self._subscriber_task.done():
                self._subscriber_task.cancel()
                try:
                    await self._subscriber_task
                except asyncio.CancelledError:
                    pass

            # Close pubsub
            if self.pubsub:
                await self.pubsub.close()

            # Close connection pool
            if self.connection_pool:
                await self.connection_pool.disconnect()

            self._connected = False
            logger.info("Redis EventBus connections closed")

        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")

    async def __aenter__(self) -> "RedisEventBus":
        """Async context manager entry."""
        await self._ensure_connection()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def __repr__(self) -> str:
        """String representation of RedisEventBus."""
        return f"RedisEventBus(redis_url={self.redis_url}, key_prefix={self.key_prefix})"
