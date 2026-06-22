"""Tests for dashboard template transformation.

Run with: make test PYTEST_ARGS_OVERRIDE=phiphi/tests/superset/
"""

import io
import zipfile

import pytest
import yaml

from phiphi.superset import template
from phiphi.superset.constants import TEMPLATE_PATH

TEST_DATABASE_UUID = "test-database-uuid-1234"
TEST_SQLALCHEMY_URI = "bigquery://bq-project-test/"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def open_zip(zip_bytes: bytes) -> zipfile.ZipFile:
    """Open zip bytes as ZipFile."""
    return zipfile.ZipFile(io.BytesIO(zip_bytes), "r")


def get_datasets(zip_bytes: bytes) -> list[dict]:
    """Extract dataset YAML contents from zip bytes."""
    datasets = []
    with open_zip(zip_bytes) as zf:
        for name in zf.namelist():
            if "datasets" in name and name.endswith(".yaml"):
                datasets.append(yaml.safe_load(zf.read(name)))
    return datasets


def get_dashboards(zip_bytes: bytes) -> list[dict]:
    """Extract dashboard YAML contents from zip bytes."""
    dashboards = []
    with open_zip(zip_bytes) as zf:
        for name in zf.namelist():
            if "dashboards" in name and name.endswith(".yaml"):
                dashboards.append(yaml.safe_load(zf.read(name)))
    return dashboards


def get_charts(zip_bytes: bytes) -> list[dict]:
    """Extract chart YAML contents from zip bytes."""
    charts = []
    with open_zip(zip_bytes) as zf:
        for name in zf.namelist():
            if "charts" in name and name.endswith(".yaml"):
                charts.append(yaml.safe_load(zf.read(name)))
    return charts


# ============================================================================
# TESTS
# ============================================================================


@pytest.mark.patch_settings(
    {
        "SUPERSET_DATABASE_UUID": TEST_DATABASE_UUID,
        "SUPERSET_DATABASE_SQLALCHEMY_URI": TEST_SQLALCHEMY_URI,
    }
)
def test_creates_valid_zip(patch_settings):
    """Test that function produces a valid ZIP file."""
    result = template.create_project_dashboard_zip(
        project_id=123,
        project_name="Test Project",
    )

    assert isinstance(result, bytes)
    with open_zip(result) as zf:
        assert zf.testzip() is None
        assert len(zf.namelist()) > 0


@pytest.mark.patch_settings(
    {
        "SUPERSET_DATABASE_UUID": TEST_DATABASE_UUID,
        "SUPERSET_DATABASE_SQLALCHEMY_URI": TEST_SQLALCHEMY_URI,
    }
)
def test_schema_updated_to_project_namespace(patch_settings):
    """Test that dataset schemas are updated to project namespace."""
    result = template.create_project_dashboard_zip(
        project_id=456,
        project_name="Test Project",
    )

    for dataset in get_datasets(result):
        assert dataset["schema"] == "project_id456"


@pytest.mark.patch_settings(
    {
        "SUPERSET_DATABASE_UUID": TEST_DATABASE_UUID,
        "SUPERSET_DATABASE_SQLALCHEMY_URI": TEST_SQLALCHEMY_URI,
    }
)
def test_database_uuid_updated(patch_settings):
    """Test that dataset database_uuid is updated."""
    result = template.create_project_dashboard_zip(
        project_id=789,
        project_name="Test Project",
    )

    for dataset in get_datasets(result):
        assert dataset["database_uuid"] == TEST_DATABASE_UUID


@pytest.mark.patch_settings(
    {
        "SUPERSET_DATABASE_UUID": TEST_DATABASE_UUID,
        "SUPERSET_DATABASE_SQLALCHEMY_URI": TEST_SQLALCHEMY_URI,
    }
)
def test_catalog_extracted_from_uri(patch_settings):
    """Test that dataset catalog is extracted from SQLAlchemy URI."""
    result = template.create_project_dashboard_zip(
        project_id=789,
        project_name="Test Project",
    )

    for dataset in get_datasets(result):
        assert dataset["catalog"] == "bq-project-test"


@pytest.mark.patch_settings(
    {
        "SUPERSET_DATABASE_UUID": TEST_DATABASE_UUID,
        "SUPERSET_DATABASE_SQLALCHEMY_URI": TEST_SQLALCHEMY_URI,
    }
)
def test_dashboard_title_updated(patch_settings):
    """Test that dashboard title includes project name."""
    result = template.create_project_dashboard_zip(
        project_id=123,
        project_name="My Custom Project",
    )

    for dashboard in get_dashboards(result):
        assert dashboard["dashboard_title"] == "My Custom Project (123)"


@pytest.mark.patch_settings(
    {
        "SUPERSET_DATABASE_UUID": TEST_DATABASE_UUID,
        "SUPERSET_DATABASE_SQLALCHEMY_URI": TEST_SQLALCHEMY_URI,
    }
)
def test_uuids_are_unique_across_projects(patch_settings):
    """Test that different projects get different UUIDs."""
    result1 = template.create_project_dashboard_zip(project_id=1, project_name="Project 1")
    result2 = template.create_project_dashboard_zip(project_id=2, project_name="Project 2")

    dashboards1 = get_dashboards(result1)
    dashboards2 = get_dashboards(result2)

    uuid1 = dashboards1[0]["uuid"] if dashboards1 else ""
    uuid2 = dashboards2[0]["uuid"] if dashboards2 else ""

    assert uuid1 != uuid2
    assert uuid1
    assert uuid2


