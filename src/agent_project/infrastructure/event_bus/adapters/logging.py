"""Logging event bus implementation."""

import logging
from typing import Any, Optional, Type

from src.agent_project.domain.events.base import DomainEvent
from src.agent_project.infrastructure.event_bus.ports import EventBus


class LoggingEventBus(EventBus):
    """Event bus implementation that logs all events."""

    def __init__(
        self,
        inner_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize the logging event bus."""
        self._inner_bus = inner_bus
        self._logger = logger or logging.getLogger(__name__)

    async def publish(self, event: DomainEvent) -> None:
        """Log the event and optionally forward to inner bus."""
        if event is not None:
            self._logger.info(
                "Publishing event: %s",
                event,
                extra={
                    "event_type": event.event_type,
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                    "timestamp": event.timestamp.isoformat(),
                },
            )

        if self._inner_bus:
            await self._inner_bus.publish(event)

    async def subscribe(self, event_type: Type[DomainEvent], handler: Any) -> None:
        """Log subscription and forward to inner bus if available."""
        self._logger.info("Subscribing handler %s to event type %s", handler, event_type.__name__)

        if self._inner_bus:
            await self._inner_bus.subscribe(event_type, handler)

    async def unsubscribe(self, event_type: Type[DomainEvent], handler: Any) -> None:
        """Log unsubscription and forward to inner bus if available."""
        self._logger.info("Unsubscribing handler %s from event type %s", handler, event_type.__name__)

        if self._inner_bus:
            await self._inner_bus.unsubscribe(event_type, handler)
