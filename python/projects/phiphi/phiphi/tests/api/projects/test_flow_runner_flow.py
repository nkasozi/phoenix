"""Test the flow_runner_flow."""

import unittest.mock as mock

import pytest
from prefect.client.schemas import objects

from phiphi import config
from phiphi.api.projects.job_runs import (
    crud,
    flow_runner_flow,
    pipeline_job_result_schemas,
    schemas,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "foreign_id,"
        "foreign_job_type,"
        "expected_deployment_name,"
        "mock_job_run_flow_result,"
        "expected_job_run_status,"
        "flow_run_result"
    ),
    [
        (
            2,
            schemas.ForeignJobType.gather,
            "gather_flow/gather_flow",
            True,
            schemas.Status.completed_successfully,
            # Result
            pipeline_job_result_schemas.PipelineJobResult(
                total_cost=1.0,
                gather_job_result=pipeline_job_result_schemas.GatherJobResult(
                    cost=1.0,
                    result_count=1,
                    normalise_total_processed=1,
                    normalise_successfully_processed=1,
                    normalise_error_count=2,
                ),
            ),
        ),
        (
            2,
            schemas.ForeignJobType.gather,
            "gather_flow/gather_flow",
            True,
            schemas.Status.completed_successfully,
            # Result with is_total_cost_estimated=True
            pipeline_job_result_schemas.PipelineJobResult(
                total_cost=1.0,
                is_total_cost_estimated=True,
                gather_job_result=pipeline_job_result_schemas.GatherJobResult(
                    cost=1.0,
                    result_count=1,
                    normalise_total_processed=1,
                    normalise_successfully_processed=1,
                    normalise_error_count=2,
                    is_cost_estimated=True,
                ),
            ),
        ),
        (
            2,
            schemas.ForeignJobType.gather,
            "gather_flow/gather_flow",
            False,
            schemas.Status.failed,
            # Prefect overrides the result to be a list of states if the flow has a return of None
            # What I think is really strange??
            [],
        ),
        (
            0,
            schemas.ForeignJobType.tabulate,
            "tabulate_flow/tabulate_flow",
            True,
            schemas.Status.completed_successfully,
            ["something"],
        ),
        (
            2,
            schemas.ForeignJobType.delete_gather,
            "delete_gather_flow/delete_gather_flow",
            True,
            schemas.Status.completed_successfully,
            None,
        ),
        (
            0,
            schemas.ForeignJobType.classify_all_tabulate,
            "classify_all_tabulate_flow/classify_all_tabulate_flow",
            True,
            schemas.Status.completed_successfully,
            None,
        ),
    ],
)
@mock.patch("prefect.deployments.run_deployment", new_callable=mock.AsyncMock)
async def test_flow_runner_flow(
    mock_start_flow_run,
    foreign_id,
    foreign_job_type,
    expected_deployment_name,
    mock_job_run_flow_result,
    expected_job_run_status,
    flow_run_result,
    session_context,
    reseed_tables,
):
    """Test the flow_runner_flow."""
    project_id = 1
    job_run_create = schemas.JobRunCreate(foreign_id=foreign_id, foreign_job_type=foreign_job_type)

    job_run = crud.create_job_run(
        session=session_context, project_id=project_id, job_run_create=job_run_create
    )

    mock_start_flow_state = mock.MagicMock()
    mock_start_flow_state.is_completed.return_value = mock_job_run_flow_result
    mock_start_flow_state.aresult = mock.AsyncMock(return_value=flow_run_result)

    assert job_run.status == schemas.Status.awaiting_start

    mock_return_start_flow_run = mock.MagicMock(spec=objects.FlowRun)
    mock_return_start_flow_run.id = "mock_uuid"
    mock_return_start_flow_run.name = "mock_start_flow_run"
    mock_return_start_flow_run.state = mock_start_flow_state
    mock_start_flow_run.return_value = mock_return_start_flow_run

    await flow_runner_flow.flow_runner_flow.fn(
        project_id=project_id,
        job_type=job_run.foreign_job_type,
        job_source_id=job_run.foreign_id,
        job_run_id=job_run.id,
    )

    # with the async functions it is very hard to test the arguments
    # so we just test that the functions were called
    mock_start_flow_run.assert_called_once()
    args = mock_start_flow_run.call_args.kwargs
    assert "name" in args
    assert args["name"] == expected_deployment_name
    assert args["timeout"] == config.settings.INNER_FLOW_TIMEOUT_SECS

    job_run_completed = crud.get_job_run(
        session=session_context, project_id=project_id, job_run_id=job_run.id
    )

    assert job_run_completed
    assert job_run_completed.id == job_run.id
    assert job_run_completed.status == expected_job_run_status
    assert job_run_completed.completed_at is not None
    if isinstance(flow_run_result, pipeline_job_result_schemas.PipelineJobResult):
        assert job_run_completed.total_cost == flow_run_result.total_cost
        assert job_run_completed.is_total_cost_estimated == flow_run_result.is_total_cost_estimated
        if isinstance(
            flow_run_result.gather_job_result, pipeline_job_result_schemas.GatherJobResult
        ):
            assert (
                job_run_completed.gather_result_count
                == flow_run_result.gather_job_result.result_count
            )
            assert (
                job_run_completed.gather_normalise_error_count
                == flow_run_result.gather_job_result.normalise_error_count
            )
    else:
        assert job_run_completed.total_cost == 0.0
        assert job_run_completed.gather_result_count is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "foreign_id, foreign_job_type",
    [
        (2, schemas.ForeignJobType.gather),
        (0, schemas.ForeignJobType.tabulate),
        (2, schemas.ForeignJobType.delete_gather),
    ],
)
@mock.patch(
    "phiphi.api.projects.job_runs.flow_runner_flow.flow_runner_flow", new_callable=mock.AsyncMock
)
async def test_create_and_start_job_run_flow(
    mock_flow_runner,
    foreign_id,
    foreign_job_type,
    session_context,
    reseed_tables,
):
    """Test that create_and_start_job_run_flow creates a job run and calls flow_runner_flow."""
    project_id = 1

    await flow_runner_flow.create_and_start_job_run_flow.fn(
        project_id=project_id,
        foreign_id=foreign_id,
        foreign_job_type=foreign_job_type,
    )

    mock_flow_runner.assert_called_once()
    call_kwargs = mock_flow_runner.call_args.kwargs
    assert call_kwargs["project_id"] == project_id
    assert call_kwargs["job_type"] == foreign_job_type
    assert call_kwargs["job_source_id"] == foreign_id

    # Verify the job run was created in the DB
    job_run_id = call_kwargs["job_run_id"]
    job_run = crud.get_job_run(
        session=session_context, project_id=project_id, job_run_id=job_run_id
    )
    assert job_run is not None
    assert job_run.foreign_id == foreign_id
    assert job_run.foreign_job_type == foreign_job_type
    assert job_run.status == schemas.Status.awaiting_start


