"""Correlation ID management using context variables for async-safe tracking."""

import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CorrelationContext:
    """Context information for correlation tracking across the system."""

    correlation_id: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None

    @classmethod
    def create(cls, request_id: Optional[str] = None, user_id: Optional[str] = None) -> "CorrelationContext":
        """Create a new correlation context with generated correlation ID."""
        return cls(
            correlation_id=str(uuid.uuid4()),
            request_id=request_id,
            user_id=user_id,
        )


# Context variable for async-safe correlation tracking
correlation_context: ContextVar[CorrelationContext] = ContextVar(
    "correlation_context", default=CorrelationContext.create()
)


def set_correlation_context(context: CorrelationContext) -> None:
    """Set the correlation context for the current async context.

    Args:
        context: The correlation context to set
    """
    correlation_context.set(context)


def get_correlation_context() -> CorrelationContext:
    """Get the current correlation context.

    Returns:
        The current correlation context
    """
    return correlation_context.get()


def get_correlation_id() -> str:
    """Get the current correlation ID.

    Returns:
        The current correlation ID
    """
    return get_correlation_context().correlation_id


def set_correlation_id(correlation_id: str) -> None:
    """Set a new correlation ID in the current context.

    Args:
        correlation_id: The correlation ID to set
    """
    current_context = get_correlation_context()
    new_context = CorrelationContext(
        correlation_id=correlation_id,
        request_id=current_context.request_id,
        user_id=current_context.user_id,
    )
    set_correlation_context(new_context)


def clear_correlation_id() -> None:
    """Clear the correlation context by setting a new default context.

    This is useful for testing and cleanup scenarios.
    """
    default_context = CorrelationContext.create()
    set_correlation_context(default_context)


def create_correlation_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> CorrelationContext:
    """Create a new correlation context.

    Args:
        request_id: Optional request ID to include
        user_id: Optional user ID to include
        correlation_id: Optional correlation ID, generated if not provided

    Returns:
        New correlation context
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    return CorrelationContext(
        correlation_id=correlation_id,
        request_id=request_id,
        user_id=user_id,
    )
