"""Module containing flow which combines classify (run single classifier), and tabulate flows."""

import asyncio
import typing

import prefect

from phiphi import constants
from phiphi.api.projects.job_runs import pipeline_job_result_schemas
from phiphi.pipeline_jobs.classify import flow as classify_flow
from phiphi.pipeline_jobs.tabulate import flow as tabulate_flow


@prefect.flow(name="classify_tabulate_flow")
async def classify_tabulate_flow(
    project_id: int,
    job_source_id: int,
    job_run_id: int,
    project_namespace: str,
    classifier_dict: dict,
    active_classifiers_versions: list[tuple[int, int]],
) -> pipeline_job_result_schemas.PipelineJobResult:
    """Flow which runs a classify, and tabulates all data."""
    await classify_flow.classify_flow(
        classifier_dict=classifier_dict,
        job_run_id=job_run_id,
        project_namespace=project_namespace,
    )

    tabulate_flow.tabulate_flow(
        job_run_id=job_run_id,
        project_namespace=project_namespace,
        active_classifiers_versions=active_classifiers_versions,
    )
    return pipeline_job_result_schemas.PipelineJobResult()


@prefect.flow(name="classify_all_tabulate_flow")
async def classify_all_tabulate_flow(
    project_id: int,
    job_source_id: int,
    job_run_id: int,
    project_namespace: str,
    classifiers_dict_list: list[dict],
    active_classifiers_versions: list[tuple[int, int]],
) -> pipeline_job_result_schemas.PipelineJobResult:
    """Flow which runs all classifiers, and tabulates all data."""
    prefect_logger = prefect.get_run_logger()
    prefect_logger.info(f"Starting classify_all_tabulate_flow for job_run_id={job_run_id}")

    classify_tasks: list[typing.Coroutine] = []
    for classifier_dict in classifiers_dict_list:
        # Running in parallel so that if we are going to run as classifier as a deployment in the
        # future it is an easy change. As well as it being a small optimisation.
        prefect_logger.info(
            "Scheduling classify_flow for classifier_id="
            f"{classifier_dict.get('id', 'unknown')} job_run_id={job_run_id}"
        )
        task = classify_flow.classify_flow(
            classifier_dict=classifier_dict,
            job_run_id=job_run_id,
            project_namespace=project_namespace,
        )
        classify_tasks.append(task)
    prefect_logger.info("Waiting for all classify tasks to complete")
    # Run all tasks (flows) concurrently and capture (and ignore) exceptions.
    # It is important that the gather is not deemed failed if a classifier fails.
    # As otherwise the user will think the gather has not been complete and will re-run.
    # We will find an other way to handle this in the future.
    _ = await asyncio.gather(*classify_tasks, return_exceptions=True)
    prefect_logger.info(f"Completed classify for job_run_id={job_run_id}")

    prefect_logger.info(f"Starting tabulate for job_run_id={job_run_id}")
    tabulate_flow.tabulate_flow(
        job_run_id=job_run_id,
        project_namespace=project_namespace,
        active_classifiers_versions=active_classifiers_versions,
    )
    prefect_logger.info(f"Completed tabulate for job_run_id={job_run_id}")
    return pipeline_job_result_schemas.PipelineJobResult()


def create_deployments(
    override_work_pool_name: str | None = None,
    deployment_name_prefix: str = "",
    image: str = constants.DEFAULT_IMAGE,
    tags: list[str] = [],
    build: bool = False,
    push: bool = False,
) -> list[typing.Coroutine]:
    """Create deployments for flow.

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
    coroutines = []
    task = classify_tabulate_flow.deploy(
        name=deployment_name_prefix + classify_tabulate_flow.name,
        work_pool_name=work_pool_name,
        image=image,
        build=build,
        push=push,
        tags=tags,
    )
    coroutines.append(task)

    task = classify_all_tabulate_flow.deploy(
        name=deployment_name_prefix + classify_all_tabulate_flow.name,
        work_pool_name=work_pool_name,
        image=image,
        build=build,
        push=push,
        tags=tags,
    )
    coroutines.append(task)

    return coroutines
