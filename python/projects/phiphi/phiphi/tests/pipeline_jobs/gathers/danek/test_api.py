"""Test danek API."""

import json

import pytest

from phiphi.pipeline_jobs.gathers.danek.api import get_cursor_from_response_json  # adjust import


def test_end_cursor_dict():
    """Test that an 'end_cursor' dict is stringified and returned correctly.

    The returned dict should have a single key 'end_cursor' whose value
    is a JSON string representing the original dict.
    """
    response = {"end_cursor": {"server_cursor": "abc123"}}
    cursor = get_cursor_from_response_json(response)
    assert isinstance(cursor, dict)
    assert "end_cursor" in cursor
    # Ensure dict is stringified
    parsed = json.loads(cursor["end_cursor"])
    assert parsed == {"server_cursor": "abc123"}


def test_end_cursor_string():
    """Test that an 'end_cursor' string is returned unchanged.

    If 'end_cursor' is already a string, the function should preserve it
    and return a dict with that string as the value.
    """
    response = {"end_cursor": '{"server_cursor": "xyz789"}'}
    cursor = get_cursor_from_response_json(response)
    assert cursor == {"end_cursor": '{"server_cursor": "xyz789"}'}


def test_cursor_string():
    """Test that a 'cursor' string is returned correctly.

    If 'cursor' exists in the response, it should be returned as a
    single-key dict.
    """
    response = {"cursor": "page_2"}
    cursor = get_cursor_from_response_json(response)
    assert cursor == {"cursor": "page_2"}


def test_max_id_string():
    """Test that a 'max_id' string is returned correctly.

    If 'next_min_child_cursor' exists in the response, it should be returned as a
    single-key dict.
    """
    response = {"next_min_child_cursor": "mid_456"}
    cursor = get_cursor_from_response_json(response)
    assert cursor == {"max_id": "mid_456"}


def test_no_cursor():
    """Test that None is returned if no pagination key exists.

    If the response contains neither 'end_cursor', 'cursor', nor 'max_id',
    the function should return None.
    """
    response = {"results": [1, 2, 3]}
    cursor = get_cursor_from_response_json(response)
    assert cursor is None


def test_end_cursor_invalid_type():
    """Test that a RuntimeError is raised for invalid 'end_cursor' types.

    If 'end_cursor' exists but is not a dict or string, the function
    should raise a RuntimeError with an appropriate message.
    """
    response = {"end_cursor": 123}  # int instead of dict/string
    with pytest.raises(RuntimeError, match="end_cursor must be a string/dict/None"):
        get_cursor_from_response_json(response)
