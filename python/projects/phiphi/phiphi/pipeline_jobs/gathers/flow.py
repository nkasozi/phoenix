"""Module containing the Prefect flow for gathers."""

import logging
from typing import Coroutine

import prefect

from phiphi import constants
from phiphi.api.projects import gathers
from phiphi.api.projects.gathers.manual_upload import schemas as manual_upload_schemas
from phiphi.api.projects.job_runs import pipeline_job_result_schemas
from phiphi.config import settings
from phiphi.pipeline_jobs import constants as pipeline_jobs_constants
from phiphi.pipeline_jobs import dataframe_writers
from phiphi.pipeline_jobs.gathers import (
    apify,
    danek,
    deduplicate,
    delete,
    gather_batch_write_managers,
    manual_upload,
    normalise,
    selectors,
)
from phiphi.pipeline_jobs.gathers import types as gather_types

DANEK_CHILD_TYPES = [
    gathers.schemas.ChildTypeName.danek_facebook_searches_posts,
    gathers.schemas.ChildTypeName.danek_instagram_posts,
    gathers.schemas.ChildTypeName.danek_instagram_comments,
]

APIFY_X_CHILD_TYPES = [
    gathers.schemas.ChildTypeName.apify_x_advanced_searches_posts_comments,
    gathers.schemas.ChildTypeName.apify_x_simple_searches_posts_comments,
]


@prefect.task
def scrape_and_write(
    gather: gathers.schemas.GatherChildResponseBase,
    gather_child_type: gathers.schemas.ChildTypeName,
    job_run_id: int,
    project_namespace: str,
    max_mb_batch_size: float = pipeline_jobs_constants.DEFAULT_MAX_MB_BATCH_SIZE,
    batch_of_batches_size: int = settings.DEFAULT_BATCH_OF_BATCHES_SIZE,
) -> gather_types.ScrapeResponse:
    """Scrape and write the gathered data and return the number of items scraped."""
    prefect_logger = prefect.get_run_logger()
    write_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=gather.id,
            job_run_id=job_run_id,
            gather_type=gather_child_type,
        ),
        df_writer=dataframe_writers.BigQueryDataFrameWriter(
            dataset=project_namespace,
            table=pipeline_jobs_constants.GATHER_BATCHES_TABLE_NAME,
        ),
        max_mb_batch_size=max_mb_batch_size,
    )
    if isinstance(gather, manual_upload_schemas.ManualUploadGatherResponse):
        # To be refactored to use the write_manager
        return manual_upload.write_manual_upload_to_gather_batches(
            manual_upload_gather=gather,
            write_manager=write_manager,
        )
    elif gather_child_type in DANEK_CHILD_TYPES:
        scrape_cost = danek.scrape.danek_scrape(
            gather=gather,
            write_manager=write_manager,
            logger=prefect_logger,
        )
    elif gather_child_type in APIFY_X_CHILD_TYPES:
        scrape_cost = apify.scrape.apify_scrape_batched_and_add_to_write_manager(
            gather=gather,
            write_manager=write_manager,
            batch_attr_name="search_list",
            # The batch size must be 1 so that the limit per search is respected and done correctly
            batch_size=1,
            logger=prefect_logger,
        )
    else:
        scrape_cost = apify.scrape.apify_scrape_and_add_to_write_manager(
            gather=gather,
            write_manager=write_manager,
            logger=prefect_logger,
        )
    # Important to call complete_write to ensure all data is written
    prefect_logger.info("Final write after scrape called.")
    manager_results = write_manager.complete_write()
    prefect_logger.info("Finished scraping.")
    prefect_logger.info(f"Batches inserted: {manager_results.total_batches_processed}.")
    prefect_logger.info(f"Items scraped: {manager_results.total_items_processed}.")
    return gather_types.ScrapeResponse(
        total_items=manager_results.total_items_processed,
        total_batches=manager_results.total_batches_processed,
        total_cost=scrape_cost.cost,
        is_cost_estimated=scrape_cost.is_cost_estimated,
    )


