"""Module containing (outer) flow which runs jobs (inner flows) and records their status.

This flow is very hard to test due to the fact that it runs other flows via deployments. It is
possible to test manually locally with: ./run_test_flow_runner_flow.py. See file for more
information.
"""

import typing
import uuid

import prefect
import prefect.client.schemas.responses as responses
from google.api_core import exceptions as google_exceptions
from prefect.client.schemas import objects

from phiphi import (
    config,
    constants,
    platform_db,
    utils,
)
from phiphi.api.projects import job_runs
from phiphi.api.projects.job_runs import pipeline_job_params, pipeline_job_result_schemas, schemas


@prefect.task
async def start_flow_run(
    project_id: int,
    job_type: schemas.ForeignJobType,
    job_source_id: int,
    job_run_id: int,
) -> objects.FlowRun:
    """Start the (inner) flow for the job.

    Args:
        project_id: ID of the project.
        job_type: Type of job to run.
        job_source_id: ID of the source for the job. Corresponds to the table corresponding to
            job_type.
        job_run_id: ID of the row in the job_runs table.
    """
    project_namespace = utils.get_project_namespace(project_id=project_id)
    pipeline_job_parameters = pipeline_job_params.form(
        project_id=project_id,
        project_namespace=project_namespace,
        job_type=job_type,
        job_source_id=job_source_id,
        job_run_id=job_run_id,
    )

    job_variables = get_job_variables(
        deployment_name=pipeline_job_parameters.deployment_name,
        parameters=pipeline_job_parameters.parameters,
    )

    job_run_flow: objects.FlowRun = await prefect.deployments.run_deployment(
        name=pipeline_job_parameters.deployment_name,
        parameters=pipeline_job_parameters.parameters,
        as_subflow=True,
        timeout=config.settings.INNER_FLOW_TIMEOUT_SECS,
        tags=[
            f"project_id:{project_id}",
            f"job_type:{job_type}",
            f"job_source_id:{job_source_id}",
            f"job_run_id:{job_run_id}",
        ],
        job_variables=job_variables,
    )
    return job_run_flow


def get_job_variables(deployment_name: str, parameters: dict) -> dict:
    """Get the job variables from the parameters.

    Args:
        deployment_name (str): The name of the deployment.
        parameters (dict): The parameters passed to the flow.

    Returns:
        dict: The job variables.
    """
    if "gather_dict" not in parameters:
        return {}

    # Default resource requests and limits
    # Making the default for the memory as generally for all job this is enough.
    memory_limit = "2048Mi"
    memory_request = "2048Mi"
    cpu_request = "500m"
    cpu_limit = "2"

    # Default resource allocation
    gather_dict = parameters["gather_dict"]
    job_run_resource_estimate = gather_dict.get("job_run_resource_estimate", None)
    max_gather_result_count = 0
    if job_run_resource_estimate is not None:
        max_gather_result_count = job_run_resource_estimate.get("max_gather_result_count", 0)

    # Current above 10k results needs more memory
    if max_gather_result_count >= 10000:
        # Large: A t3.medium has 3919464ki
        # So using 85%: (3919464 * 0.85)/1024
        memory_limit = "3253Mi"
        memory_request = "3253Mi"
        cpu_request = "1"

    return {
        "resources": {
            "requests": {"memory": memory_request, "cpu": cpu_request},
            "limits": {"memory": memory_limit, "cpu": cpu_limit},
        }
    }


@prefect.task
def job_run_update_started(job_run_id: int) -> None:
    """Update the job_runs row with this (outer) flow's info and set job row status to started.

    Args:
        job_run_id: ID of the row in the job_runs table.
    """
    job_run_update_processing = schemas.JobRunUpdateProcessing(
        id=job_run_id,
    )
    with platform_db.get_session_context() as session:
        job_runs.crud.update_job_run(session=session, job_run_data=job_run_update_processing)


async def cancel_flow_run(flow_run_id: uuid.UUID, message: str) -> None:
    """Cancel an existing flow run by sending a cancellation request.

    Args:
        flow_run_id (uuid.UUID): The unique identifier for the flow run to cancel.
        message (str): A brief description or reason for canceling the flow run.

    Adapted from:
    https://github.com/PrefectHQ/prefect/blob/e04760780e1af1acddd68f00b69386431552514c/src/prefect/cli/flow_run.py#L201

    Note:
        Due to the complexity of the system, there is currently no dedicated Prefect integration
        test for this function. It has, however, been manually verified following the instructions
        in:
        python/projects/phiphi/docs/debugging_flows_locally.md
    """
    async with prefect.get_client() as client:
        # Cancel the flow run
        cancelling_state = prefect.states.State(type=objects.StateType.CANCELLED, message=message)
        result = await client.set_flow_run_state(flow_run_id=flow_run_id, state=cancelling_state)
        if result.status == responses.SetStateStatus.ABORT:
            raise Exception(f"Failed to cancel flow run with flow id: {flow_run_id=}")


