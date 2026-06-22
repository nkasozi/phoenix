"""Tests for project_resources provisioning flow."""

from unittest import mock

import pytest

from phiphi.pipeline_jobs import project_resources
from phiphi.superset import constants as superset_constants
from phiphi.superset import exceptions as superset_exceptions


@mock.patch("phiphi.pipeline_jobs.project_resources.project_pipeline_jobs.init_project_db.fn")
def test_provision_bigquery_dataset(mock_init_db):
    """Test BigQuery dataset provisioning task."""
    mock_init_db.return_value = "project_id123"

    result = project_resources.provision_bigquery_dataset.fn(
        project_id=123,
        project_namespace="project_id123",
        workspace_slug="main",
        with_dummy_data=True,
    )

    assert result == "project_id123"
    mock_init_db.assert_called_once_with(
        project_namespace="project_id123",
        workspace_slug="main",
        with_dummy_data=True,
        logger=mock.ANY,
    )


@mock.patch("phiphi.pipeline_jobs.project_resources.project_pipeline_jobs.init_project_db.fn")
def test_provision_bigquery_dataset_without_dummy_data(mock_init_db):
    """Test BigQuery dataset provisioning task without dummy data."""
    mock_init_db.return_value = "project_id456"

    result = project_resources.provision_bigquery_dataset.fn(
        project_id=456,
        project_namespace="project_id456",
        workspace_slug="test_workspace",
        with_dummy_data=False,
    )

    assert result == "project_id456"
    mock_init_db.assert_called_once_with(
        project_namespace="project_id456",
        workspace_slug="test_workspace",
        with_dummy_data=False,
        logger=mock.ANY,
    )


@mock.patch(
    "phiphi.pipeline_jobs.project_resources.project_pipeline_jobs.init_prefect_concurrency"
)
def test_provision_prefect_rate_limits(mock_init_concurrency):
    """Test Prefect rate limits provisioning task."""
    project_resources.provision_prefect_rate_limits.fn(
        project_id=123,
    )

    mock_init_concurrency.assert_called_once_with(123)


@mock.patch(
    "phiphi.pipeline_jobs.project_resources.project_crud.set_project_resources_provisioned"
)
@mock.patch("phiphi.pipeline_jobs.project_resources.platform_db.get_session_context")
def test_update_project_resources_provisioned(mock_get_session, mock_set_provisioned):
    """Test updating project_resources_provisioned_at timestamp without dashboard_id."""
    mock_session = mock.MagicMock()
    mock_get_session.return_value.__enter__ = mock.MagicMock(return_value=mock_session)
    mock_get_session.return_value.__exit__ = mock.MagicMock(return_value=False)

    project_resources.update_project_resources_provisioned.fn(
        project_id=123,
        dashboard_id=None,
    )

    mock_set_provisioned.assert_called_once_with(
        mock_session,
        123,
        None,
        superset_view_role_id=None,
        superset_edit_role_id=None,
    )


@mock.patch(
    "phiphi.pipeline_jobs.project_resources.project_crud.set_project_resources_provisioned"
)
@mock.patch("phiphi.pipeline_jobs.project_resources.platform_db.get_session_context")
def test_update_project_resources_provisioned_with_dashboard_id(
    mock_get_session, mock_set_provisioned
):
    """Test updating project_resources_provisioned_at timestamp with a dashboard_id."""
    mock_session = mock.MagicMock()
    mock_get_session.return_value.__enter__ = mock.MagicMock(return_value=mock_session)
    mock_get_session.return_value.__exit__ = mock.MagicMock(return_value=False)

    project_resources.update_project_resources_provisioned.fn(
        project_id=123,
        dashboard_id=42,
    )

    mock_set_provisioned.assert_called_once_with(
        mock_session,
        123,
        42,
        superset_view_role_id=None,
        superset_edit_role_id=None,
    )


