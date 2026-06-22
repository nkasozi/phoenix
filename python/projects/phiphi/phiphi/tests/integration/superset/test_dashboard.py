"""Integration tests for Superset dashboard operations.

Run with:
    make test_integration PYTEST_ARGS_OVERRIDE=phiphi/tests/integration/superset/
"""

import pytest

from phiphi import config
from phiphi.superset import dashboard, template


@pytest.fixture
def test_dashboard_zip(test_project_id, test_project_name):
    """Create a test dashboard ZIP."""
    return template.create_project_dashboard_zip(
        project_id=test_project_id,
        project_name=test_project_name,
        database_uuid=config.settings.SUPERSET_DATABASE_UUID
        or "12345678-1234-1234-1234-123456789012",
    )


def test_get_dashboard_by_title_returns_none_for_nonexistent(superset_url, superset_session):
    """Test get_dashboard_by_title returns None for nonexistent dashboard."""
    result = dashboard.get_dashboard_by_title(
        title="Nonexistent Dashboard 12345",
        base_url=superset_url,
        session=superset_session,
    )

    assert result is None


def test_import_and_get_dashboard(
    superset_url, superset_session, test_project_id, test_project_name, test_dashboard_zip
):
    """Test importing, retrieving, and deleting a dashboard."""
    dashboard_title = template.get_dashboard_title(test_project_name, test_project_id)

    # Import dashboard
    import_result = dashboard.import_dashboard(
        zip_file=test_dashboard_zip,
        overwrite=True,
        base_url=superset_url,
        session=superset_session,
    )
    assert import_result is not None

    # Get dashboard by title
    found_dashboard = dashboard.get_dashboard_by_title(
        title=dashboard_title,
        base_url=superset_url,
        session=superset_session,
    )
    assert found_dashboard is not None
    assert found_dashboard["dashboard_title"] == dashboard_title


def test_delete_dashboard_is_idempotent(superset_url, superset_session):
    """Test delete_dashboard does not raise for nonexistent dashboard."""
    # Should not raise even for nonexistent ID
    dashboard.delete_dashboard(
        dashboard_id=999999999,
        base_url=superset_url,
        session=superset_session,
    )
