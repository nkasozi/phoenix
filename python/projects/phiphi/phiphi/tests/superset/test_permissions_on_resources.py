"""Tests for Superset permissions on resources operations."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from phiphi.superset import exceptions, permissions_on_resources


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_permissions_related_to_view_menu_success(mock_get_base_url, mock_get_session):
    """Test getting permissions related to view menu."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": [
            {"id": 100, "permission": {"name": "can_read"}},
            {"id": 101, "permission": {"name": "can_write"}},
        ]
    }
    mock_session.get.return_value = mock_response

    result = permissions_on_resources.get_permissions_related_to_view_menu(42)

    assert result is not None
    assert len(result) == 2
    assert result[0]["id"] == 100
    mock_session.get.assert_called_once_with(
        "http://superset.local/api/v1/security/permissions-resources/",
        params={"q": "(filters:!((col:view_menu,opr:rel_o_m,value:42)))"},
        timeout=30,
    )


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_permissions_related_to_view_menu_none(mock_get_base_url, mock_get_session):
    """Test behavior when view_menu_id is None."""
    result = permissions_on_resources.get_permissions_related_to_view_menu(None)
    assert result is None


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_permissions_related_to_view_menu_connection_error(
    mock_get_base_url, mock_get_session
):
    """Test connection error handling."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_session.get.side_effect = requests.exceptions.ConnectionError("Connection failed")

    with pytest.raises(exceptions.SupersetConnectionError, match="Cannot connect to Superset"):
        permissions_on_resources.get_permissions_related_to_view_menu(42)


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_permissions_related_to_view_menu_timeout_error(mock_get_base_url, mock_get_session):
    """Test timeout error handling."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_session.get.side_effect = requests.exceptions.Timeout("Timeout occurred")

    with pytest.raises(exceptions.SupersetTimeoutError, match="Request to Superset timed out"):
        permissions_on_resources.get_permissions_related_to_view_menu(42)