@mock.patch(
    "phiphi.pipeline_jobs.project_resources.project_crud.set_project_resources_provisioned"
)
@mock.patch("phiphi.pipeline_jobs.project_resources.platform_db.get_session_context")
def test_update_project_resources_provisioned_with_role_ids(
    mock_get_session, mock_set_provisioned
):
    """Test updating project_resources_provisioned_at timestamp with role IDs."""
    mock_session = mock.MagicMock()
    mock_get_session.return_value.__enter__ = mock.MagicMock(return_value=mock_session)
    mock_get_session.return_value.__exit__ = mock.MagicMock(return_value=False)

    project_resources.update_project_resources_provisioned.fn(
        project_id=123,
        dashboard_id=42,
        superset_view_role_id=10,
        superset_edit_role_id=20,
    )

    mock_set_provisioned.assert_called_once_with(
        mock_session,
        123,
        42,
        superset_view_role_id=10,
        superset_edit_role_id=20,
    )


@mock.patch("phiphi.pipeline_jobs.project_resources.link_superset_roles_to_dashboard")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_superset_roles")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_superset_dashboard")
@mock.patch("phiphi.pipeline_jobs.project_resources.update_project_resources_provisioned")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_prefect_rate_limits")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_bigquery_dataset")
def test_provision_project_resources_flow_all_enabled(
    mock_provision_bq,
    mock_provision_rate_limits,
    mock_update_provisioned,
    mock_provision_superset,
    mock_provision_roles,
    mock_provision_dashboard_roles,
):
    """Test full provisioning flow with all options enabled."""
    mock_provision_superset.return_value = 42
    mock_provision_roles.return_value = (10, 20)

    project_resources.provision_project_resources_flow.fn(
        project_id=123,
        project_name="Test project",
        project_namespace="project_id123",
        workspace_slug="main",
        with_dummy_data=True,
        provision_bigquery=True,
        provision_rate_limits=True,
        provision_superset=True,
    )

    mock_provision_bq.assert_called_once_with(
        project_id=123,
        project_namespace="project_id123",
        workspace_slug="main",
        with_dummy_data=True,
        logger=mock.ANY,
    )
    mock_provision_rate_limits.assert_called_once_with(
        project_id=123,
        logger=mock.ANY,
    )
    mock_provision_superset.assert_called_once_with(
        project_id=123,
        project_name="Test project",
        project_namespace="project_id123",
        logger=mock.ANY,
    )
    mock_provision_roles.assert_called_once_with(
        project_id=123,
        project_name="Test project",
        logger=mock.ANY,
    )
    mock_provision_dashboard_roles.assert_called_once_with(
        project_id=123,
        dashboard_id=42,
        view_role_id=10,
        logger=mock.ANY,
    )
    mock_update_provisioned.assert_called_once_with(
        project_id=123,
        dashboard_id=42,
        superset_view_role_id=10,
        superset_edit_role_id=20,
        logger=mock.ANY,
    )


@mock.patch("phiphi.pipeline_jobs.project_resources.update_project_resources_provisioned")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_prefect_rate_limits")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_bigquery_dataset")
def test_provision_project_resources_flow_bigquery_only(
    mock_provision_bq,
    mock_provision_rate_limits,
    mock_update_provisioned,
):
    """Test provisioning flow with only BigQuery enabled."""
    project_resources.provision_project_resources_flow.fn(
        project_id=123,
        project_name="Test project",
        project_namespace="project_id123",
        workspace_slug="main",
        provision_bigquery=True,
        provision_rate_limits=False,
    )

    mock_provision_bq.assert_called_once()
    mock_provision_rate_limits.assert_not_called()
    mock_update_provisioned.assert_called_once_with(
        project_id=123,
        dashboard_id=None,
        superset_view_role_id=None,
        superset_edit_role_id=None,
        logger=mock.ANY,
    )


@mock.patch("phiphi.pipeline_jobs.project_resources.update_project_resources_provisioned")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_prefect_rate_limits")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_bigquery_dataset")
def test_provision_project_resources_flow_rate_limits_only(
    mock_provision_bq,
    mock_provision_rate_limits,
    mock_update_provisioned,
):
    """Test provisioning flow with only rate limits enabled."""
    project_resources.provision_project_resources_flow.fn(
        project_id=123,
        project_name="Test project",
        project_namespace="project_id123",
        workspace_slug="main",
        provision_bigquery=False,
        provision_rate_limits=True,
    )

    mock_provision_bq.assert_not_called()
    mock_provision_rate_limits.assert_called_once()
    mock_update_provisioned.assert_called_once_with(
        project_id=123,
        dashboard_id=None,
        superset_view_role_id=None,
        superset_edit_role_id=None,
        logger=mock.ANY,
    )


