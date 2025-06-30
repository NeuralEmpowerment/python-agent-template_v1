"""Pure business logic for greeting creation."""

from datetime import datetime


def create_greeting(name: str) -> str:
    """Create a greeting message with timestamp.

    This is pure business logic that can be tested independently
    of any framework decorators or infrastructure concerns.

    Args:
        name: The name to include in the greeting

    Returns:
        A formatted greeting string with current timestamp
    """
    return f"Hello {name}, it's a beautiful World! The time is {datetime.now()}"


def create_multiple_greetings(names: list[str]) -> list[str]:
    """Create greeting messages for multiple names.

    Args:
        names: List of names to create greetings for

    Returns:
        List of greeting strings
    """
    return [create_greeting(name) for name in names]