@prefect.task
async def wait_for_job_flow_run(job_run_flow_id: uuid.UUID) -> objects.FlowRun:
    """Wait for the inner flow to complete and fetch the final state."""
    logger = prefect.get_run_logger()
    logger.info(f"Waiting for flow run to complete. {job_run_flow_id=}")
    timeout_secs = config.settings.INNER_FLOW_TIMEOUT_SECS
    try:
        flow_run_result: objects.FlowRun = await prefect.flow_runs.wait_for_flow_run(
            flow_run_id=job_run_flow_id,
            timeout=timeout_secs,
        )
    # This exception is different from the documentation but is in the source code:
    # https://github.com/PrefectHQ/prefect/blob/e04760780e1af1acddd68f00b69386431552514c/src/prefect/flow_runs.py#L127C11-L127C29
    except prefect.exceptions.FlowRunWaitTimeout:
        logger.error(f"Inner flow run timed out. {job_run_flow_id=}")
        await cancel_flow_run(
            flow_run_id=job_run_flow_id,
            message=f"Inner flow run timed out after seconds: {timeout_secs}",
        )
        raise Exception(f"Inner flow run timed out after seconds: {timeout_secs}")
    return flow_run_result


def get_status_from_flow_run(flow_run: objects.FlowRun) -> schemas.Status:
    """Get the job_runs status from the flow_run.

    This can't be a task other wise prefect will fail.
    """
    assert flow_run.state is not None
    if flow_run.state.is_completed():
        return schemas.Status.completed_successfully
    return schemas.Status.failed


async def get_result_from_flow_run(
    flow_run: objects.FlowRun,
) -> pipeline_job_result_schemas.PipelineJobResult:
    """Get the PipelineJobResult result from the flow_run.

    Be aware that this function requires that the persist of results for Prefect flows is correctly
    configured. See phiphi/config.py for more information.
    """
    prefect_logger = prefect.get_run_logger()
    # Needed for mypy
    assert flow_run.state is not None
    try:
        # There is a problem with the call overload of this function :( using ignore to get around
        # this.
        # We are using raise_on_failure as False because we are going to handle errors with
        # the status of the flow_run. Maybe in the future we will get more information about the
        # error from the result.
        result = await flow_run.state.aresult(raise_on_failure=False)
        if not isinstance(result, pipeline_job_result_schemas.PipelineJobResult):
            # Currently we don't handle any other return values from the inner flow.
            # Return Values from prefect flow can be hard to predict. For instance if the return
            # value is None then prefect will change this to be the states of the flow.
            return pipeline_job_result_schemas.PipelineJobResult()
        return result
    except prefect.exceptions.UnfinishedRun:
        # If it is not finished then we can consider it has been timed out and should be cancelled
        timeout_secs = config.settings.INNER_FLOW_TIMEOUT_SECS
        prefect_logger.error(f"Inner flow run timed out. {flow_run.id=}")
        await cancel_flow_run(
            flow_run_id=flow_run.id,
            message=f"Inner flow run timed out after seconds: {timeout_secs}",
        )
        raise Exception(f"Inner flow run timed out after seconds: {timeout_secs}")
    except google_exceptions.NotFound:
        # Due to a bug in prefect we have to catch the google exception rather then the missing
        # results
        prefect_logger.warn(
            "Missing result due to misconfiguration of Prefect results. "
            "See `flow_runner_flow.py` for more information."
        )
    except prefect.exceptions.MissingResult:
        prefect_logger.warn(
            "Missing result due to misconfiguration of Prefect results. "
            "See `flow_runner_flow.py` for more information."
        )
    return pipeline_job_result_schemas.PipelineJobResult()


@prefect.task
async def job_run_update_completed(
    job_run_id: int,
    status: schemas.Status,
    job_result: pipeline_job_result_schemas.PipelineJobResult,
) -> None:
    """Update the job_runs table with the final state of the job (the inner flow)."""
    gather_result_count = None
    gather_normalise_error_count = None
    if job_result.gather_job_result:
        gather_result_count = job_result.gather_job_result.result_count
        gather_normalise_error_count = job_result.gather_job_result.normalise_error_count
    job_run_update_completed = schemas.JobRunUpdateCompleted(
        id=job_run_id,
        status=status,
        total_cost=job_result.total_cost,
        gather_result_count=gather_result_count,
        gather_normalise_error_count=gather_normalise_error_count,
        is_total_cost_estimated=job_result.is_total_cost_estimated,
    )
    with platform_db.get_session_context() as session:
        job_runs.crud.update_job_run(session=session, job_run_data=job_run_update_completed)


def non_success_hook(
    flow: prefect.flows.Flow, flow_run: objects.FlowRun, state: objects.State
) -> None:
    """Hook to run when the flow fails."""
    job_run_id = flow_run.parameters["job_run_id"]
    job_run_update_completed = schemas.JobRunUpdateCompleted(
        id=job_run_id, status=schemas.Status.failed
    )
    with platform_db.get_session_context() as session:
        job_runs.crud.update_job_run(session=session, job_run_data=job_run_update_completed)


