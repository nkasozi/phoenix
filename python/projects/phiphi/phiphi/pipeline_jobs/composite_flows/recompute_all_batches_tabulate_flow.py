"""Recompute all batches and tabulate flow.

This flow is used to recompute all batches and tabulate the data.
"""

from typing import Coroutine, Optional

import prefect

from phiphi import constants
from phiphi.api.projects.job_runs import pipeline_job_result_schemas
from phiphi.config import settings
from phiphi.pipeline_jobs import projects
from phiphi.pipeline_jobs.gathers import deduplicate, normalise
from phiphi.pipeline_jobs.tabulate import flow as tabulate_flow


@prefect.flow(name="recompute_all_batches_tabulate_flow")
def recompute_all_batches_tabulate_flow(
    job_run_id: int,
    project_id: int,
    project_namespace: str,
    active_classifiers_versions: list[tuple[int, int]],
    drop_downstream_tables: bool = False,
    gather_ids: Optional[list[int]] = None,
    batch_of_batches_size: int = settings.DEFAULT_BATCH_OF_BATCHES_SIZE,
) -> pipeline_job_result_schemas.PipelineJobResult:
    """Flow that recomputes all batches and tabulates the data.

    Importantly this will not replace any metadata about the normalised batches. Ie `job_run_id`
    will be the original job_run_id from the gather not the new job_run_id.

    This will not run if there are no gather batches to recompute. This is important behaviour
    in that with the deletion of a PI data this will include the gather batches. If a recompute is
    run after a PI delete it will leave all tables and data as is.

    Args:
        job_run_id: The job run ID.
        project_id: The project ID.
        project_namespace: The project namespace.
        active_classifiers_versions (list[tuple[int, int]]): The active classifiers versions to
            use. Each tuple should be (classifier_id, version_id).
        drop_downstream_tables: If True, delete downstream tables. Defaults to False.
            This will also recompute the schemas for theses downstream tables.
        gather_ids: The gather IDs to recompute. If None, all gather IDs will be recomputed.
        batch_of_batches_size: The size of the batch of batches when normalising. Defaults to
            settings.DEFAULT_BATCH_OF_BATCHES_SIZE.
    """
    prefect_logger = prefect.get_run_logger()
    if drop_downstream_tables:
        prefect_logger.info("Dropping downstream tables.")
        projects.drop_downstream_tables(
            project_namespace=project_namespace,
        )

    gather_batches_metadata = normalise.get_gather_and_job_run_ids(
        bigquery_dataset=project_namespace,
        gather_ids=gather_ids,
    )
    prefect_logger.info(f"Found {len(gather_batches_metadata)} gather batches to recompute.")
    if len(gather_batches_metadata) == 0:
        return pipeline_job_result_schemas.PipelineJobResult()
    normalise_result = normalise.normalise_batches(
        gather_job_run_pairs=list(gather_batches_metadata.itertuples(index=False)),
        bigquery_dataset=project_namespace,
        batch_of_batches_size=batch_of_batches_size,
    )
    prefect_logger.info(
        f"Processed {normalise_result.total_processed} gather batches, successfully processed "
        f"{normalise_result.successfully_processed}, "
        f"and had {normalise_result.error_count} errors."
    )

    prefect_logger.info("Refreshing deduplicated messages tables.")
    deduplicate.refresh_deduplicated_messages_tables(
        bigquery_dataset=project_namespace,
    )
    deduplicate.refresh_deduplicated_authors_tables(
        bigquery_dataset=project_namespace,
    )
    prefect_logger.info("Tabulating data.")
    tabulate_flow.tabulate_flow(
        job_run_id=job_run_id,
        project_namespace=project_namespace,
        active_classifiers_versions=active_classifiers_versions,
    )
    prefect_logger.info("Recompute batches and tabulate flow completed.")
    return pipeline_job_result_schemas.PipelineJobResult()


def create_deployments(
    override_work_pool_name: str | None = None,
    deployment_name_prefix: str = "",
    image: str = constants.DEFAULT_IMAGE,
    tags: list[str] = [],
    build: bool = False,
    push: bool = False,
) -> list[Coroutine]:
    """Create deployments for recompute_all_batches_tabulate_flow.

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
    task = recompute_all_batches_tabulate_flow.deploy(
        name=deployment_name_prefix + recompute_all_batches_tabulate_flow.name,
        work_pool_name=work_pool_name,
        image=image,
        build=build,
        push=push,
        tags=tags,
    )

    return [task]
