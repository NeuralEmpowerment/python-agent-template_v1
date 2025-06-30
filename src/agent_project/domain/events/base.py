"""Base domain event classes."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from src.agent_project.correlation import get_correlation_id


@dataclass(frozen=True)
class EventMetadata:
    """Metadata for domain events."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: str = field(default_factory=get_correlation_id)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "event_id": self.event_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
        }


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""

    metadata: EventMetadata = field(default_factory=EventMetadata)

    @property
    def event_id(self) -> str:
        """Get event ID from metadata."""
        return self.metadata.event_id

    @property
    def correlation_id(self) -> str:
        """Get correlation ID from metadata."""
        return self.metadata.correlation_id

    @property
    def timestamp(self) -> datetime:
        """Get timestamp from metadata."""
        return self.metadata.timestamp

    @property
    def event_type(self) -> str:
        """Get event type name."""
        return self.__class__.__name__

    @property
    def version(self) -> int:
        """Get event version from metadata."""
        return self.metadata.version

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        # Get all fields except metadata
        data_fields = {}
        for field_name, field_def in self.__dataclass_fields__.items():
            if field_name != "metadata":
                data_fields[field_name] = getattr(self, field_name)

        # Convert complex types to strings
        for key, value in data_fields.items():
            if hasattr(value, "isoformat"):  # datetime
                data_fields[key] = value.isoformat()
            elif hasattr(value, "__str__") and not isinstance(value, (str, int, float, bool, list, dict)):
                data_fields[key] = str(value)

        return {
            "event_type": self.event_type,
            "metadata": self.metadata.to_dict(),
            "data": data_fields,
        }

    def __str__(self) -> str:
        """String representation of the event."""
        return f"{self.event_type}(id={self.event_id}, correlation_id={self.correlation_id})"

    def __repr__(self) -> str:
        """Detailed string representation of the event."""
        return f"{self.event_type}(metadata={self.metadata})"