def create_and_run_non_success_hook(
    flow: prefect.flows.Flow, flow_run: objects.FlowRun, state: objects.State
) -> None:
    """Hook to run when create_and_start_job_run_flow fails."""
    prefect_logger = prefect.get_run_logger()
    job_run_id = flow_run.parameters.get("job_run_id")
    if job_run_id is None:
        prefect_logger.warn(
            "create_and_start_job_run_flow failed before job_run_id was available."
        )
        return
    job_run_update_completed = schemas.JobRunUpdateCompleted(
        id=job_run_id, status=schemas.Status.failed
    )
    with platform_db.get_session_context() as session:
        job_runs.crud.update_job_run(session=session, job_run_data=job_run_update_completed)


@prefect.flow(
    name="flow_runner_flow",
    on_failure=[non_success_hook],
    on_cancellation=[non_success_hook],
    on_crashed=[non_success_hook],
)
async def flow_runner_flow(
    project_id: int,
    job_type: schemas.ForeignJobType,
    job_source_id: int,
    job_run_id: int,
) -> None:
    """Flow which runs flow deployments and records their status.

    Args:
        project_id: ID of the project.
        job_type: Type of job to run.
        job_source_id: ID of the source for the job. I.e., if type is `gather` then
            `job_source_id` is the ID of the row in the gathers table.
        job_run_id: ID of the row in the job_runs table.
    """
    prefect_logger = prefect.get_run_logger()
    prefect_logger.info(
        f"Starting flow_runner_flow with {project_id=}, {job_type=}, "
        f"{job_source_id=}, {job_run_id=}"
    )
    if not config.settings.PREFECT_RESULTS_PERSIST_BY_DEFAULT:
        prefect_logger.warn(
            "Warning: PhiPhi may not be configured correctly and the update of job_runs with the "
            "results (return) values from flows may not work. "
            "Prefect results should be persisted for this to work correctly."
        )

    job_run_update_started(job_run_id=job_run_id)
    # There is an issue with prefect and mypy here so using ignore to get around this.
    job_run_flow: objects.FlowRun = await start_flow_run(  # type: ignore[assignment]
        project_id=project_id,
        job_type=job_type,
        job_source_id=job_source_id,
        job_run_id=job_run_id,
    )
    job_run_flow_result = job_run_flow.id
    prefect_logger.info(f"Inner flow run completed with id: {job_run_flow_result}")
    status = get_status_from_flow_run(flow_run=job_run_flow)
    job_result = await get_result_from_flow_run(flow_run=job_run_flow)
    prefect_logger.info(f"Status: {status}, Job result: {job_result}")
    # This await is needed or the test does not pass
    _ = await job_run_update_completed(job_run_id=job_run_id, status=status, job_result=job_result)


@prefect.flow(
    name="create_and_start_job_run_flow",
    on_failure=[create_and_run_non_success_hook],
    on_cancellation=[create_and_run_non_success_hook],
    on_crashed=[create_and_run_non_success_hook],
)
async def create_and_start_job_run_flow(
    project_id: int,
    foreign_id: int,
    foreign_job_type: schemas.ForeignJobType,
) -> None:
    """Flow that creates a job run in the DB and runs it via flow_runner_flow.

    Parameters match JobRunCreate but without estimated_total_cost.

    Args:
        project_id: ID of the project.
        foreign_id: The foreign table ID (e.g., gather_id).
        foreign_job_type: The type of job to run.
    """
    with platform_db.get_session_context() as session:
        job_run = job_runs.crud.create_job_run(
            session=session,
            project_id=project_id,
            job_run_create=schemas.JobRunCreate(
                foreign_id=foreign_id,
                foreign_job_type=foreign_job_type,
            ),
        )

    try:
        await flow_runner_flow(
            project_id=project_id,
            job_type=foreign_job_type,
            job_source_id=foreign_id,
            job_run_id=job_run.id,
        )
    except Exception:
        job_run_update_completed = schemas.JobRunUpdateCompleted(
            id=job_run.id, status=schemas.Status.failed
        )
        with platform_db.get_session_context() as session:
            job_runs.crud.update_job_run(session=session, job_run_data=job_run_update_completed)
        raise


def create_deployments(
    override_work_pool_name: str | None = None,
    deployment_name_prefix: str = "",
    image: str = constants.DEFAULT_IMAGE,
    tags: list[str] = [],
    build: bool = False,
    push: bool = False,
) -> list[typing.Coroutine]:
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
    work_pool_name = str(constants.WorkPool.main)
    if override_work_pool_name:
        work_pool_name = override_work_pool_name
    coroutines = []
    task = flow_runner_flow.deploy(
        name=deployment_name_prefix + flow_runner_flow.name,
        work_pool_name=work_pool_name,
        work_queue_name="flow_runner_flow_queue",
        image=image,
        build=build,
        push=push,
        tags=tags,
    )

    coroutines.append(task)

    task = create_and_start_job_run_flow.deploy(
        name=deployment_name_prefix + create_and_start_job_run_flow.name,
        work_pool_name=work_pool_name,
        work_queue_name="flow_runner_flow_queue",
        image=image,
        build=build,
        push=push,
        tags=tags,
    )
    coroutines.append(task)

    return coroutines
