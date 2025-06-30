"""Tests for greeting service business logic."""
import re
from datetime import datetime

from src.agent_project.domain.hello_world.greeting_service import create_greeting, create_multiple_greetings


def test_create_greeting():
    """Test greeting creation with a simple name."""
    result = create_greeting("TestUser")

    # Verify the basic structure
    assert "Hello TestUser" in result
    assert "beautiful World" in result
    assert "time is" in result

    # Verify it contains a timestamp
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", result)


def test_create_greeting_with_special_characters():
    """Test greeting creation with names containing special characters."""
    result = create_greeting("José-María")

    assert "Hello José-María" in result
    assert "beautiful World" in result


def test_create_greeting_with_empty_string():
    """Test greeting creation with empty string name."""
    result = create_greeting("")

    assert "Hello " in result
    assert "beautiful World" in result


def test_create_multiple_greetings():
    """Test creation of multiple greetings."""
    names = ["Alice", "Bob", "Charlie"]
    results = create_multiple_greetings(names)

    # Verify we get the right number of results
    assert len(results) == 3

    # Verify each result contains the expected name
    assert "Hello Alice" in results[0]
    assert "Hello Bob" in results[1]
    assert "Hello Charlie" in results[2]

    # Verify all results have the expected structure
    for result in results:
        assert "beautiful World" in result
        assert "time is" in result


def test_create_multiple_greetings_empty_list():
    """Test creation of greetings with empty list."""
    results = create_multiple_greetings([])

    assert results == []


def test_create_multiple_greetings_single_name():
    """Test creation of greetings with single name."""
    results = create_multiple_greetings(["SingleUser"])

    assert len(results) == 1
    assert "Hello SingleUser" in results[0]


def test_greeting_consistency():
    """Test that greetings are consistent in format."""
    names = ["User1", "User2", "User3"]
    results = create_multiple_greetings(names)

    # All should follow the same pattern
    for i, result in enumerate(results):
        expected_start = f"Hello {names[i]}, it's a beautiful World!"
        assert result.startswith(expected_start)


def test_greeting_timestamp_recent():
    """Test that the timestamp in greeting is recent."""
    before_call = datetime.now().replace(microsecond=0)  # Remove microseconds for comparison
    result = create_greeting("TimeTest")
    after_call = datetime.now().replace(microsecond=0)  # Remove microseconds for comparison

    # Extract timestamp from result
    timestamp_match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", result)
    assert timestamp_match is not None

    timestamp_str = timestamp_match.group(1)
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

    # Verify timestamp is between our before/after markers (allowing 1 second tolerance)
    assert before_call <= timestamp <= after_call or (timestamp - before_call).total_seconds() <= 1