@mock.patch("phiphi.pipeline_jobs.project_resources.update_project_resources_provisioned")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_prefect_rate_limits")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_bigquery_dataset")
def test_provision_project_resources_flow_bigquery_disabled(
    mock_provision_bq,
    mock_provision_rate_limits,
    mock_update_provisioned,
):
    """Test provisioning flow skips BigQuery when provision_bigquery=False."""
    project_resources.provision_project_resources_flow.fn(
        project_id=123,
        project_name="Test project",
        project_namespace="project_id123",
        workspace_slug="main",
        provision_bigquery=False,
        provision_rate_limits=False,
    )

    mock_provision_bq.assert_not_called()
    mock_provision_rate_limits.assert_not_called()
    mock_update_provisioned.assert_called_once_with(
        project_id=123,
        dashboard_id=None,
        superset_view_role_id=None,
        superset_edit_role_id=None,
        logger=mock.ANY,
    )


@mock.patch("phiphi.pipeline_jobs.project_resources.update_project_resources_provisioned")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_prefect_rate_limits")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_bigquery_dataset")
def test_provision_project_resources_flow_only_update_provisioned(
    mock_provision_bq,
    mock_provision_rate_limits,
    mock_update_provisioned,
):
    """Test provisioning flow with all provisioning disabled still updates timestamp."""
    project_resources.provision_project_resources_flow.fn(
        project_id=123,
        project_name="Test project",
        project_namespace="project_id123",
        workspace_slug="main",
        provision_bigquery=False,
        provision_rate_limits=False,
        provision_superset=False,
    )

    mock_provision_bq.assert_not_called()
    mock_provision_rate_limits.assert_not_called()
    mock_update_provisioned.assert_called_once_with(
        project_id=123,
        dashboard_id=None,
        superset_view_role_id=None,
        superset_edit_role_id=None,
        logger=mock.ANY,
    )


@mock.patch("phiphi.pipeline_jobs.project_resources.update_project_resources_provisioned")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_bigquery_dataset")
def test_provision_project_resources_flow_with_dummy_data(
    mock_provision_bq,
    mock_update_provisioned,
):
    """Test provisioning flow passes with_dummy_data correctly."""
    project_resources.provision_project_resources_flow.fn(
        project_id=123,
        project_name="Test project",
        project_namespace="project_id123",
        workspace_slug="main",
        with_dummy_data=False,
        provision_bigquery=True,
        provision_rate_limits=False,
    )

    mock_provision_bq.assert_called_once_with(
        project_id=123,
        project_namespace="project_id123",
        workspace_slug="main",
        with_dummy_data=False,
        logger=mock.ANY,
    )
    mock_update_provisioned.assert_called_once_with(
        project_id=123,
        dashboard_id=None,
        superset_view_role_id=None,
        superset_edit_role_id=None,
        logger=mock.ANY,
    )


def test_create_deployments_returns_coroutines():
    """Test that create_deployments returns a list of coroutines."""
    with mock.patch.object(
        project_resources.provision_project_resources_flow, "deploy"
    ) as mock_deploy:
        mock_deploy.return_value = mock.AsyncMock()

        result = project_resources.create_deployments(
            override_work_pool_name="test-pool",
            deployment_name_prefix="test-",
            image="test-image:latest",
            tags=["test"],
            build=False,
            push=False,
        )

        assert isinstance(result, list)
        assert len(result) == 1
        mock_deploy.assert_called_once_with(
            name="test-provision_project_resources_flow",
            work_pool_name="test-pool",
            image="test-image:latest",
            build=False,
            push=False,
            tags=["test"],
        )


@pytest.mark.asyncio
@mock.patch(
    "phiphi.pipeline_jobs.project_resources.deployments.run_deployment",
    new_callable=mock.AsyncMock,
)
async def test_run_provision_deployment(mock_run_deployment):
    """Test run_provision_deployment calls Prefect with correct parameters."""
    mock_flow_run = mock.MagicMock()
    mock_flow_run.id = "test-flow-run-id"
    mock_flow_run.name = "test-flow-run-name"
    mock_run_deployment.return_value = mock_flow_run

    parameters = {
        "project_id": 123,
        "project_namespace": "project_id123",
        "workspace_slug": "main",
    }

    result = await project_resources.run_provision_deployment(parameters)

    assert result == mock_flow_run
    mock_run_deployment.assert_awaited_once_with(
        name=project_resources.PROVISION_DEPLOYMENT_NAME,
        parameters=parameters,
        timeout=0,
    )


