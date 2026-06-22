"""Module containing flow which combines gather, run all classifiers, and tabulate flows."""

import typing

import prefect

from phiphi import constants
from phiphi.api.projects import gathers
from phiphi.api.projects.job_runs import pipeline_job_result_schemas
from phiphi.pipeline_jobs import constants as pipeline_jobs_constants
from phiphi.pipeline_jobs.composite_flows import classify_tabulate_flow
from phiphi.pipeline_jobs.gathers import flow as gather_flow


@prefect.flow(name="gather_classify_tabulate_flow")
async def gather_classify_tabulate_flow(
    project_id: int,
    job_source_id: int,
    job_run_id: int,
    project_namespace: str,
    gather_dict: dict,
    gather_child_type: gathers.schemas.ChildTypeName,
    classifiers_dict_list: list[dict],
    active_classifiers_versions: list[tuple[int, int]],
    max_mb_batch_size: float = pipeline_jobs_constants.DEFAULT_MAX_MB_BATCH_SIZE,
) -> pipeline_job_result_schemas.PipelineJobResult:
    """Flow which gathers, classifies, and tabulates data.

    Args:
        project_id (int): The project id.
        job_source_id (int): The job source id.
        job_run_id (int): The job run id.
        project_namespace (str): The project namespace.
        gather_dict (dict): Dictionary containing the gather parameters.
        gather_child_type (gathers.schemas.ChildTypeName): The type of gather.
        classifiers_dict_list (list[dict]): List of dictionaries containing the classifier
            parameters.
        active_classifiers_versions (list[tuple[int, int]]): List of tuples containing the
            classifier id and version id.
        max_mb_batch_size (float, optional): Maximum memory size in megabytes for each batch.
            Defaults to pipeline_jobs_constants.DEFAULT_MAX_MB_BATCH_SIZE.

    Returns:
        pipeline_job_result_schemas.GatherClassifyTabulatePipelineJobResult
            The pipeline job result.
    """
    prefect_logger = prefect.get_run_logger()
    prefect_logger.info(f"Starting gather_classify_tabulate_flow for job_run_id={job_run_id}")
    gather_pipeline_job_result = gather_flow.gather_flow(
        gather_dict=gather_dict,
        gather_child_type=gather_child_type,
        job_run_id=job_run_id,
        project_namespace=project_namespace,
        max_mb_batch_size=max_mb_batch_size,
    )
    prefect_logger.info(f"Completed gather for job_run_id={job_run_id}")

    _ = await classify_tabulate_flow.classify_all_tabulate_flow(
        project_id=project_id,
        job_source_id=job_source_id,
        job_run_id=job_run_id,
        project_namespace=project_namespace,
        classifiers_dict_list=classifiers_dict_list,
        active_classifiers_versions=active_classifiers_versions,
    )
    return pipeline_job_result_schemas.create_result(
        gather_job_result=gather_pipeline_job_result,
    )


def create_deployments(
    override_work_pool_name: str | None = None,
    deployment_name_prefix: str = "",
    image: str = constants.DEFAULT_IMAGE,
    tags: list[str] = [],
    build: bool = False,
    push: bool = False,
) -> list[typing.Coroutine]:
    """Create deployments for gather_classify_tabulate_flow.

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
    task = gather_classify_tabulate_flow.deploy(
        name=deployment_name_prefix + gather_classify_tabulate_flow.name,
        work_pool_name=work_pool_name,
        image=image,
        build=build,
        push=push,
        tags=tags,
    )

    return [task]
