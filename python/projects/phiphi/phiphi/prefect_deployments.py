"""Deployments creation entry point.

To add new deployments, add the create_deployments function to variable
`list_of_create_deployment_fn`.
The functions in this list have the same interface as the CreateDeployments protocol.

This module can be run as a script to create deployments.

Example:
    $ python prefect_deployments.py
"""

import argparse
import asyncio
import logging
from typing import Coroutine, Protocol

from phiphi import constants, health_check_flows, platform_usage_analytics, utils
from phiphi.api.projects.job_runs import flow_runner_flow
from phiphi.pipeline_jobs import project_resources, projects
from phiphi.pipeline_jobs.classify import flow as classify_flow
from phiphi.pipeline_jobs.composite_flows import (
    classify_tabulate_flow,
    delete_gather_tabulate_flow,
    gather_classify_tabulate_flow,
    recompute_all_batches_tabulate_flow,
)
from phiphi.pipeline_jobs.gathers import flow as gather_flow
from phiphi.pipeline_jobs.tabulate import flow as tabulate_flow

utils.init_logging()
utils.init_sentry()

logger = logging.getLogger(__name__)


class CreateDeploymentsInterface(Protocol):
    """Protocol for create deployments functions."""

    def __call__(
        self,
        override_work_pool_name: str | None = None,
        deployment_name_prefix: str = "",
        image: str = constants.DEFAULT_IMAGE,
        tags: list[str] = [],
        build: bool = False,
        push: bool = False,
    ) -> list[Coroutine]:
        """Create deployments interface."""
        pass


list_of_create_deployment_fn: list[CreateDeploymentsInterface] = [
    health_check_flows.create_deployments,
    flow_runner_flow.create_deployments,
    gather_flow.create_deployments,
    classify_flow.create_deployments,
    tabulate_flow.create_deployments,
    gather_classify_tabulate_flow.create_deployments,
    delete_gather_tabulate_flow.create_deployments,
    classify_tabulate_flow.create_deployments,
    projects.create_deployments,
    project_resources.create_deployments,
    recompute_all_batches_tabulate_flow.create_deployments,
    platform_usage_analytics.create_deployments,
    # Add new create deployment functions here.
]


async def create_all_deployments(
    override_work_pool_name: str | None = None,
    deployment_name_prefix: str = "",
    image: str = constants.DEFAULT_IMAGE,
    tags: list[str] = [],
    build: bool = False,
    push: bool = False,
) -> None:
    """Create all deployments.

    Args:
        override_work_pool_name (str | None): The name of the work pool to use for deployments.
            In general each separate create_deployment function must have a default work pool.
        deployment_name_prefix (str, optional): The prefix of the deployment name. Defaults to "".
        image (str, optional): The image to use for the deployments. Defaults to
            constants.DEFAULT_IMAGE.
        tags (list[str], optional): The tags to use for the deployments. Defaults to [].
        build (bool, optional): If True, build the image. Defaults to False.
        push (bool, optional): If True, push the image. Defaults to False.
    """
    coroutines = []
    for create_deployment_coroutines in list_of_create_deployment_fn:
        coroutines.extend(
            create_deployment_coroutines(
                deployment_name_prefix=deployment_name_prefix,
                override_work_pool_name=override_work_pool_name,
                tags=tags,
                image=image,
                build=build,
                push=push,
            )
        )
    await asyncio.gather(*coroutines)


if __name__ == "__main__":
    logger.info("Running Prefect deployments...")
    parser = argparse.ArgumentParser(
        description="Create deployments for phiphi", prog="PhiphiDeploymentCreator"
    )
    # Currently image is the only argument that is used.
    # As we need others they should be added.
    parser.add_argument(
        "--image",
        default=constants.DEFAULT_IMAGE,
        help=("The image to use for the deployments."),
    )
    args = parser.parse_args()

    asyncio.run(
        create_all_deployments(
            image=args.image,
        )
    )
