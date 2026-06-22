"""Tests for Superset permission operations."""

import logging
from unittest.mock import patch

from phiphi.superset import permissions


@patch("phiphi.superset.permissions.get_view_menu_id_by_resource_name")
@patch("phiphi.superset.permissions.get_permissions_related_to_view_menu")
def test_get_permission_id_on_view_menu_and_permission_type_success(mock_get_perms, mock_get_vm):
    """Test getting specific permission ID."""
    mock_get_vm.return_value = 42
    mock_get_perms.return_value = [
        {"id": 195, "permission": {"name": "datasource_access"}},
        {"id": 196, "permission": {"name": "can_read"}},
    ]
    logger = logging.getLogger("test")

    result = permissions.get_permission_id_on_view_menu_and_permission_type(
        "MyViewMenu", "datasource_access", logger
    )

    assert result == 195


@patch("phiphi.superset.permissions.get_view_menu_id_by_resource_name")
@patch("phiphi.superset.permissions.get_permissions_related_to_view_menu")
def test_get_permission_id_on_view_menu_and_permission_type_not_found(mock_get_perms, mock_get_vm):
    """Test when permission type is not found."""
    mock_get_vm.return_value = 42
    mock_get_perms.return_value = [{"id": 196, "permission": {"name": "can_read"}}]
    logger = logging.getLogger("test")

    result = permissions.get_permission_id_on_view_menu_and_permission_type(
        "MyViewMenu", "datasource_access", logger
    )

    assert result is None


@patch("phiphi.superset.permissions.get_permission_id_on_view_menu_and_permission_type")
@patch("phiphi.superset.permissions.dataset.get_dataset_by_schema_table")
def test_collect_datasource_permission_ids_success(mock_get_ds, mock_get_perm_id):
    """Test collecting datasource permission IDs."""
    mock_get_ds.return_value = {"id": 100}
    mock_get_perm_id.return_value = 200

    result = permissions.collect_datasource_access_permission_ids(
        db_name="DB",
        project_namespace="ns",
        table_names=["t1", "t2"],
    )

    assert result == [200, 200]
    assert mock_get_ds.call_count == 2
    assert mock_get_perm_id.call_count == 2


@patch("phiphi.superset.permissions.get_permission_id_on_view_menu_and_permission_type")
@patch("phiphi.superset.permissions.dataset.get_dataset_by_schema_table")
def test_collect_datasource_permission_ids_no_datasets(mock_get_ds, mock_get_perm_id):
    """Test empty list returned when datasets are not found."""
    mock_get_ds.return_value = None

    result = permissions.collect_datasource_access_permission_ids(
        db_name="DB",
        project_namespace="ns",
        table_names=["t1"],
    )

    assert result == []
    mock_get_perm_id.assert_not_called()
