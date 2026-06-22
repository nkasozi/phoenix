"""Pipeline jobs for provisioning project resources."""

import asyncio
import logging
from typing import Any, Coroutine

import prefect
from prefect import deployments
from prefect.client.schemas import objects

from phiphi import config, constants, platform_db, utils
from phiphi.api.projects import crud as project_crud
from phiphi.pipeline_jobs import projects as project_pipeline_jobs
from phiphi.superset import client, dashboard, database, permissions, roles, template
from phiphi.superset import constants as superset_constants

utils.init_logging()

file_logger = logging.getLogger(__name__)

# Deployment name for the provisioning flow
PROVISION_DEPLOYMENT_NAME = "provision_project_resources_flow/provision_project_resources_flow"


@prefect.task(
    retries=3,
    retry_delay_seconds=[60, 120, 300],  # 1min, 2min, 5min
)
def provision_bigquery_dataset(
    project_id: int,
    project_namespace: str,
    workspace_slug: str,
    with_dummy_data: bool = False,
    logger: logging.Logger = file_logger,
) -> str:
    """Provision BigQuery dataset for a project.

    This is a wrapper around init_project_db that can be conditionally called.

    Args:
        project_id: The project ID.
        project_namespace: The project namespace (e.g., "project_id123").
        workspace_slug: The workspace slug.
        with_dummy_data: If True, seed dummy data for tabulated messages.
        logger: Logger instance.

    Returns:
        The project namespace.
    """
    logger.info(f"Provisioning BigQuery dataset for project {project_id}")
    result = project_pipeline_jobs.init_project_db.fn(
        project_namespace=project_namespace,
        workspace_slug=workspace_slug,
        with_dummy_data=with_dummy_data,
        logger=logger,
    )
    logger.info(f"BigQuery dataset provisioned for project {project_id}")
    return result


@prefect.task()
def provision_superset_dashboard(
    project_id: int,
    project_name: str,
    project_namespace: str,
    logger: logging.Logger = file_logger,
) -> int:
    """Provision Superset dashboard for a project.

    Args:
        project_id: The project ID.
        project_name: The project name.
        project_namespace: The project namespace. (e.g., "project_id123").
        logger: Logger instance.

    Returns:
        The dashboard ID if successful.

    Raises:
        ValueError: If the imported dashboard is not found by its title.
    """
    logger.info(f"Provisioning Superset dashboard for project {project_id}")
    dashboard_zip = template.create_project_dashboard_zip(
        project_id=project_id,
        project_name=project_name,
        template_path=superset_constants.TEMPLATE_PATH,
        database_uuid=config.settings.SUPERSET_DATABASE_UUID,
    )

    base_url = client.get_base_url()
    session = client.get_authenticated_session(base_url=base_url)
    logger.info(f"Importing dashboard to {base_url=}")
    dashboard.import_dashboard(
        zip_file=dashboard_zip,
        overwrite=False,
        base_url=base_url,
        session=session,
    )
    title = template.get_dashboard_title(project_name=project_name, project_id=project_id)
    logger.info(f"Getting dashboard id for {title=}")
    result = dashboard.get_dashboard_by_title(title=title, base_url=base_url, session=session)
    if not result:
        raise ValueError(f"Dashboard not found for title: {title}")
    return int(result["id"])


@prefect.task()
def provision_superset_roles(
    project_id: int,
    project_name: str,
    logger: logging.Logger = file_logger,
) -> tuple[int, int]:
    """Provision Superset roles and permissions for a project dashboard.

    Args:
        project_id: The project ID.
        project_name: The project name.
        logger: Logger instance.

    Returns:
        Tuple of (view_role_id, edit_role_id).
    """
    logger.info(f"Provisioning Superset roles for project {project_id}")

    base_url = client.get_base_url()
    session = client.get_authenticated_session(base_url=base_url)

    dashboard_title = template.get_dashboard_title(project_name, project_id)
    view_role_name = template.get_superset_role_name(project_id, "View", dashboard_title)
    edit_role_name = template.get_superset_role_name(project_id, "Edit", dashboard_title)

    view_role = roles.create_role(view_role_name, base_url=base_url, session=session)
    view_role_id = view_role["id"]
    edit_role = roles.create_role(edit_role_name, base_url=base_url, session=session)
    edit_role_id = edit_role["id"]

    db_uuid = config.settings.SUPERSET_DATABASE_UUID
    if not db_uuid:
        raise ValueError("SUPERSET_DATABASE_UUID is not configured")

    db_name = database.get_database_name_by_uuid(db_uuid, base_url=base_url, session=session)
    project_namespace = utils.get_project_namespace(project_id)

    permission_view_ids = permissions.collect_datasource_access_permission_ids(
        db_name=db_name,
        project_namespace=project_namespace,
        table_names=superset_constants.DATASET_TABLES,
        logger=logger,
        base_url=base_url,
        session=session,
    )

    if permission_view_ids:
        roles.add_permissions_to_role(
            role_id=edit_role_id,
            permission_view_ids=permission_view_ids,
            base_url=base_url,
            session=session,
        )

    logger.info(f"Superset roles provisioned for project {project_id}")
    return view_role_id, edit_role_id


