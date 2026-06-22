"""Tests for Superset role operations."""

from unittest.mock import MagicMock, patch

from phiphi.superset import roles


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_roles_success(mock_get_base_url, mock_get_session):
    """Test successful role listing."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": [{"id": 1, "name": "Admin"}, {"id": 2, "name": "Public"}]
    }
    mock_session.get.return_value = mock_response

    result = roles.get_roles()

    assert len(result) == 2
    assert result[0]["name"] == "Admin"
    mock_session.get.assert_called_once_with(
        "http://superset.local/api/v1/security/roles/", timeout=30
    )


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_role_by_name_found(mock_get_base_url, mock_get_session):
    """Test finding role by name using server-side filter."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": [{"id": 1, "name": "Gamma"}]}
    mock_session.get.return_value = mock_response

    result = roles.get_role_by_name("Gamma")

    assert result is not None
    assert result["id"] == 1
    # Verify the server-side filter was used
    call_url = mock_session.get.call_args[0][0]
    assert "api/v1/security/roles/" in call_url
    assert "filters" in call_url


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_role_by_name_not_found(mock_get_base_url, mock_get_session):
    """Test get_role_by_name returns None when no match."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": []}
    mock_session.get.return_value = mock_response

    result = roles.get_role_by_name("NonExistent")

    assert result is None


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
@patch("phiphi.superset.roles.get_role_by_name")
def test_create_role_existing(mock_get_role, mock_get_base_url, mock_get_session):
    """Test idempotent creation if role exists."""
    mock_get_role.return_value = {"id": 123, "name": "ExistingRole"}

    result = roles.create_role("ExistingRole")

    assert result["id"] == 123
    mock_get_session.assert_called_once()


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
@patch("phiphi.superset.roles.get_role_by_name")
def test_create_role_new(mock_get_role, mock_get_base_url, mock_get_session):
    """Test creating a new role."""
    mock_get_role.return_value = None
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 456, "result": {"name": "NewRole"}}
    mock_session.post.return_value = mock_response

    result = roles.create_role("NewRole")

    assert result["id"] == 456
    assert result["name"] == "NewRole"
    mock_session.post.assert_called_once()


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_add_permissions_to_role_success(mock_get_base_url, mock_get_session):
    """Test adding permissions to a role."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_session.post.return_value = mock_response

    roles.add_permissions_to_role(123, [100, 101])

    mock_session.post.assert_called_once_with(
        "http://superset.local/api/v1/security/roles/123/permissions",
        json={"permission_view_menu_ids": [100, 101]},
        timeout=30,
    )


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_role_permissions_success(mock_get_base_url, mock_get_session):
    """Test fetching permissions for a role."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": [
            {
                "id": 264,
                "permission_name": "datasource_access",
                "view_menu_name": "[db].[table_name](id:1)",
            }
        ]
    }
    mock_session.get.return_value = mock_response

    result = roles.get_role_permissions(123, None, None)

    assert len(result) == 1
    assert result[0]["id"] == 264
    assert result[0]["permission_name"] == "datasource_access"
    mock_session.get.assert_called_once_with(
        "http://superset.local/api/v1/security/roles/123/permissions/", timeout=30
    )


@patch("phiphi.superset.client.get_authenticated_session")
@patch("phiphi.superset.client.get_base_url")
def test_get_role_permissions_returns_empty_list_when_result_missing(
    mock_get_base_url, mock_get_session
):
    """Test fetching role permissions returns [] when API payload has no result key."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_session.get.return_value = mock_response

    result = roles.get_role_permissions(123, None, None)

    assert result == []
