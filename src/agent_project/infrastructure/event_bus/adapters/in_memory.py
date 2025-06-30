"""In-memory event bus implementation."""

import asyncio
from collections import defaultdict
from typing import Any, Dict, List, Type

from src.agent_project.domain.events.base import DomainEvent
from src.agent_project.infrastructure.event_bus.ports import EventBus


class InMemoryEventBus(EventBus):
    """In-memory implementation of the event bus."""

    def __init__(self) -> None:
        """Initialize the in-memory event bus."""
        self._subscribers: Dict[Type[DomainEvent], List[Any]] = defaultdict(list)
        self._published_events: List[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all registered handlers."""
        if event is not None:
            self._published_events.append(event)

        # Get handlers for this specific event type
        handlers = self._subscribers.get(type(event), [])

        # Execute all handlers concurrently
        if handlers:
            await asyncio.gather(
                *[self._execute_handler(handler, event) for handler in handlers],
                return_exceptions=True,
            )

    async def subscribe(self, event_type: Type[DomainEvent], handler: Any) -> None:
        """Subscribe a handler to an event type."""
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    async def unsubscribe(self, event_type: Type[DomainEvent], handler: Any) -> None:
        """Unsubscribe a handler from an event type."""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    async def _execute_handler(self, handler: Any, event: DomainEvent) -> None:
        """Execute a single event handler."""
        try:
            if callable(handler):
                # Handler is a callable function - call it directly
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
        except Exception as e:
            # Log error but don't stop other handlers
            print(f"Error executing handler {handler} for event {event}: {e}")

    def get_published_events(self) -> List[DomainEvent]:
        """Get all published events (useful for testing)."""
        return self._published_events.copy()

    def clear_published_events(self) -> None:
        """Clear the published events list (useful for testing)."""
        self._published_events.clear()

    def get_handler_count(self, event_type: Type[DomainEvent]) -> int:
        """Get the number of handlers for an event type."""
        return len(self._subscribers.get(event_type, []))

    def get_subscriber_count(self, event_type: Type[DomainEvent]) -> int:
        """Get the number of subscribers for an event type (alias for get_handler_count)."""
        return self.get_handler_count(event_type)