@pytest.mark.asyncio
@mock.patch(
    "phiphi.pipeline_jobs.project_resources.run_provision_deployment",
    new_callable=mock.AsyncMock,
)
async def test_start_provision_deployment(mock_run_deployment):
    """Test start_provision_deployment passes all parameters correctly."""
    mock_flow_run = mock.MagicMock()
    mock_flow_run.id = "test-flow-run-id"
    mock_flow_run.name = "test-flow-run-name"
    mock_run_deployment.return_value = mock_flow_run

    result = await project_resources.start_provision_deployment(
        project_id=123,
        project_name="Test project",
        project_namespace="project_id123",
        workspace_slug="main",
        with_dummy_data=True,
        provision_bigquery=True,
        provision_rate_limits=False,
        provision_superset=False,
    )

    assert result == mock_flow_run
    mock_run_deployment.assert_awaited_once_with(
        {
            "project_id": 123,
            "project_name": "Test project",
            "project_namespace": "project_id123",
            "workspace_slug": "main",
            "with_dummy_data": True,
            "provision_bigquery": True,
            "provision_rate_limits": False,
            "provision_superset": False,
        }
    )


@pytest.mark.asyncio
@mock.patch(
    "phiphi.pipeline_jobs.project_resources.run_provision_deployment",
    new_callable=mock.AsyncMock,
)
async def test_start_provision_deployment_default_values(mock_run_deployment):
    """Test start_provision_deployment uses correct default values."""
    mock_flow_run = mock.MagicMock()
    mock_run_deployment.return_value = mock_flow_run

    await project_resources.start_provision_deployment(
        project_id=456,
        project_name="Test project",
        project_namespace="project_id456",
        workspace_slug="test",
    )

    mock_run_deployment.assert_awaited_once_with(
        {
            "project_id": 456,
            "project_name": "Test project",
            "project_namespace": "project_id456",
            "workspace_slug": "test",
            "with_dummy_data": True,
            "provision_bigquery": True,
            "provision_rate_limits": True,
            "provision_superset": False,
        }
    )


# --- Failed Provisioning Tests ---


@mock.patch("phiphi.pipeline_jobs.project_resources.project_pipeline_jobs.init_project_db.fn")
def test_provision_bigquery_dataset_failure(mock_init_db):
    """Test that BigQuery provisioning failure propagates exception."""
    mock_init_db.side_effect = Exception("BigQuery connection failed")

    with pytest.raises(Exception, match="BigQuery connection failed"):
        project_resources.provision_bigquery_dataset.fn(
            project_id=123,
            project_namespace="project_id123",
            workspace_slug="main",
            with_dummy_data=True,
        )


@mock.patch(
    "phiphi.pipeline_jobs.project_resources.project_pipeline_jobs.init_prefect_concurrency"
)
def test_provision_prefect_rate_limits_failure(mock_init_concurrency):
    """Test that Prefect rate limits provisioning failure propagates exception."""
    mock_init_concurrency.side_effect = Exception("Prefect API unavailable")

    with pytest.raises(Exception, match="Prefect API unavailable"):
        project_resources.provision_prefect_rate_limits.fn(
            project_id=123,
        )


@mock.patch(
    "phiphi.pipeline_jobs.project_resources.project_crud.set_project_resources_provisioned"
)
@mock.patch("phiphi.pipeline_jobs.project_resources.platform_db.get_session_context")
def test_update_project_resources_provisioned_failure(mock_get_session, mock_set_provisioned):
    """Test that updating provisioned timestamp failure propagates exception."""
    mock_session = mock.MagicMock()
    mock_get_session.return_value.__enter__ = mock.MagicMock(return_value=mock_session)
    mock_get_session.return_value.__exit__ = mock.MagicMock(return_value=False)
    mock_set_provisioned.side_effect = Exception("Database connection lost")

    with pytest.raises(Exception, match="Database connection lost"):
        project_resources.update_project_resources_provisioned.fn(
            project_id=123,
            dashboard_id=None,
        )


