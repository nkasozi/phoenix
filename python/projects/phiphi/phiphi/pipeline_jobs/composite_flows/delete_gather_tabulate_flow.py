"""Module containing flow which combines delete gather, and tabulate flows."""

from typing import Coroutine

import prefect

from phiphi import constants
from phiphi.pipeline_jobs.gathers import flow as gather_flow
from phiphi.pipeline_jobs.tabulate import flow as tabulate_flow


@prefect.flow(name="delete_gather_tabulate_flow")
def delete_gather_tabulate_flow(
    project_id: int,
    job_source_id: int,
    job_run_id: int,
    project_namespace: str,
    active_classifiers_versions: list[tuple[int, int]],
) -> None:
    """Flow which deletes a gather's data, and tabulates all data."""
    gather_flow.delete_flow(
        gather_id=job_source_id,
        job_run_id=job_run_id,
        project_namespace=project_namespace,
    )

    tabulate_flow.tabulate_flow(
        job_run_id=job_run_id,
        project_namespace=project_namespace,
        active_classifiers_versions=active_classifiers_versions,
    )


def create_deployments(
    override_work_pool_name: str | None = None,
    deployment_name_prefix: str = "",
    image: str = constants.DEFAULT_IMAGE,
    tags: list[str] = [],
    build: bool = False,
    push: bool = False,
) -> list[Coroutine]:
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
    task = delete_gather_tabulate_flow.deploy(
        name=deployment_name_prefix + delete_gather_tabulate_flow.name,
        work_pool_name=work_pool_name,
        image=image,
        build=build,
        push=push,
        tags=tags,
    )

    return [task]