@pytest.mark.asyncio
@mock.patch(
    "phiphi.api.projects.job_runs.flow_runner_flow.flow_runner_flow", new_callable=mock.AsyncMock
)
async def test_create_and_start_job_run_flow_exception(
    mock_flow_runner,
    session_context,
    reseed_tables,
):
    """Test create_and_start_job_run_flow when flow_runner_flow raises an exception."""
    project_id = 1
    foreign_id = 2
    foreign_job_type = schemas.ForeignJobType.gather

    mock_flow_runner.side_effect = Exception("Mock (correctly) triggered exception, for testing.")

    with pytest.raises(Exception):
        await flow_runner_flow.create_and_start_job_run_flow.fn(
            project_id=project_id,
            foreign_id=foreign_id,
            foreign_job_type=foreign_job_type,
        )

    # Job run should still have been created before the exception
    mock_flow_runner.assert_called_once()
    job_run_id = mock_flow_runner.call_args.kwargs["job_run_id"]
    job_run = crud.get_job_run(
        session=session_context, project_id=project_id, job_run_id=job_run_id
    )
    assert job_run is not None
    assert job_run.foreign_id == foreign_id
    assert job_run.foreign_job_type == foreign_job_type
    assert job_run.status == schemas.Status.failed
    assert job_run.completed_at is not None


@pytest.mark.asyncio
@mock.patch(
    "phiphi.api.projects.job_runs.flow_runner_flow.start_flow_run", new_callable=mock.AsyncMock
)
async def test_flow_runner_flow_exception(mock_start_flow_run, session_context, reseed_tables):
    """Test the flow_runner_flow if there is an exception."""
    project_id = 1
    gather_id = 2
    job_run_create = schemas.JobRunCreate(
        foreign_id=gather_id, foreign_job_type=schemas.ForeignJobType.gather
    )

    job_run = crud.create_job_run(
        session=session_context, project_id=project_id, job_run_create=job_run_create
    )

    mock_start_flow_run.side_effect = Exception(
        "Mock (correctly) triggered exception, for testing."
    )

    assert job_run.status == schemas.Status.awaiting_start

    with pytest.raises(Exception):
        await flow_runner_flow.flow_runner_flow(
            project_id=project_id,
            job_type=job_run.foreign_job_type,
            job_source_id=job_run.foreign_id,
            job_run_id=job_run.id,
        )

    job_run_completed = crud.get_job_run(
        session=session_context, project_id=project_id, job_run_id=job_run.id
    )

    assert job_run_completed
    assert job_run_completed.id == job_run.id
    assert job_run_completed.status == schemas.Status.failed
    assert job_run_completed.completed_at is not None