@mock.patch("phiphi.pipeline_jobs.project_resources.update_project_resources_provisioned")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_prefect_rate_limits")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_bigquery_dataset")
def test_provision_project_resources_flow_bigquery_failure(
    mock_provision_bq,
    mock_provision_rate_limits,
    mock_update_provisioned,
):
    """Test provisioning flow propagates BigQuery failure."""
    mock_provision_bq.side_effect = Exception("BigQuery provisioning failed")

    with pytest.raises(Exception, match="BigQuery provisioning failed"):
        project_resources.provision_project_resources_flow.fn(
            project_id=123,
            project_name="Test project",
            project_namespace="project_id123",
            workspace_slug="main",
            provision_bigquery=True,
            provision_rate_limits=True,
        )

    # Subsequent tasks should not be called after failure
    mock_provision_rate_limits.assert_not_called()
    mock_update_provisioned.assert_not_called()


@mock.patch("phiphi.pipeline_jobs.project_resources.update_project_resources_provisioned")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_prefect_rate_limits")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_bigquery_dataset")
def test_provision_project_resources_flow_rate_limits_failure(
    mock_provision_bq,
    mock_provision_rate_limits,
    mock_update_provisioned,
):
    """Test provisioning flow propagates rate limits failure."""
    mock_provision_rate_limits.side_effect = Exception("Rate limits provisioning failed")

    with pytest.raises(Exception, match="Rate limits provisioning failed"):
        project_resources.provision_project_resources_flow.fn(
            project_id=123,
            project_name="Test project",
            project_namespace="project_id123",
            workspace_slug="main",
            provision_bigquery=True,
            provision_rate_limits=True,
        )

    # BigQuery should succeed before rate limits failure
    mock_provision_bq.assert_called_once()
    mock_update_provisioned.assert_not_called()


@mock.patch("phiphi.pipeline_jobs.project_resources.update_project_resources_provisioned")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_prefect_rate_limits")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_bigquery_dataset")
def test_provision_project_resources_flow_update_provisioned_failure(
    mock_provision_bq,
    mock_provision_rate_limits,
    mock_update_provisioned,
):
    """Test provisioning flow propagates update_provisioned failure."""
    mock_update_provisioned.side_effect = Exception("Failed to mark project provisioned")

    with pytest.raises(Exception, match="Failed to mark project provisioned"):
        project_resources.provision_project_resources_flow.fn(
            project_id=123,
            project_name="Test project",
            project_namespace="project_id123",
            workspace_slug="main",
            provision_bigquery=True,
            provision_rate_limits=True,
        )

    # Both tasks should succeed before update_provisioned failure
    mock_provision_bq.assert_called_once()
    mock_provision_rate_limits.assert_called_once()


@pytest.mark.asyncio
@mock.patch(
    "phiphi.pipeline_jobs.project_resources.deployments.run_deployment",
    new_callable=mock.AsyncMock,
)
async def test_run_provision_deployment_failure(mock_run_deployment):
    """Test run_provision_deployment propagates deployment failure."""
    mock_run_deployment.side_effect = Exception("Deployment not found")

    with pytest.raises(Exception, match="Deployment not found"):
        await project_resources.run_provision_deployment(
            {"project_id": 123, "project_namespace": "project_id123", "workspace_slug": "main"}
        )


@pytest.mark.asyncio
@mock.patch(
    "phiphi.pipeline_jobs.project_resources.run_provision_deployment",
    new_callable=mock.AsyncMock,
)
async def test_start_provision_deployment_failure(mock_run_deployment):
    """Test start_provision_deployment propagates deployment failure."""
    mock_run_deployment.side_effect = Exception("Failed to start deployment")

    with pytest.raises(Exception, match="Failed to start deployment"):
        await project_resources.start_provision_deployment(
            project_id=123,
            project_name="Test project",
            project_namespace="project_id123",
            workspace_slug="main",
        )


