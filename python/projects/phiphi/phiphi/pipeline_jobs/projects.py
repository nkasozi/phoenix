"""Pipeline jobs for projects."""

import asyncio
import logging
from enum import Enum
from typing import Coroutine

import prefect
from google.cloud import bigquery

from phiphi import config, constants, platform_db, project_db, utils
from phiphi.api.projects import crud as project_crud
from phiphi.pipeline_jobs import constants as pipeline_constants
from phiphi.pipeline_jobs import tabulated_messages
from phiphi.pipeline_jobs.composite_flows import recompute_all_batches_tabulate_flow

utils.init_logging()

file_logger = logging.getLogger(__name__)


@prefect.task
def init_project_db(
    project_namespace: str,
    workspace_slug: str,
    with_dummy_data: bool = False,
    logger: logging.Logger = file_logger,
) -> str:
    """Initialize the project database.

    WARNING: if this is used in async code it must be awaited as Prefect does async magic.
    This task will be combined in to a flow to initialise other project resources.
    IE. superset dashboards.

    Args:
        project_namespace (str): The project namespace.
        workspace_slug (str): The workspace_slug.
        with_dummy_data (bool, optional): If True then dummy data will be seeded.
            Defaults to False.
        logger (logging.Logger, optional): The logger to use. Defaults to file_logger.

    Returns:
        str: The project namespace.
    """
    logger.info(f"Initializing project database for {project_namespace}.")
    project = utils.get_default_bigquery_project()
    client = bigquery.Client()
    # the dataset reference will use the default project or the project in the project_namespace if
    # has this in the string ie. <project_id>.<dataset_id>
    dataset_reference = bigquery.DatasetReference.from_string(
        dataset_id=project_namespace, default_project=project
    )
    dataset = bigquery.Dataset(dataset_reference)
    logger.debug(f"Creating dataset {project_namespace} in project {project}.")

    dataset.location = config.settings.BQ_DEFAULT_LOCATION
    dataset.labels = {"workspace_slug": workspace_slug}
    client.create_dataset(dataset=dataset, exists_ok=True)

    logger.debug(f"Dataset {project_namespace} created in project {project}.")

    with project_db.init_connection(
        project_db.form_bigquery_sqlalchmey_uri(project_namespace)
    ) as connection:
        logger.debug("Applying migrations to project database.")
        project_db.alembic_upgrade(connection)
        logger.debug(f"Applied migrations for {project_namespace}.")
        if with_dummy_data:
            logger.debug("Seeding dummy data for tabulated messages.")
            tabulated_messages.seed_dummy_data(project_namespace)
    logger.info(f"Project database {project_namespace} initialized.")
    return project_namespace


@prefect.task
def delete_project_db(
    project_namespace: str,
) -> None:
    """Delete the project database.

    Args:
        project_namespace (str): The project namespace.
    """
    client = bigquery.Client()
    client.delete_dataset(dataset=project_namespace, delete_contents=True, not_found_ok=True)


@prefect.task
def drop_downstream_tables(
    project_namespace: str,
) -> None:
    """Drop downstream tables.

    Currently this only drops the generalised_messages table as the rest of the tables are
    recreated with each pipeline.

    Args:
        project_namespace (str): The project namespace.
    """
    client = bigquery.Client()
    query = f"""
        DROP TABLE {project_namespace}.{pipeline_constants.GENERALISED_MESSAGES_TABLE_NAME}
    """
    client.query(query)
    return None


class RecomputeStrategy(str, Enum):
    """Recompute strategy enum."""

    always = "always"
    never = "never"
    on_upgrade = "on_upgrade"


@prefect.flow(name="project_apply_migrations")
async def project_apply_migrations(
    job_run_id: int,
    project_id: int,
    project_namespace: str,
    active_classifiers_versions: list[tuple[int, int]],
    with_recompute_all_batches: RecomputeStrategy = RecomputeStrategy.on_upgrade,
) -> bool:
    """Apply the migrations to the project database.

    If the migrations are applied successfully then the recompute_all_batches_tabulate_flow will be
    run.

    Args:
        job_run_id (int): The job run id.
        project_id (int): The project id.
        project_namespace (str): The project namespace.
        active_classifiers_versions (list[tuple[int, int]]): The active classifiers versions to
            use. Each tuple should be (classifier_id, version_id).
        with_recompute_all_batches (RecomputeStrategy, optional): The recompute strategy.
            Defaults to RecomputeStrategy.on_upgrade.
    """
    logger = prefect.get_run_logger()
    with project_db.init_connection(
        project_db.form_bigquery_sqlalchmey_uri(project_namespace)
    ) as connection:
        logger.info("Applying migrations.")
        revisions_applied = project_db.alembic_upgrade(connection)
        logger.info(f"Revisions applied: {revisions_applied}")
    if with_recompute_all_batches == RecomputeStrategy.always or (
        with_recompute_all_batches == RecomputeStrategy.on_upgrade and revisions_applied
    ):
        recompute_all_batches_tabulate_flow.recompute_all_batches_tabulate_flow(
            job_run_id=job_run_id,
            project_id=project_id,
            project_namespace=project_namespace,
            active_classifiers_versions=active_classifiers_versions,
            # It is important that we drop the downstream tables as the schemas of downstream
            # tables may have changed.
            drop_downstream_tables=True,
        )
        logger.info("Recompute all batches tabulate flow completed.")
    logger.info("Migrations applied.")
    return revisions_applied


