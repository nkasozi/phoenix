"""Tests for Superset database operations."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from phiphi.superset import database, exceptions


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_databases_success(mock_get_base_url, mock_get_session):
    """Test successful database listing."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": [
            {"id": 1, "database_name": "db1", "uuid": "uuid1"},
            {"id": 2, "database_name": "db2", "uuid": "uuid2"},
        ]
    }
    mock_session.get.return_value = mock_response

    result = database.get_databases()

    assert len(result) == 2
    assert result[0]["database_name"] == "db1"
    mock_session.get.assert_called_once_with("http://superset.local/api/v1/database/", timeout=30)


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_databases_connection_error(mock_get_base_url, mock_get_session):
    """Test connection error handling."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    mock_session.get.side_effect = requests.exceptions.ConnectionError("Connection failed")

    with pytest.raises(exceptions.SupersetConnectionError, match="Cannot connect to Superset"):
        database.get_databases()


@patch("phiphi.superset.database.get_databases")
def test_get_database_by_uuid_found(mock_get_databases):
    """Test finding a database by UUID."""
    mock_get_databases.return_value = [
        {"id": 1, "database_name": "db1", "uuid": "uuid1"},
        {"id": 2, "database_name": "db2", "uuid": "uuid2"},
    ]

    result = database.get_database_by_uuid("uuid2")

    assert result is not None
    assert result["database_name"] == "db2"


@patch("phiphi.superset.database.get_databases")
def test_get_database_by_uuid_not_found(mock_get_databases):
    """Test database isn't found by UUID."""
    mock_get_databases.return_value = [{"id": 1, "database_name": "db1", "uuid": "uuid1"}]

    result = database.get_database_by_uuid("non-existent")

    assert result is None


@patch("phiphi.superset.database.get_database_by_uuid")
def test_get_database_name_by_uuid_found(mock_get_db):
    """Test getting database name by UUID."""
    mock_get_db.return_value = {"id": 1, "database_name": "Some OLAP Test", "uuid": "uuid1"}

    result = database.get_database_name_by_uuid("uuid1")

    assert result == "Some OLAP Test"


@patch("phiphi.superset.database.get_database_by_uuid")
def test_get_database_name_by_uuid_not_found(mock_get_db):
    """Test ValueError raised when database not found."""
    mock_get_db.return_value = None

    with pytest.raises(ValueError, match="Superset database with UUID missing-uuid not found"):
        database.get_database_name_by_uuid("missing-uuid")