@mock.patch("phiphi.pipeline_jobs.project_resources.dashboard.get_dashboard_by_title")
@mock.patch("phiphi.pipeline_jobs.project_resources.dashboard.import_dashboard")
@mock.patch("phiphi.pipeline_jobs.project_resources.client.get_authenticated_session")
@mock.patch("phiphi.pipeline_jobs.project_resources.client.get_base_url")
@mock.patch("phiphi.pipeline_jobs.project_resources.template.create_project_dashboard_zip")
@mock.patch("phiphi.pipeline_jobs.project_resources.config.settings")
def test_provision_superset_dashboard(
    mock_settings,
    mock_create_zip,
    mock_get_base_url,
    mock_get_session,
    mock_import_dashboard,
    mock_get_dashboard_by_title,
):
    """Test Superset dashboard provisioning happy path."""
    mock_settings.SUPERSET_DATABASE_UUID = "12345678-1234-1234-1234-123456789012"
    mock_zip = mock.MagicMock()
    mock_create_zip.return_value = mock_zip
    mock_get_base_url.return_value = "http://superset.local"
    mock_session = mock.MagicMock()
    mock_get_session.return_value = mock_session
    mock_get_dashboard_by_title.return_value = {"id": 42, "title": "project_id123"}

    result = project_resources.provision_superset_dashboard.fn(
        project_id=123,
        project_name="Test project",
        project_namespace="project_id123",
    )

    assert result == 42
    mock_create_zip.assert_called_once_with(
        project_id=123,
        project_name="Test project",
        template_path=superset_constants.TEMPLATE_PATH,
        database_uuid="12345678-1234-1234-1234-123456789012",
    )
    mock_get_base_url.assert_called_once()
    mock_get_session.assert_called_once_with(base_url="http://superset.local")
    mock_import_dashboard.assert_called_once_with(
        zip_file=mock_zip,
        overwrite=False,
        base_url="http://superset.local",
        session=mock_session,
    )
    mock_get_dashboard_by_title.assert_called_once_with(
        title=mock.ANY,
        base_url="http://superset.local",
        session=mock_session,
    )


@mock.patch("phiphi.pipeline_jobs.project_resources.dashboard.get_dashboard_by_title")
@mock.patch("phiphi.pipeline_jobs.project_resources.dashboard.import_dashboard")
@mock.patch("phiphi.pipeline_jobs.project_resources.client.get_authenticated_session")
@mock.patch("phiphi.pipeline_jobs.project_resources.client.get_base_url")
@mock.patch("phiphi.pipeline_jobs.project_resources.template.create_project_dashboard_zip")
@mock.patch("phiphi.pipeline_jobs.project_resources.config.settings")
def test_provision_superset_dashboard_not_found(
    mock_settings,
    mock_create_zip,
    mock_get_base_url,
    mock_get_session,
    mock_import_dashboard,
    mock_get_dashboard_by_title,
):
    """Test that ValueError is raised when dashboard is not found after import."""
    mock_settings.SUPERSET_DATABASE_UUID = "12345678-1234-1234-1234-123456789012"
    mock_create_zip.return_value = mock.MagicMock()
    mock_get_base_url.return_value = "http://superset.local"
    mock_get_session.return_value = mock.MagicMock()
    mock_import_dashboard.return_value = None
    mock_get_dashboard_by_title.return_value = None

    with pytest.raises(ValueError, match="Dashboard not found for title"):
        project_resources.provision_superset_dashboard.fn(
            project_id=123,
            project_name="Test project",
            project_namespace="project_id123",
        )


@mock.patch("phiphi.pipeline_jobs.project_resources.template.create_project_dashboard_zip")
@mock.patch("phiphi.pipeline_jobs.project_resources.config.settings")
def test_provision_superset_dashboard_template_failure(mock_settings, mock_create_zip):
    """Test Superset dashboard provisioning propagates template creation ValueError."""
    mock_settings.SUPERSET_DATABASE_UUID = "12345678-1234-1234-1234-123456789012"
    mock_create_zip.side_effect = ValueError("SUPERSET_DATABASE_SQLALCHEMY_URI is not configured")

    with pytest.raises(ValueError, match="SUPERSET_DATABASE_SQLALCHEMY_URI is not configured"):
        project_resources.provision_superset_dashboard.fn(
            project_id=123,
            project_name="Test project",
            project_namespace="project_id123",
        )