@prefect.task()
def link_superset_roles_to_dashboard(
    project_id: int,
    dashboard_id: int,
    view_role_id: int,
    logger: logging.Logger = file_logger,
) -> None:
    """Assign the view role to the dashboard's Roles access control section.

    Args:
        project_id: The project ID.
        dashboard_id: The dashboard ID.
        view_role_id: The Superset view-only role ID to assign.
        logger: Logger instance.
    """
    logger.info(
        f"Assigning view role {view_role_id} to dashboard {dashboard_id} for project {project_id}"
    )
    base_url = client.get_base_url()
    session = client.get_authenticated_session(base_url=base_url)
    dashboard.set_dashboard_roles(
        dashboard_id=dashboard_id,
        role_ids=[view_role_id],
        base_url=base_url,
        session=session,
    )
    logger.info(f"View role assigned to dashboard {dashboard_id} for project {project_id}")


@prefect.task(
    retries=3,
    retry_delay_seconds=[60, 120, 300],
)
def provision_prefect_rate_limits(
    project_id: int,
    logger: logging.Logger = file_logger,
) -> None:
    """Provision Prefect rate limits for BigQuery inserts.

    Args:
        project_id: The project ID.
        logger: Logger instance.
    """
    logger.info(f"Provisioning Prefect rate limits for project {project_id}")
    asyncio.run(project_pipeline_jobs.init_prefect_concurrency(project_id))
    logger.info(f"Prefect rate limits provisioned for project {project_id}")


@prefect.task
def update_project_resources_provisioned(
    project_id: int,
    dashboard_id: int | None,
    superset_view_role_id: int | None = None,
    superset_edit_role_id: int | None = None,
    logger: logging.Logger = file_logger,
) -> None:
    """Updates the project resources provisioned at a specific time.

    This function marks the given project as provisioned by updating its
    'project_resources_provisioned_at' timestamp. If a dashboard ID is provided,
    it associates the provisioning with the specified dashboard.

    Args:
        project_id (int): The ID of the project to be updated.
        dashboard_id (int or None): The ID of the dashboard associated with the
          provisioning. If None, provisioning superset wasn't enabled.
        superset_view_role_id: The Superset view-only role ID to persist.
        superset_edit_role_id: The Superset edit role ID to persist.
        logger : Logger instance.

    Returns:
        None
    """
    dashboard_log_str = f" with dashboard {dashboard_id}" if dashboard_id else ""
    logger.info(
        f"Updating project_resources_provisioned_at for project {project_id}{dashboard_log_str}"
    )
    with platform_db.get_session_context() as session:
        project_crud.set_project_resources_provisioned(
            session,
            project_id,
            dashboard_id,
            superset_view_role_id=superset_view_role_id,
            superset_edit_role_id=superset_edit_role_id,
        )
    logger.info(f"Project {project_id} marked as provisioned")


