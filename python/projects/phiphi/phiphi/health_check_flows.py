"""Health check flows."""

import dataclasses
from typing import Coroutine

import apify_client
import prefect
import sqlalchemy
from google.api_core import exceptions
from google.cloud import bigquery

from phiphi import config, constants, platform_db, utils


@dataclasses.dataclass
class HealthCheckResult:
    """Health check result."""

    check_sqlalchemy_connection_success: bool
    check_bigquery_connection_success: bool
    check_apify_connection_success: bool


@prefect.task
def check_sqlalchemy_connection() -> bool:
    """Check the SQLAlchemy connection to the database."""
    logger = prefect.get_run_logger()
    try:
        with platform_db.get_session_context() as session:
            # Doing a SELECT 1 to check the connection.
            select_query = sqlalchemy.select(1)
            response = session.execute(select_query)
            result = response.first()
            assert result
            assert result[0] == 1
        logger.info("Successfully connected to platform database.")
        return True
    except sqlalchemy.exc.SQLAlchemyError as e:
        logger.error(f"Failed to connect to platform database: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return False


@prefect.task
def check_bigquery_connection() -> bool:
    """Check the BigQuery connection."""
    logger = prefect.get_run_logger()
    if config.settings.USE_MOCK_BQ:
        logger.info("Using mock BigQuery.")
        return True
    try:
        client = bigquery.Client()
        datasets = list(client.list_datasets())
        if datasets:
            logger.info(f"Successfully connected to BigQuery. Found {len(datasets)} datasets.")
        else:
            logger.info("Successfully connected to BigQuery, but no datasets found.")
        return True
    except exceptions.GoogleAPIError as e:
        logger.error(f"Google API Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return False


@prefect.task
def check_apify_connection() -> bool:
    """Check the Apify connection."""
    logger = prefect.get_run_logger()
    if config.settings.USE_MOCK_APIFY:
        logger.info("Using mock Apify.")
        return True
    try:
        client = apify_client.ApifyClient(utils.get_apify_api_key())
        actors_collection = client.actors().list()
        actors_count = actors_collection.count
        actors = [item["name"] for item in actors_collection.items]
        if actors_count > 0:
            logger.info(f"Successfully connected to Apify. Found {actors_count} actors.")
            logger.info(f"Actors: {actors}")
        else:
            logger.info("Successfully connected to Apify, but no actors.")
        return True
    except apify_client.errors.ApifyClientError as e:
        logger.error(f"Apify Client Error: {e}")
    except apify_client.errors.ApifyApiError as e:
        logger.error(f"Apify API Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return False


@prefect.flow(name="health_check")
def health_check(workspace_slug: str | None) -> HealthCheckResult:
    """Runs a health check flow for the specified workspace.

    This function initiates a health check for the given workspace slug.
    It is designed to persist and return a `HealthCheckResult` object,
    allowing verification of the system's health status for the specified workspace.

    Args:
        workspace_slug (str | None): The slug of the workspace to check.
                                     If None, the flow defaults to a general health check.

    Returns:
        HealthCheckResult: An object containing the health check status and details.
    """
    logger = prefect.get_run_logger()
    logger.info("Health checks started.")

    check_sqlalchemy_connection_success = check_sqlalchemy_connection()
    check_bigquery_connection_success = check_bigquery_connection()
    check_apify_connection_success = check_apify_connection()

    assert all(
        [
            check_sqlalchemy_connection_success,
            check_bigquery_connection_success,
            check_apify_connection_success,
        ]
    )
    logger.info("Health checks completed.")
    prefect.events.emit_event(
        event="phoenix.health_check.completed",
        resource={"prefect.resource.id": f"phoenix.app_version.{config.settings.VERSION}"},
    )
    return HealthCheckResult(
        check_sqlalchemy_connection_success=check_sqlalchemy_connection_success,
        check_bigquery_connection_success=check_bigquery_connection_success,
        check_apify_connection_success=check_apify_connection_success,
    )


def create_deployments(
    override_work_pool_name: str | None = None,
    deployment_name_prefix: str = "",
    image: str = constants.DEFAULT_IMAGE,
    tags: list[str] = [],
    build: bool = False,
    push: bool = False,
) -> list[Coroutine]:
    """Create deployments for health check flows.

    By default the deployments are into the main work pool.

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
    workspace_slugs = [config.settings.FIRST_WORKSPACE_SLUG]
    coroutines = []
    for slug in workspace_slugs:
        task = health_check.deploy(
            name=deployment_name_prefix + "health_check-workspace-" + slug,
            work_pool_name=work_pool_name,
            image=image,
            build=build,
            push=push,
            tags=tags,
            parameters={"workspace_slug": slug},
        )
        coroutines.append(task)

    return coroutines