@mock.patch("phiphi.pipeline_jobs.project_resources.dashboard.import_dashboard")
@mock.patch("phiphi.pipeline_jobs.project_resources.client.get_authenticated_session")
@mock.patch("phiphi.pipeline_jobs.project_resources.client.get_base_url")
@mock.patch("phiphi.pipeline_jobs.project_resources.template.create_project_dashboard_zip")
@mock.patch("phiphi.pipeline_jobs.project_resources.config.settings")
def test_provision_superset_dashboard_import_failure(
    mock_settings,
    mock_create_zip,
    mock_get_base_url,
    mock_get_session,
    mock_import_dashboard,
):
    """Test Superset dashboard provisioning propagates import failure."""
    mock_settings.SUPERSET_DATABASE_UUID = "12345678-1234-1234-1234-123456789012"
    mock_create_zip.return_value = mock.MagicMock()
    mock_get_base_url.return_value = "http://superset.local"
    mock_get_session.return_value = mock.MagicMock()
    mock_import_dashboard.side_effect = superset_exceptions.SupersetAPIError(
        "Dashboard import failed", status_code=400
    )

    with pytest.raises(superset_exceptions.SupersetAPIError, match="Dashboard import failed"):
        project_resources.provision_superset_dashboard.fn(
            project_id=123,
            project_name="Test project",
            project_namespace="project_id123",
        )


@mock.patch("phiphi.pipeline_jobs.project_resources.link_superset_roles_to_dashboard")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_superset_roles")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_superset_dashboard")
@mock.patch("phiphi.pipeline_jobs.project_resources.update_project_resources_provisioned")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_prefect_rate_limits")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_bigquery_dataset")
def test_provision_project_resources_flow_with_superset_enabled(
    mock_provision_bigquery,
    mock_provision_rate_limits,
    mock_update_provisioned,
    mock_provision_superset,
    mock_provision_roles,
    mock_provision_dashboard_roles,
):
    """Test provisioning flow calls provision_superset_dashboard when provision_superset=True."""
    mock_provision_superset.return_value = 42
    mock_provision_roles.return_value = (10, 20)

    project_resources.provision_project_resources_flow.fn(
        project_id=123,
        project_name="Test project",
        project_namespace="project_id123",
        workspace_slug="main",
        provision_bigquery=False,
        provision_rate_limits=False,
        provision_superset=True,
    )

    mock_provision_bigquery.assert_not_called()
    mock_provision_rate_limits.assert_not_called()
    mock_provision_superset.assert_called_once_with(
        project_id=123,
        project_name="Test project",
        project_namespace="project_id123",
        logger=mock.ANY,
    )
    mock_provision_roles.assert_called_once_with(
        project_id=123,
        project_name="Test project",
        logger=mock.ANY,
    )
    mock_provision_dashboard_roles.assert_called_once_with(
        project_id=123,
        dashboard_id=42,
        view_role_id=10,
        logger=mock.ANY,
    )
    mock_update_provisioned.assert_called_once_with(
        project_id=123,
        dashboard_id=42,
        superset_view_role_id=10,
        superset_edit_role_id=20,
        logger=mock.ANY,
    )


@mock.patch("phiphi.pipeline_jobs.project_resources.provision_superset_dashboard")
@mock.patch("phiphi.pipeline_jobs.project_resources.update_project_resources_provisioned")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_prefect_rate_limits")
@mock.patch("phiphi.pipeline_jobs.project_resources.provision_bigquery_dataset")
def test_provision_project_resources_flow_superset_disabled(
    mock_provision_bq,
    mock_provision_rate_limits,
    mock_update_provisioned,
    mock_provision_superset,
):
    """Test provisioning flow skips provision_superset_dashboard when provision_superset=False."""
    project_resources.provision_project_resources_flow.fn(
        project_id=123,
        project_name="Test project",
        project_namespace="project_id123",
        workspace_slug="main",
        provision_bigquery=True,
        provision_rate_limits=True,
        provision_superset=False,
    )

    mock_provision_bq.assert_called_once()
    mock_provision_rate_limits.assert_called_once()
    mock_provision_superset.assert_not_called()
    mock_update_provisioned.assert_called_once_with(
        project_id=123,
        dashboard_id=None,
        superset_view_role_id=None,
        superset_edit_role_id=None,
        logger=mock.ANY,
    )


