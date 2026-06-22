"""Deployments grouped creation entry point.

This module can be run as a script to create grouped deployments. The group is passed as an
argument to the script. The script creates deployments for the given group by calling the
create_all_deployments function from the prefect_deployments module.

The deployments will have a name prefixed with the `{group_name}-`.

Example:
$ python create_grouped_deployments.py --group_name local --override_work_pool_name local-work-pool
"""

import argparse
import asyncio

from phiphi import constants, prefect_deployments


async def create_grouped_deployments(
    group_name: str,
    override_work_pool_name: str | None = None,
) -> None:
    """Create grouped deployments.

    The deployments that are created are prefixed with the group_name.
    """
    print(f"Creating deployments for group: {group_name}")
    print(f"Override work pool name: {override_work_pool_name}")
    await prefect_deployments.create_all_deployments(
        override_work_pool_name=override_work_pool_name,
        deployment_name_prefix=f"{group_name}-",
        image=constants.DEFAULT_IMAGE_REPO + f":{group_name}",
        tags=[group_name],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create grouped deployments for phiphi", prog="PhiphiGroupedDeploymentCreator"
    )
    parser.add_argument(
        "--group_name",
        required=True,
        help=(
            "The name of the group of deployments to create. "
            "If not provided, all deployments will be created."
        ),
    )
    parser.add_argument(
        "--override_work_pool_name",
        default=None,
        help="Override the default work pool for all deployments.",
    )

    args = parser.parse_args()

    asyncio.run(
        create_grouped_deployments(
            group_name=args.group_name,
            override_work_pool_name=args.override_work_pool_name,
        )
    )