@prefect.flow(name="provision_project_resources_flow")
def provision_project_resources_flow(
    project_id: int,
    project_name: str,
    project_namespace: str,
    workspace_slug: str,
    with_dummy_data: bool = True,
    provision_bigquery: bool = True,
    provision_rate_limits: bool = True,
    provision_superset: bool = False,
) -> None:
    """Provision all external resources for a project.

    This flow provisions BigQuery dataset, Prefect rate limits, and optionally
    Superset dashboard for a project. Each provisioning step can be enabled/disabled
    via parameters.

    Args:
        project_id: The project ID.
        project_name: The project name.
        project_namespace: The project namespace (e.g., "project_id123").
        workspace_slug: The workspace slug.
        with_dummy_data: If True, seed dummy data in BigQuery.
        provision_bigquery: If True, provision BigQuery dataset.
        provision_rate_limits: If True, provision Prefect rate limits.
        provision_superset: If True, provision Superset dashboard.
    """
    logger = prefect.get_run_logger()
    logger.info(f"Starting resource provisioning for project {project_id}")

    # Provision BigQuery dataset
    if provision_bigquery:
        provision_bigquery_dataset(
            project_id=project_id,
            project_namespace=project_namespace,
            workspace_slug=workspace_slug,
            with_dummy_data=with_dummy_data,
            logger=logger,
        )

    # Provision Prefect rate limits
    if provision_rate_limits:
        provision_prefect_rate_limits(
            project_id=project_id,
            logger=logger,
        )

    # Provision Superset dashboard
    dashboard_id = None
    view_role_id = None
    edit_role_id = None
    if provision_superset:
        dashboard_id = provision_superset_dashboard(
            project_id=project_id,
            project_name=project_name,
            project_namespace=project_namespace,
            logger=logger,
        )
        view_role_id, edit_role_id = provision_superset_roles(
            project_id=project_id,
            project_name=project_name,
            logger=logger,
        )
        link_superset_roles_to_dashboard(
            project_id=project_id,
            dashboard_id=dashboard_id,
            view_role_id=view_role_id,
            logger=logger,
        )

    # Mark project as provisioned
    update_project_resources_provisioned(
        project_id=project_id,
        dashboard_id=dashboard_id,
        superset_view_role_id=view_role_id,
        superset_edit_role_id=edit_role_id,
        logger=logger,
    )

    logger.info(f"Resource provisioning completed for project {project_id}")


async def run_provision_deployment(
    parameters: dict[str, Any],
) -> objects.FlowRun:
    """Run the provisioning deployment.

    This wrapper exists to enable mocking in tests.

    Args:
        parameters: Parameters to pass to the flow.

    Returns:
        The FlowRun object.
    """
    flow_run: objects.FlowRun = await deployments.run_deployment(
        name=PROVISION_DEPLOYMENT_NAME,
        parameters=parameters,
        # Return immediately without waiting for completion
        timeout=0,
    )
    return flow_run


async def start_provision_deployment(
    project_id: int,
    project_name: str,
    project_namespace: str,
    workspace_slug: str,
    with_dummy_data: bool = True,
    provision_bigquery: bool = True,
    provision_rate_limits: bool = True,
    provision_superset: bool = False,
) -> objects.FlowRun:
    """Start the project resources provisioning deployment.

    Triggers the provisioning flow asynchronously via Prefect deployment.
    Returns immediately without waiting for the flow to complete.

    Args:
        project_id: The project ID.
        project_name: The project name.
        project_namespace: The project namespace (e.g., "project_id123").
        workspace_slug: The workspace slug.
        with_dummy_data: If True, seed dummy data in BigQuery.
        provision_bigquery: If True, provision BigQuery dataset.
        provision_rate_limits: If True, provision Prefect rate limits.
        provision_superset: If True, provision Superset dashboard.

    Returns:
        The FlowRun object from Prefect.
    """
    parameters = {
        "project_id": project_id,
        "project_name": project_name,
        "project_namespace": project_namespace,
        "workspace_slug": workspace_slug,
        "with_dummy_data": with_dummy_data,
        "provision_bigquery": provision_bigquery,
        "provision_rate_limits": provision_rate_limits,
        "provision_superset": provision_superset,
    }

    file_logger.info(f"Starting provisioning deployment for project {project_id}")
    flow_run = await run_provision_deployment(parameters)
    file_logger.info(
        f"Provisioning deployment started for project {project_id}, "
        f"flow_run_id={flow_run.id}, flow_run_name={flow_run.name}"
    )
    return flow_run


def create_deployments(
    override_work_pool_name: str | None = None,
    deployment_name_prefix: str = "",
    image: str = constants.DEFAULT_IMAGE,
    tags: list[str] = [],
    build: bool = False,
    push: bool = False,
) -> list[Coroutine]:
    """Create deployments for project resources provisioning.

    Args:
        override_work_pool_name: Override the default work pool name.
        deployment_name_prefix: Prefix for deployment names.
        image: Docker image to use.
        tags: Tags for the deployment.
        build: Whether to build the image.
        push: Whether to push the image.

    Returns:
        List of coroutines that create deployments.
    """
    work_pool_name = str(constants.WorkPool.main)
    if override_work_pool_name:
        work_pool_name = override_work_pool_name

    flows_to_deploy = [
        provision_project_resources_flow,
    ]

    tasks: list[Coroutine] = []
    for flow_to_deploy in flows_to_deploy:
        tasks.append(
            flow_to_deploy.deploy(
                name=deployment_name_prefix + flow_to_deploy.name,
                work_pool_name=work_pool_name,
                image=image,
                build=build,
                push=push,
                tags=tags,
            )
        )

    return tasks