@prefect.flow(name="apply_migrations_for_projects")
async def apply_migrations_for_projects(
    job_run_id: int,
    start: int = 0,
    end: int = 100,
) -> None:
    """Apply migrations for multiple projects in parallel.

    This function will fetch projects from the database using offset and limit,
    then run the `project_apply_migrations` flow in parallel for each project.

    Currently this is not complete and will not run the recompute_all_batches_tabulate_flow.

    Args:
        job_run_id: The overarching job run identifier.
        start: The offset to start fetching projects from the database.
        end: The limit to stop fetching projects from the database.

    Returns:
        None
    """
    logger = prefect.get_run_logger()

    # Fetch projects from database with offset and limit
    with platform_db.get_session_context() as session:
        projects = project_crud.get_all_projects(
            session=session,
            start=start,
            end=end,
            desc=False,
        )

    logger.info(f"Found {len(projects)} projects to process from {start} to {end}.")

    if not projects:
        logger.info("No projects found to process")
        return

    tasks = []
    for project in projects:
        project_id = project.id
        project_namespace = utils.get_project_namespace(project_id)
        logger.info(f"Processing project {project_id} with namespace {project_namespace}.")

        tasks.append(
            project_apply_migrations(
                job_run_id=job_run_id,
                project_id=project_id,
                project_namespace=project_namespace,
                active_classifiers_versions=[],  # Not needed unless recompute is done
                with_recompute_all_batches=RecomputeStrategy.never,
            )
        )

    # Run all tasks concurrently
    _ = await asyncio.gather(*tasks)


async def init_prefect_concurrency(
    project_id: int,
) -> None:
    """Initialize the prefect concurrency and rate limits for the project.

    This will create the rate limit for big query inserts per project namespace and table.
    Uses the limits as defined in the bigquery document of 5 per 10 seconds:
    https://cloud.google.com/bigquery/quotas#standard_tables
    """
    project_namespace = utils.get_project_namespace(project_id)
    # These tables are the ones that are inserted directly into
    tables = [
        pipeline_constants.GATHER_BATCHES_TABLE_NAME,
        pipeline_constants.GENERALISED_MESSAGES_TABLE_NAME,
        pipeline_constants.CLASSIFIED_MESSAGES_TABLE_NAME,
        pipeline_constants.CLASSIFIED_MESSAGES_ERRORS_TABLE_NAME,
    ]
    async with prefect.get_client() as client:
        for table in tables:
            name = utils.form_bq_rate_limit_write_id(project_namespace, table)
            limit = 5
            # 0.1 as to release a slot in 10 seconds (1.0 / 0.1)
            # https://orion-docs.prefect.io/latest/guides/global-concurrency-limits/?h=rate#slot-decay
            slot_decay_per_second = 0.1
            try:
                await client.read_global_concurrency_limit_by_name(name=name)
                await client.update_global_concurrency_limit(
                    name=name,
                    concurrency_limit=prefect.client.schemas.actions.GlobalConcurrencyLimitUpdate(
                        name=name,
                        active=True,
                        limit=limit,
                        slot_decay_per_second=slot_decay_per_second,
                        active_slots=0,
                    ),
                )
            except prefect.exceptions.ObjectNotFound:
                await client.create_global_concurrency_limit(
                    prefect.client.schemas.actions.GlobalConcurrencyLimitCreate(
                        name=name,
                        limit=limit,
                        slot_decay_per_second=slot_decay_per_second,
                    )
                )


def create_deployments(
    override_work_pool_name: str | None = None,
    deployment_name_prefix: str = "",
    image: str = constants.DEFAULT_IMAGE,
    tags: list[str] = [],
    build: bool = False,
    push: bool = False,
) -> list[Coroutine]:
    """Create deployments for projects.

    Args:
        override_work_pool_name (str | None): The name of the work pool to use to override the
        default work pool.
        deployment_name_prefix (str, optional): The prefix of the deployment name. Defaults to "".
        image (str, optional): The image to use for the deployments. Defaults to
        constants.DEFAULT_IMAGE.
        tags (list[str], optional): The tags to use for the deployments. Defaults to [].
        build (bool, optional): If True, build the image. Defaults to False.
        push (bool, optional): If True, push the image. Defaults to False.

    Returns:
        list[Coroutine]: List of coroutines that create deployments.
    """
    work_pool_name = str(constants.WorkPool.main)
    if override_work_pool_name:
        work_pool_name = override_work_pool_name
    tasks: list[Coroutine] = []
    flows_to_deploy: list[prefect.flows.Flow] = [
        project_apply_migrations,
        apply_migrations_for_projects,
    ]
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
