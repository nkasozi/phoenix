"""Tests for Superset dataset operations."""

from unittest.mock import MagicMock, patch

from phiphi.superset import dataset


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_dataset_by_schema_table_success(mock_get_base_url, mock_get_session):
    """Test finding dataset by schema and table."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": [{"id": 1, "table_name": "table1", "schema": "schema1"}]
    }
    mock_session.get.return_value = mock_response

    result = dataset.get_dataset_by_schema_table("schema1", "table1")

    assert result is not None
    assert result["id"] == 1
    mock_session.get.assert_called_once_with(
        "http://superset.local/api/v1/dataset/",
        params={
            "q": (
                "(filters:!((col:schema,opr:eq,value:'schema1'),"
                "(col:table_name,opr:eq,value:'table1')))"
            )
        },
        timeout=30,
    )


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_delete_dataset_success(mock_get_base_url, mock_get_session):
    """Test successful dataset deletion."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_session.delete.return_value = mock_response

    dataset.delete_dataset(123)

    mock_session.delete.assert_called_once_with(
        "http://superset.local/api/v1/dataset/123", timeout=30
    )


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_delete_dataset_404_ignored(mock_get_base_url, mock_get_session):
    """Test that 404 on delete is ignored (idempotent)."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_session.delete.return_value = mock_response

    dataset.delete_dataset(123)

    mock_session.delete.assert_called_once()
    # Should not raise exception or call handle_response if it checks for 404
