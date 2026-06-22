"""Tests for Superset resource operations."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from phiphi.superset import exceptions, resources


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_view_menu_id_by_resource_name_success(mock_get_base_url, mock_get_session):
    """Test getting view menu ID by resource name."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"count": 1, "result": [{"id": 42, "name": "ResourceName"}]}
    mock_session.get.return_value = mock_response

    result = resources.get_view_menu_id_by_resource_name("ResourceName")

    assert result == 42
    mock_session.get.assert_called_once_with(
        "http://superset.local/api/v1/security/resources/",
        params={"q": "(filters:!((col:name,opr:eq,value:'ResourceName')))"},
        timeout=30,
    )


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_view_menu_id_by_resource_name_invalid_count(mock_get_base_url, mock_get_session):
    """Test exception when multiple or zero resources found."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"count": 2, "result": [{"id": 1}, {"id": 2}]}
    mock_session.get.return_value = mock_response

    with pytest.raises(exceptions.SupersetError, match="Expected 1 resource"):
        resources.get_view_menu_id_by_resource_name("ResourceName")


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_view_menu_id_by_resource_name_connection_error(mock_get_base_url, mock_get_session):
    """Test connection error handling."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_session.get.side_effect = requests.exceptions.ConnectionError("Connection failed")

    with pytest.raises(exceptions.SupersetConnectionError, match="Cannot connect to Superset"):
        resources.get_view_menu_id_by_resource_name("ResourceName")


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_view_menu_id_by_resource_name_timeout_error(mock_get_base_url, mock_get_session):
    """Test timeout error handling."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_session.get.side_effect = requests.exceptions.Timeout("Timeout occurred")

    with pytest.raises(
        exceptions.SupersetTimeoutError, match="Request to Superset timed out: Timeout occurred"
    ):
        resources.get_view_menu_id_by_resource_name("ResourceName")
