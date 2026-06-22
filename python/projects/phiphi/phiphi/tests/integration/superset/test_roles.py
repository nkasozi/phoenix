"""Integration tests for Superset role operations as used in project_resources.py.

Run with:
    make test_integration PYTEST_ARGS_OVERRIDE=phiphi/tests/integration/superset/
"""

import logging
import uuid

import pytest

from phiphi import config, utils
from phiphi.superset import constants as superset_constants
from phiphi.superset import dashboard, database, permissions, roles
from phiphi.superset.template import get_dashboard_title, get_superset_role_name


@pytest.fixture
def view_role_name(test_project_name, test_project_id):
    """Generate the view-only role name matching project_resources.py convention."""
    title = get_dashboard_title(test_project_name, test_project_id)
    return get_superset_role_name(test_project_id, "View", title)


@pytest.fixture
def edit_role_name(test_project_name, test_project_id):
    """Generate the edit role name matching project_resources.py convention."""
    title = get_dashboard_title(test_project_name, test_project_id)
    return get_superset_role_name(test_project_id, "Edit", title)


def test_get_role_by_name_returns_none_for_nonexistent(superset_url, superset_session):
    """Test get_role_by_name returns None for a nonexistent role."""
    result = roles.get_role_by_name(
        name=f"Nonexistent Role {uuid.uuid4().hex}",
        base_url=superset_url,
        session=superset_session,
    )

    assert result is None


def test_create_view_and_edit_roles(
    superset_url, superset_session, view_role_name, edit_role_name
):
    """Test creating view-only and edit roles as done in provision_superset_roles."""
    # Create view-only role (return value not used, matching project_resources.py)
    roles.create_role(view_role_name, base_url=superset_url, session=superset_session)

    # Create edit role and capture its id
    edit_role = roles.create_role(edit_role_name, base_url=superset_url, session=superset_session)
    edit_role_id = edit_role["id"]

    assert edit_role is not None
    assert edit_role["name"] == edit_role_name
    assert edit_role_id is not None

    # Verify view role was created
    found_view = roles.get_role_by_name(
        name=view_role_name, base_url=superset_url, session=superset_session
    )
    assert found_view is not None
    assert found_view["name"] == view_role_name


def test_create_role_is_idempotent(superset_url, superset_session, edit_role_name):
    """Test create_role returns the existing role when called with the same name."""
    first = roles.create_role(
        name=edit_role_name,
        base_url=superset_url,
        session=superset_session,
    )
    second = roles.create_role(
        name=edit_role_name,
        base_url=superset_url,
        session=superset_session,
    )

    assert first["id"] == second["id"]
    assert first["name"] == second["name"] == edit_role_name


def test_set_dashboard_roles(superset_url, superset_session, test_dashboard_id, view_role_name):
    """Test set_dashboard_roles assigns the view role to a dashboard."""
    view_role = roles.create_role(view_role_name, base_url=superset_url, session=superset_session)
    view_role_id = view_role["id"]

    dashboard.set_dashboard_roles(
        dashboard_id=test_dashboard_id,
        role_ids=[view_role_id],
        base_url=superset_url,
        session=superset_session,
    )

    result = superset_session.get(
        f"{superset_url}/api/v1/dashboard/{test_dashboard_id}", timeout=30
    )
    result.raise_for_status()
    role_ids_on_dashboard = [r["id"] for r in result.json().get("result", {}).get("roles", [])]
    assert view_role_id in role_ids_on_dashboard


def test_create_roles_with_special_character_project_name(superset_url, superset_session):
    """Test that role creation succeeds when the project name contains special characters.

    Regression test for a 422 error from FAB when role names contained raw special characters
    (e.g. '#', '$', '&', '(', ')') passed in unsanitised project names.
    get_dashboard_title must strip those characters before the role name is submitted.
    """
    # Project name that caused the real production 422 error
    raw_project_name = "fjkdls#$&*(#(*&#(*@$)&*#@jkldsdfjklajdfa75843792387432047930827 782974"
    project_id = 9999

    title = get_dashboard_title(raw_project_name, project_id)
    view_role_name = get_superset_role_name(project_id, "View", title)
    edit_role_name = get_superset_role_name(project_id, "Edit", title)

    # Role names must fit within FAB's 64-char column limit
    assert len(view_role_name) <= 64
    assert len(edit_role_name) <= 64
    # Special chars from the raw project name must have been stripped
    for char in "#$&*@":
        assert char not in view_role_name
        assert char not in edit_role_name

    view_role = roles.create_role(view_role_name, base_url=superset_url, session=superset_session)
    edit_role = roles.create_role(edit_role_name, base_url=superset_url, session=superset_session)

    assert view_role["id"] is not None
    assert edit_role["id"] is not None


def test_add_permissions_to_edit_role(
    superset_url, superset_session, test_project_id, edit_role_name
):
    """Test collecting datasource permissions and assigning them to the edit role.

    Mirrors the permission-assignment block in provision_superset_roles.
    """
    db_uuid = config.settings.SUPERSET_DATABASE_UUID
    if not db_uuid:
        pytest.skip("SUPERSET_DATABASE_UUID is not configured")

    edit_role = roles.create_role(edit_role_name, base_url=superset_url, session=superset_session)
    edit_role_id = edit_role["id"]

    db_name = database.get_database_name_by_uuid(
        db_uuid, base_url=superset_url, session=superset_session
    )
    project_namespace = utils.get_project_namespace(test_project_id)

    permission_view_ids = permissions.collect_datasource_access_permission_ids(
        db_name=db_name,
        project_namespace=project_namespace,
        table_names=superset_constants.DATASET_TABLES,
        logger=logging.getLogger(__name__),
        base_url=superset_url,
        session=superset_session,
    )

    if permission_view_ids:
        roles.add_permissions_to_role(
            role_id=edit_role_id,
            permission_view_ids=permission_view_ids,
            base_url=superset_url,
            session=superset_session,
        )

    # Verify role still exists and has the expected id
    found = roles.get_role_by_name(
        name=edit_role_name, base_url=superset_url, session=superset_session
    )
    assert found is not None
    assert found["id"] == edit_role_id

    # Verify edit role has expected permissions
    permissions_on_role = roles.get_role_permissions(
        role_id=edit_role_id, base_url=superset_url, session=superset_session
    )

    assert permissions_on_role != []
    assert permissions_on_role[0]["id"] in permission_view_ids