@prefect.flow(name="gather_flow")
def gather_flow(
    gather_dict: dict,
    gather_child_type: gathers.schemas.ChildTypeName,
    job_run_id: int,
    project_namespace: str,
    max_mb_batch_size: float = pipeline_jobs_constants.DEFAULT_MAX_MB_BATCH_SIZE,
    batch_of_batches_size: int = settings.DEFAULT_BATCH_OF_BATCHES_SIZE,
) -> pipeline_job_result_schemas.GatherJobResult:
    """Flow which gathers data.

    Args:
        gather_dict (dict): Dictionary containing the gather parameters.
        gather_child_type (gathers.schemas.ChildTypeName): The type of gather.
        job_run_id (int): The job run id.
        project_namespace (str): The project namespace.
        max_mb_batch_size (float, optional): Maximum memory size in megabytes for each batch.
            Defaults to pipeline_jobs_constants.DEFAULT_MAX_MB_BATCH_SIZE. Note that one batch
            is written to one row in BigQuery, and BQ has a row size limit of 10MB.
        batch_of_batches_size (int, optional): The number of batches to read and process at once
            when normalising.

    Warning: there is a race condition in this flow for the deduplicate step if multiple gathers
    flow are being run at the same time. Very unlikely though.
    """
    prefect_logger = prefect.get_run_logger()
    # Create the gather object from the gather_dict as prefect can't parse it automatically from
    # the parameters. Optionally None now for mypy to accept its use in chaining of multiple
    # gather flows
    root_gather: gathers.schemas.GatherChildResponseBase = gathers.child_types.get_response_type(
        gather_child_type
    )(**gather_dict)

    current_gather: gathers.schemas.GatherChildResponseBase | None = root_gather
    results: list[pipeline_job_result_schemas.GatherJobResult] = []
    gather_history: list[gathers.schemas.GatherChildResponseBase] = []
    while current_gather is not None:
        gather_history.append(current_gather)
        gather_response = run_single_gather(
            current_gather,
            job_run_id,
            max_mb_batch_size,
            prefect_logger,
            project_namespace,
            batch_of_batches_size,
        )
        results.append(gather_response)
        current_gather = get_next_gather_flow_params(
            root_gather, job_run_id, prefect_logger, project_namespace, results, gather_history
        )
    aggregated_gather_response = aggregate_gather_job_results(results)
    return aggregated_gather_response


def get_next_gather_flow_params(
    root_gather: gathers.schemas.GatherChildResponseBase,
    job_run_id: int,
    prefect_logger: logging.Logger | logging.LoggerAdapter,
    project_namespace: str,
    results: list[pipeline_job_result_schemas.GatherJobResult],
    previous_gathers: list[gathers.schemas.GatherChildResponseBase],
) -> gathers.schemas.GatherChildResponseBase | None:
    """Get next gather based on previous gather.

    Args:
        root_gather (gathers.schemas.GatherChildResponseBase): The initial gather sent by the user.
        job_run_id (int): The job run id.
        prefect_logger (logging.Logger | logging.LoggerAdapter): The prefect logger.
        project_namespace (str): The project namespace.
        results: list[pipeline_job_result_schemas.GatherJobResult]: list of previous results of
            gathers
        previous_gathers: list[gathers.schemas.GatherChildResponseBase]: Sequential list of
            previously executed gathers.

    """
    latest_gather = previous_gathers[-1]
    if isinstance(
        latest_gather,
        gathers.danek_instagram_posts.schemas.DanekInstagramPostsGatherResponse,
    ):
        if latest_gather.scrape_comments_count_per_post > 0:
            prefect_logger.info(
                f"Selecting ig posts with comments for gather_id={latest_gather.id}, "
                f"job_run_id={job_run_id}, "
                f"project_namespace={project_namespace}, "
                f"gather_type={latest_gather.child_type.value}"
            )
            post_id_list = selectors.get_post_ids_with_comments(
                bigquery_dataset=project_namespace,
                gather_id=latest_gather.id,
                gather_type=latest_gather.child_type,
            )
            prefect_logger.info(
                f"Selector returned {len(post_id_list)} post_ids for gather_id={latest_gather.id}"
            )
            if not post_id_list:
                prefect_logger.info(
                    f"No posts with comments found for gather_id = {latest_gather.id}."
                    " Skipping comments gather."
                )
                return None
            gather = gathers.danek_instagram_comments.schemas.DanekInstagramCommentsGatherResponse(
                name=latest_gather.name,
                id=latest_gather.id,
                created_at=latest_gather.created_at,
                updated_at=latest_gather.updated_at,
                project_id=latest_gather.project_id,
                latest_job_run=latest_gather.latest_job_run,
                delete_job_run=latest_gather.delete_job_run,
                child_type=gathers.schemas.ChildTypeName.danek_instagram_comments,
                post_id_list=post_id_list,
                limit_comments_per_post=latest_gather.scrape_comments_count_per_post,
                limit_child_comments_per_comment=latest_gather.limit_child_comments_per_comment,
            )
            return gather

    return None


