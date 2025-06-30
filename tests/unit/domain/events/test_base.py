"""Unit tests for base domain events."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime

import pytest

from src.agent_project.correlation import set_correlation_id
from src.agent_project.domain.events.base import DomainEvent, EventMetadata


@dataclass(frozen=True)
class SampleEvent(DomainEvent):
    """Sample event for unit testing."""

    message: str = "default message"
    user_id: str = "default user"


@dataclass(frozen=True)
class ComplexSampleEvent(DomainEvent):
    """More complex sample event with various data types."""

    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp_field: datetime = field(default_factory=datetime.utcnow)
    metadata_dict: dict = field(default_factory=dict)


class SampleEventMetadata:
    """Test cases for EventMetadata class."""

    def test_metadata_creation_with_defaults(self):
        """Test creating metadata with default values."""
        metadata = EventMetadata()

        assert metadata.event_id is not None
        assert metadata.correlation_id is not None
        assert metadata.timestamp is not None
        assert metadata.version == 1

        # Verify event_id is valid UUID
        uuid.UUID(metadata.event_id)
        # Verify correlation_id is valid UUID
        uuid.UUID(metadata.correlation_id)
        # Verify timestamp is recent
        assert (datetime.utcnow() - metadata.timestamp).total_seconds() < 1

    def test_metadata_creation_with_correlation_context(self):
        """Test that metadata uses correlation context."""
        test_correlation_id = str(uuid.uuid4())
        set_correlation_id(test_correlation_id)

        metadata = EventMetadata()

        assert metadata.correlation_id == test_correlation_id

    def test_metadata_immutability(self):
        """Test that EventMetadata is immutable."""
        metadata = EventMetadata()

        with pytest.raises(AttributeError):
            metadata.event_id = "new-id"

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = EventMetadata(
            event_id="test-event-id",
            correlation_id="test-correlation-id",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            version=2,
        )

        result = metadata.to_dict()

        expected = {
            "event_id": "test-event-id",
            "correlation_id": "test-correlation-id",
            "timestamp": "2023-01-01T12:00:00",
            "version": 2,
        }
        assert result == expected


class TestDomainEvent:
    """Test cases for DomainEvent base class."""

    def test_domain_event_creation(self):
        """Test creating a domain event."""
        event = SampleEvent(message="Hello World", user_id="user-123")

        assert event.message == "Hello World"
        assert event.user_id == "user-123"
        assert event.metadata is not None
        assert isinstance(event.metadata, EventMetadata)

    def test_domain_event_properties(self):
        """Test domain event property accessors."""
        event = SampleEvent(message="Test", user_id="user-123")

        assert event.event_id == event.metadata.event_id
        assert event.correlation_id == event.metadata.correlation_id
        assert event.timestamp == event.metadata.timestamp
        assert event.event_type == "SampleEvent"
        assert event.version == event.metadata.version

    def test_domain_event_immutability(self):
        """Test that domain events are immutable."""
        event = SampleEvent(message="Test", user_id="user-123")

        with pytest.raises(AttributeError):
            event.message = "Changed"

        with pytest.raises(AttributeError):
            event.metadata = EventMetadata()

    def test_domain_event_with_custom_metadata(self):
        """Test creating domain event with custom metadata."""
        custom_metadata = EventMetadata(event_id="custom-event-id", correlation_id="custom-correlation-id", version=5)

        event = SampleEvent(message="Custom event", user_id="user-456", metadata=custom_metadata)

        assert event.event_id == "custom-event-id"
        assert event.correlation_id == "custom-correlation-id"
        assert event.version == 5

    def test_domain_event_uses_correlation_context(self):
        """Test that domain events use current correlation context."""
        test_correlation_id = str(uuid.uuid4())
        set_correlation_id(test_correlation_id)

        event = SampleEvent(message="Test", user_id="user-123")

        assert event.correlation_id == test_correlation_id

    def test_event_to_dict_simple(self):
        """Test converting simple event to dictionary."""
        test_correlation_id = str(uuid.uuid4())
        set_correlation_id(test_correlation_id)

        event = SampleEvent(message="Hello", user_id="user-123")
        result = event.to_dict()

        assert result["event_type"] == "SampleEvent"
        assert result["metadata"]["correlation_id"] == test_correlation_id
        assert result["data"]["message"] == "Hello"
        assert result["data"]["user_id"] == "user-123"

    def test_event_to_dict_complex(self):
        """Test converting complex event to dictionary."""
        user_id = uuid.uuid4()
        timestamp_val = datetime(2023, 6, 15, 10, 30, 0)
        metadata_dict = {"key": "value", "nested": {"inner": "data"}}

        event = ComplexSampleEvent(user_id=user_id, timestamp_field=timestamp_val, metadata_dict=metadata_dict)

        result = event.to_dict()

        assert result["event_type"] == "ComplexSampleEvent"
        assert result["data"]["user_id"] == str(user_id)
        assert result["data"]["timestamp_field"] == "2023-06-15T10:30:00"
        assert result["data"]["metadata_dict"] == metadata_dict

    def test_event_string_representation(self):
        """Test string representation of events."""
        event = SampleEvent(message="Test", user_id="user-123")

        str_repr = str(event)

        assert "SampleEvent" in str_repr
        assert event.event_id in str_repr
        assert event.correlation_id in str_repr

    def test_event_repr_representation(self):
        """Test repr representation of events."""
        event = SampleEvent(message="Test", user_id="user-123")

        repr_str = repr(event)

        assert "SampleEvent" in repr_str
        assert "metadata=" in repr_str


class TestDomainEventBehavior:
    """Test cases for domain event behavior."""

    def test_multiple_events_have_different_ids(self):
        """Test that multiple events have unique IDs."""
        event1 = SampleEvent(message="First", user_id="user-1")
        event2 = SampleEvent(message="Second", user_id="user-2")

        assert event1.event_id != event2.event_id
        # But they should have same correlation ID if in same context
        assert event1.correlation_id == event2.correlation_id

    def test_events_in_different_correlation_contexts(self):
        """Test events created in different correlation contexts."""
        correlation_id_1 = str(uuid.uuid4())
        correlation_id_2 = str(uuid.uuid4())

        set_correlation_id(correlation_id_1)
        event1 = SampleEvent(message="First", user_id="user-1")

        set_correlation_id(correlation_id_2)
        event2 = SampleEvent(message="Second", user_id="user-2")

        assert event1.correlation_id == correlation_id_1
        assert event2.correlation_id == correlation_id_2
        assert event1.correlation_id != event2.correlation_id

    def test_event_timestamp_ordering(self):
        """Test that event timestamps are ordered correctly."""
        event1 = SampleEvent(message="First", user_id="user-1")
        # Small delay to ensure different timestamps
        import time

        time.sleep(0.001)
        event2 = SampleEvent(message="Second", user_id="user-2")

        assert event1.timestamp <= event2.timestamp

    def test_event_timestamp_is_utc(self):
        """Test that events have reasonable timestamps."""
        event = SampleEvent(message="Test", user_id="user-123")

        # Verify timestamp is recent (within last 5 seconds)
        now = datetime.utcnow()
        assert (now - event.timestamp).total_seconds() < 5
        assert event.timestamp <= now
