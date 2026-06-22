"""Super simple dev flow just for deving the CICD etc working.

Will be deleted once real job flows are live.
"""

import asyncio

from prefect import flow, get_run_logger, runtime, task


@task
def log_flow_run_name() -> None:
    """Task to log the flow run name."""
    logger = get_run_logger()
    logger.info(f"Flow run name: {runtime.flow_run.name}")


@flow(name="dev_job_flow")
def dev_job_flow() -> None:
    """Super simple dev flow just for deving the CICD etc working."""
    log_flow_run_name()


if __name__ == "__main__":
    asyncio.run(
        dev_job_flow.deploy(
            name="main_deployment",
            work_pool_name="TODO",  # this should be the same work pool right?
            image="TODO",  # then try using another image for this (just a public one should be ok)
            tags=["TODO"],
            build=False,
        )
    )
