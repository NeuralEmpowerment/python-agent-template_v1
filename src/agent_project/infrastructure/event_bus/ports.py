"""Event bus port definitions (interfaces)."""

from abc import ABC, abstractmethod
from typing import Any, List, Type

from src.agent_project.domain.events.base import DomainEvent


class EventBusError(Exception):
    """Base exception for event bus errors."""

    pass


class PublishError(EventBusError):
    """Exception raised when publishing an event fails."""

    pass


class SubscriptionError(EventBusError):
    """Exception raised when subscribing/unsubscribing fails."""

    pass


class EventBus(ABC):
    """Abstract event bus interface."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to the bus."""
        pass

    @abstractmethod
    async def subscribe(self, event_type: Type[DomainEvent], handler: Any) -> None:
        """Subscribe a handler to an event type."""
        pass

    @abstractmethod
    async def unsubscribe(self, event_type: Type[DomainEvent], handler: Any) -> None:
        """Unsubscribe a handler from an event type."""
        pass


class EventHandler(ABC):
    """Abstract event handler interface."""

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Handle an event."""
        pass


class EventStore(ABC):
    """Abstract event store interface."""

    @abstractmethod
    async def save_events(self, events: List[DomainEvent]) -> None:
        """Save events to the store."""
        pass

    @abstractmethod
    async def get_events(self, aggregate_id: str) -> List[DomainEvent]:
        """Get events for an aggregate."""
        pass
