"""Integration tests for Superset client.

Run with:
    make test_integration PYTEST_ARGS_OVERRIDE=phiphi/tests/integration/superset/
"""

import pytest

from phiphi.superset import client, exceptions


def test_health_check_returns_true_when_superset_available(superset_url):
    """Test health_check returns True when Superset is running."""
    result = client.health_check(base_url=superset_url)

    assert result is True


def test_health_check_returns_false_for_invalid_url():
    """Test health_check returns False for invalid URL."""
    result = client.health_check(base_url="http://localhost:59999")

    assert result is False


def test_get_authenticated_session_succeeds(superset_url):
    """Test get_authenticated_session returns a session with CSRF token."""
    session = client.get_authenticated_session(base_url=superset_url)

    assert session is not None
    assert "X-CSRFToken" in session.headers
    assert session.headers["X-CSRFToken"]  # Not empty


def test_get_authenticated_session_raises_connection_error_for_invalid_url():
    """Test get_authenticated_session raises SupersetConnectionError for invalid URL."""
    with pytest.raises(exceptions.SupersetConnectionError):
        client.get_authenticated_session(base_url="http://localhost:59999")
