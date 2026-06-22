"""Script to initialize Prefect environment."""

import argparse
import asyncio
import logging
import re

# No stubs for prefect_gcp
import prefect_gcp  # type: ignore[import-untyped]

from phiphi import config, constants, platform_db, prefect_deployments, utils
from phiphi.api import projects as api_projects
from phiphi.pipeline_jobs import projects as pipeline_projects

utils.init_logging()
utils.init_sentry()

logger = logging.getLogger(__name__)


async def init_storage_block() -> None:
    """Initialize the storage block by setting up a GCS bucket if specified in the configuration.

    Expects PREFECT_DEFAULT_RESULT_STORAGE_BLOCK in the format 'gcs-bucket/<bucket_name>'.
    """
    storage_block = config.settings.PREFECT_DEFAULT_RESULT_STORAGE_BLOCK
    logger.info(f"Storage block configuration: {storage_block}")

    if config.settings.CREATE_PREFECT_STORAGE_BLOCK_ON_INIT and storage_block:
        if storage_block.startswith("gcs-bucket/"):
            logger.info("Initializing GCS storage bucket...")

            # Extract the bucket name using regex
            match = re.match(r"^gcs-bucket/([^/]+)$", storage_block)
            if not match:
                raise ValueError("Invalid GCS bucket format in storage block configuration.")

            bucket_name = match.group(1)
            logger.info(f"Extracted bucket name: {bucket_name}")

            # Initialize the GCS bucket
            gcs_storage = prefect_gcp.GcsBucket(bucket=bucket_name)
            await gcs_storage.save(name=bucket_name, overwrite=True)
            logger.info(f"GCS bucket '{bucket_name}' initialized and saved.")
        else:
            raise ValueError("Unknown storage block format. Only 'gcs-bucket' is supported.")


async def reinit_all_project_concurrency_limits(
    offset: int | None = None, limit: int | None = None
) -> None:
    """Reinitialize the conncurrency limits for all projects.

    Retrieves all active project IDs and reinitializes Prefect
    concurrency limits for each project in parallel.
    """
    logger.info("Reinitializing per-project configuration...")

    with platform_db.get_session_context() as session:
        project_ids = api_projects.crud.get_all_active_project_ids(
            session, offset=offset, limit=limit
        )

    if not project_ids:
        logger.info("No active projects found to reinitialize.")
        return

    # Use gather with return_exceptions=True to ensure all tasks are attempted
    tasks = [pipeline_projects.init_prefect_concurrency(project_id) for project_id in project_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Process results to identify any failed tasks
    failed_projects = []
    for project_id, result in zip(project_ids, results):
        if isinstance(result, Exception):
            logger.error(f"Failed to initialize project {project_id}: {result}")
            failed_projects.append((project_id, str(result)))

    # Log the summary
    logger.info(
        "Reinitialization attempt complete for %d projects. Success: %d, Failed: %d",
        len(project_ids),
        len(project_ids) - len(failed_projects),
        len(failed_projects),
    )

    # If any projects failed, raise a consolidated exception
    if failed_projects:
        error_details = "\n".join([f"- Project {pid}: {error}" for pid, error in failed_projects])
        raise RuntimeError(
            f"Failed to reinitialize {len(failed_projects)} out of {len(project_ids)} "
            f"projects:\n{error_details}"
        )


async def main(image: str, reinit_all_project_concurrency_limits_flag: bool) -> None:
    """Initialize Prefect environment."""
    await init_storage_block()
    logger.info("Prefect deployments created.")
    # Should not create the deployments if the concurrency limits fails
    if reinit_all_project_concurrency_limits_flag:
        await reinit_all_project_concurrency_limits()
        logger.info("Reinitialized all project concurrency limits.")
    else:
        logger.info("Skipping reinitialization of project concurrency limits.")
    logger.info("Prefect initialization complete.")
    await prefect_deployments.create_all_deployments(image=image)


if __name__ == "__main__":
    logger.info("Running Prefect init...")
    parser = argparse.ArgumentParser(
        description="Init a prefect environment for PhiPhi", prog="PhiPhiPrefectInit"
    )
    parser.add_argument(
        "--image",
        default=constants.DEFAULT_IMAGE,
        help=("The image which will be ran when any of the Prefect deployments are run."),
    )
    parser.add_argument(
        "--reinit-all-project-concurrency-limits",
        action="store_true",
        help=("Reinitialize the concurrency limits for all projects."),
    )
    args = parser.parse_args()

    asyncio.run(
        main(
            image=args.image,
            reinit_all_project_concurrency_limits_flag=args.reinit_all_project_concurrency_limits,
        )
    )