@pytest.mark.patch_settings(
    {
        "SUPERSET_DATABASE_UUID": TEST_DATABASE_UUID,
        "SUPERSET_DATABASE_SQLALCHEMY_URI": TEST_SQLALCHEMY_URI,
    }
)
def test_chart_dataset_references_updated(patch_settings):
    """Test that chart dataset_uuid references are updated consistently."""
    result = template.create_project_dashboard_zip(
        project_id=123,
        project_name="Test Project",
    )

    dataset_uuids = {ds["uuid"] for ds in get_datasets(result)}

    for chart in get_charts(result):
        if "dataset_uuid" in chart:
            assert chart["dataset_uuid"] in dataset_uuids


@pytest.mark.patch_settings(
    {
        "SUPERSET_DATABASE_UUID": TEST_DATABASE_UUID,
        "SUPERSET_DATABASE_SQLALCHEMY_URI": TEST_SQLALCHEMY_URI,
    }
)
def test_original_template_not_modified(patch_settings):
    """Test that original template files are not modified."""
    original_contents = {}
    for file_path in TEMPLATE_PATH.rglob("*.yaml"):
        original_contents[str(file_path)] = file_path.read_text()

    template.create_project_dashboard_zip(project_id=123, project_name="Test Project")

    for file_path in TEMPLATE_PATH.rglob("*.yaml"):
        assert file_path.read_text() == original_contents[str(file_path)]


def test_transform_dataset_updates_schema():
    """Test schema is updated to project namespace."""
    content = {
        "uuid": "old-uuid",
        "schema": "old_schema",
        "database_uuid": "old-db",
        "catalog": "old_catalog",
    }
    uuid_map = {"old-uuid": "new-uuid"}

    result = template._transform_dataset(
        content, "project_id99", uuid_map, "new-db-uuid", "new_catalog"
    )

    assert result["schema"] == "project_id99"
    assert result["uuid"] == "new-uuid"
    assert result["database_uuid"] == "new-db-uuid"
    assert result["catalog"] == "new_catalog"


def test_transform_dataset_keeps_uuid_when_not_in_map():
    """Test UUID is kept when not in map."""
    content = {"uuid": "unknown-uuid", "schema": "old_schema"}
    uuid_map = {"other-uuid": "new-uuid"}

    result = template._transform_dataset(
        content, "project_id1", uuid_map, "db-uuid", "test_catalog"
    )

    assert result["uuid"] == "unknown-uuid"


def test_transform_chart_updates_references():
    """Test chart UUID and dataset reference are updated."""
    content = {"uuid": "old-chart-uuid", "dataset_uuid": "old-dataset-uuid"}
    dataset_map = {"old-dataset-uuid": "new-dataset-uuid"}
    chart_map = {"old-chart-uuid": "new-chart-uuid"}

    result = template._transform_chart(content, dataset_map, chart_map)

    assert result["uuid"] == "new-chart-uuid"
    assert result["dataset_uuid"] == "new-dataset-uuid"


def test_transform_dashboard_updates_title_and_uuid():
    """Test dashboard UUID and title are updated."""
    content = {"uuid": "old-uuid", "dashboard_title": "Old Title"}

    result = template._transform_dashboard(content, "New Project", 123, "new-uuid", {}, {})

    assert result["uuid"] == "new-uuid"
    assert result["dashboard_title"] == "New Project (123)"


def test_transform_dashboard_updates_native_filter_references():
    """Test native filter dataset references are updated."""
    content = {
        "uuid": "old-uuid",
        "dashboard_title": "Title",
        "metadata": {
            "native_filter_configuration": [{"targets": [{"datasetUuid": "old-dataset-uuid"}]}]
        },
    }
    dataset_map = {"old-dataset-uuid": "new-dataset-uuid"}

    result = template._transform_dashboard(content, "Project", 123, "new-uuid", dataset_map, {})

    targets = result["metadata"]["native_filter_configuration"][0]["targets"]
    assert targets[0]["datasetUuid"] == "new-dataset-uuid"


def test_transform_dashboard_updates_chart_references():
    """Test chart UUID references in position data are updated."""
    content = {
        "uuid": "old-dashboard-uuid",
        "dashboard_title": "Title",
        "position": {
            "CHART-1": {
                "type": "CHART",
                "meta": {"uuid": "old-chart-uuid"},
            },
            "ROW-1": {"type": "ROW"},
        },
    }
    chart_map = {"old-chart-uuid": "new-chart-uuid"}

    result = template._transform_dashboard(
        content, "Project", 123, "new-dashboard-uuid", {}, chart_map
    )

    assert result["position"]["CHART-1"]["meta"]["uuid"] == "new-chart-uuid"


def test_get_dashboard_title():
    """Test dashboard title format."""
    assert template.get_dashboard_title("My Project", 123) == "My Project (123)"


def test_get_dashboard_title_strips_special_characters():
    """Special characters other than word chars, spaces, and hyphens are removed."""
    assert template.get_dashboard_title("My Project! @#$%", 1) == "My Project (1)"


def test_get_dashboard_title_preserves_hyphens_and_underscores():
    """Hyphens and underscores are kept."""
    assert template.get_dashboard_title("My-Project_Name", 5) == "My-Project_Name (5)"


def test_get_dashboard_title_normalizes_whitespace():
    """Multiple consecutive spaces are collapsed to one."""
    assert template.get_dashboard_title("My   Project", 2) == "My Project (2)"


def test_get_dashboard_title_truncates_long_name():
    """Names longer than _MAX_PROJECT_NAME_LENGTH are truncated."""
    long_name = "A" * 200
    result = template.get_dashboard_title(long_name, 7)
    expected_name = "A" * template._MAX_PROJECT_NAME_LENGTH
    assert result == f"{expected_name} (7)"


def test_get_dashboard_title_strips_leading_trailing_whitespace():
    """Leading/trailing whitespace is stripped."""
    assert template.get_dashboard_title("  My Project  ", 9) == "My Project (9)"