def aggregate_gather_job_results(
    job_results: list[pipeline_job_result_schemas.GatherJobResult],
) -> pipeline_job_result_schemas.GatherJobResult:
    """Aggregate gather job results.

    Args:
        job_results (list[pipeline_job_result_schemas.GatherJobResult]):
            List of individual gather job results to aggregate.

    Returns:
        pipeline_job_result_schemas.GatherJobResult: The aggregated gather job results.
    """
    if not job_results:
        raise ValueError("No job results to aggregate. This indicates no gathers were executed.")

    total_cost = 0.0
    is_cost_estimated = False

    total_result_count = 0
    total_normalise_processed = 0
    total_normalise_success = 0
    total_normalise_errors = 0

    for result in job_results:
        # Cost handling
        if result.cost is not None:
            total_cost += result.cost

        # If any part is estimated → overall is estimated
        is_cost_estimated = is_cost_estimated or result.is_cost_estimated

        # Counters
        total_result_count += result.result_count
        total_normalise_processed += result.normalise_total_processed
        total_normalise_success += result.normalise_successfully_processed
        total_normalise_errors += result.normalise_error_count

    return pipeline_job_result_schemas.GatherJobResult(
        cost=total_cost,
        result_count=total_result_count,
        normalise_total_processed=total_normalise_processed,
        normalise_successfully_processed=total_normalise_success,
        normalise_error_count=total_normalise_errors,
        is_cost_estimated=is_cost_estimated,
    )


@prefect.flow(name="run_single_gather")
def run_single_gather(
    gather: gathers.schemas.GatherChildResponseBase,
    job_run_id: int,
    max_mb_batch_size: float,
    prefect_logger: logging.Logger | logging.LoggerAdapter,
    project_namespace: str,
    batch_of_batches_size: int,
) -> pipeline_job_result_schemas.GatherJobResult:
    """Run a single gather job."""
    gather_child_type = gather.child_type
    prefect_logger.info(f"Gathering data for {gather_child_type} and id {gather.id}.")
    scrape_response = scrape_and_write(
        gather=gather,
        gather_child_type=gather_child_type,
        job_run_id=job_run_id,
        project_namespace=project_namespace,
        max_mb_batch_size=max_mb_batch_size,
        batch_of_batches_size=batch_of_batches_size,
    )

    prefect_logger.info(
        f"Scraped {scrape_response.total_items} items for {gather_child_type} and id {gather.id}."
        f" Total cost: {scrape_response.total_cost}."
    )
    normalise_result = normalise.normalise_batches(
        gather_job_run_pairs=[(gather.id, job_run_id)],
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
    prefect_logger.info("Refreshing deduplicated authors tables.")
    deduplicate.refresh_deduplicated_authors_tables(
        bigquery_dataset=project_namespace,
    )
    return pipeline_job_result_schemas.GatherJobResult(
        cost=scrape_response.total_cost,
        result_count=scrape_response.total_items,
        normalise_total_processed=normalise_result.total_processed,
        normalise_successfully_processed=normalise_result.successfully_processed,
        normalise_error_count=normalise_result.error_count,
        is_cost_estimated=scrape_response.is_cost_estimated,
    )


@prefect.flow(name="delete_gather_flow")
def delete_flow(
    gather_id: int,
    # To be consistent with other flows we keep the job_run_id even though it is not used.
    job_run_id: int,
    project_namespace: str,
) -> None:
    """Flow which deletes gathered data."""
    delete.delete_gathered_data(
        gather_id=gather_id,
        bigquery_dataset=project_namespace,
    )
    deduplicate.refresh_deduplicated_messages_tables(
        bigquery_dataset=project_namespace,
    )
    deduplicate.refresh_deduplicated_authors_tables(
        bigquery_dataset=project_namespace,
    )


def create_deployments(
    override_work_pool_name: str | None = None,
    deployment_name_prefix: str = "",
    image: str = constants.DEFAULT_IMAGE,
    tags: list[str] | None = None,
    build: bool = False,
    push: bool = False,
) -> list[Coroutine]:
    """Create deployments for flow_runner_flow.

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
    if tags is None:
        tags = []
    work_pool_name = str(constants.WorkPool.main)
    if override_work_pool_name:
        work_pool_name = override_work_pool_name
    task = gather_flow.deploy(
        name=deployment_name_prefix + gather_flow.name,
        work_pool_name=work_pool_name,
        image=image,
        build=build,
        push=push,
        tags=tags,
    )

    task_2 = delete_flow.deploy(
        name=deployment_name_prefix + delete_flow.name,
        work_pool_name=work_pool_name,
        image=image,
        build=build,
        push=push,
        tags=tags,
    )

    return [task, task_2]