@mock.patch("phiphi.pipeline_jobs.project_resources.config.settings")
@mock.patch("phiphi.pipeline_jobs.project_resources.client.get_authenticated_session")
@mock.patch("phiphi.pipeline_jobs.project_resources.client.get_base_url")
def test_provision_superset_roles_missing_db_uuid(
    mock_get_base_url, mock_get_session, mock_settings
):
    """Test provision_superset_roles raises ValueError when DB UUID is missing."""
    mock_settings.SUPERSET_DATABASE_UUID = None
    mock_get_base_url.return_value = "http://superset.local"
    mock_get_session.return_value = mock.MagicMock()

    with pytest.raises(ValueError, match="SUPERSET_DATABASE_UUID is not configured"):
        project_resources.provision_superset_roles.fn(
            project_id=123,
            project_name="Test Project",
        )


@mock.patch("phiphi.superset.database.get_database_by_uuid")
@mock.patch("phiphi.pipeline_jobs.project_resources.config.settings")
@mock.patch("phiphi.pipeline_jobs.project_resources.client.get_authenticated_session")
@mock.patch("phiphi.pipeline_jobs.project_resources.client.get_base_url")
def test_provision_superset_roles_db_not_found(
    mock_get_base_url, mock_get_session, mock_settings, mock_get_db
):
    """Test provision_superset_roles raises ValueError when DB is not found."""
    mock_settings.SUPERSET_DATABASE_UUID = "test-uuid"
    mock_get_base_url.return_value = "http://superset.local"
    mock_get_session.return_value = mock.MagicMock()
    mock_get_db.return_value = None

    with pytest.raises(ValueError, match="Superset database with UUID test-uuid not found"):
        project_resources.provision_superset_roles.fn(
            project_id=123,
            project_name="Test Project",
        )


@mock.patch("phiphi.superset.roles.add_permissions_to_role")
@mock.patch("phiphi.superset.permissions.collect_datasource_access_permission_ids")
@mock.patch("phiphi.superset.database.get_database_by_uuid")
@mock.patch("phiphi.superset.roles.create_role")
@mock.patch("phiphi.pipeline_jobs.project_resources.config.settings")
@mock.patch("phiphi.pipeline_jobs.project_resources.client.get_authenticated_session")
@mock.patch("phiphi.pipeline_jobs.project_resources.client.get_base_url")
def test_provision_superset_roles_success(
    mock_get_base_url,
    mock_get_session,
    mock_settings,
    mock_create_role,
    mock_get_db,
    mock_collect_perms,
    mock_add_perms,
):
    """Test provision_superset_roles success path."""
    mock_settings.SUPERSET_DATABASE_UUID = "test-uuid"
    mock_get_base_url.return_value = "http://superset.local"
    mock_get_session.return_value = mock.MagicMock()
    mock_get_db.return_value = {"database_name": "Some OLAP Test"}
    mock_create_role.side_effect = [
        {"id": 10, "name": "View Role"},
        {"id": 20, "name": "Edit Role"},
    ]
    mock_collect_perms.return_value = [100, 101]

    view_role_id, edit_role_id = project_resources.provision_superset_roles.fn(
        project_id=123,
        project_name="Test Project",
    )

    assert view_role_id == 10
    assert edit_role_id == 20
    assert mock_create_role.call_count == 2

    mock_collect_perms.assert_called_once_with(
        db_name="Some OLAP Test",
        project_namespace="project_id123",
        table_names=superset_constants.DATASET_TABLES,
        logger=mock.ANY,
        base_url="http://superset.local",
        session=mock.ANY,
    )

    mock_add_perms.assert_called_once_with(
        role_id=20,
        permission_view_ids=[100, 101],
        base_url="http://superset.local",
        session=mock.ANY,
    )


@mock.patch("phiphi.pipeline_jobs.project_resources.dashboard.set_dashboard_roles")
@mock.patch("phiphi.pipeline_jobs.project_resources.client.get_authenticated_session")
@mock.patch("phiphi.pipeline_jobs.project_resources.client.get_base_url")
def test_provision_superset_dashboard_roles(
    mock_get_base_url,
    mock_get_session,
    mock_set_dashboard_roles,
):
    """Test link_superset_roles_to_dashboard calls set_dashboard_roles correctly."""
    mock_get_base_url.return_value = "http://superset.local"
    mock_get_session.return_value = mock.MagicMock()

    project_resources.link_superset_roles_to_dashboard.fn(
        project_id=123,
        dashboard_id=42,
        view_role_id=10,
    )

    mock_set_dashboard_roles.assert_called_once_with(
        dashboard_id=42,
        role_ids=[10],
        base_url="http://superset.local",
        session=mock.ANY,
    )
