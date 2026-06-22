"""Conftest for Superset integration tests.

All tests in this folder require SUPERSET_API_URL to be configured.
"""

import uuid

import pytest

from phiphi import config
from phiphi.superset import client, dashboard, template


@pytest.fixture(autouse=True)
def skip_if_superset_not_configured():
    """Skip all tests in this folder if SUPERSET_API_URL is not configured."""
    if not config.settings.SUPERSET_API_URL:
        pytest.skip("SUPERSET_API_URL not configured")


@pytest.fixture
def superset_url():
    """Get Superset URL from config."""
    return config.settings.SUPERSET_API_URL


@pytest.fixture
def superset_session(superset_url):
    """Get authenticated Superset session."""
    from phiphi.superset import client

    return client.get_authenticated_session(base_url=superset_url)


@pytest.fixture(scope="session")
def test_project_name():
    """Generate one unique test project name for the full integration test run."""
    return f"Test Project {uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def test_project_id():
    """Use one test project ID for the full integration test run."""
    return 5


@pytest.fixture(scope="session")
def test_dashboard_id(test_project_id, test_project_name):
    """Import the test project dashboard once for the session and return its ID.

    Skips if SUPERSET_API_URL is not configured or SUPERSET_DATABASE_UUID is missing.
    """
    if not config.settings.SUPERSET_API_URL:
        pytest.skip("SUPERSET_API_URL not configured")
    if not config.settings.SUPERSET_DATABASE_UUID:
        pytest.skip("SUPERSET_DATABASE_UUID not configured")

    url = config.settings.SUPERSET_API_URL
    sess = client.get_authenticated_session(base_url=url)

    dashboard_zip = template.create_project_dashboard_zip(
        project_id=test_project_id,
        project_name=test_project_name,
        database_uuid=config.settings.SUPERSET_DATABASE_UUID,
    )
    dashboard.import_dashboard(zip_file=dashboard_zip, overwrite=True, base_url=url, session=sess)

    title = template.get_dashboard_title(test_project_name, test_project_id)
    result = dashboard.get_dashboard_by_title(title=title, base_url=url, session=sess)
    if not result:
        pytest.fail(f"Dashboard not found after import: {title}")

    return int(result["id"])
