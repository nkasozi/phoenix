"""Gather run functionality."""

import sqlalchemy.orm

from phiphi import config
from phiphi.api import exceptions
from phiphi.api.projects import schemas as project_schemas
from phiphi.api.projects.gathers import child_crud, child_types
from phiphi.api.projects.job_runs import crud as job_run_crud
from phiphi.api.projects.job_runs import schemas as job_run_schemas

NO_REMAINING_CREDITS = "You have no remaining credits for this project."
ESTIMATE_OVER_REMAINING_CREDITS = (
    "The estimated cost of this gather exceeds the remaining credits for this project."
)

ESTIMATE_INCLUDING_RUNNING_GATHERS_OVER_REMAINING_CREDITS = (
    "The estimated cost of this gather exceeds the project's remaining credits, "
    "including the estimated cost of currently running gathers. "
    "Please wait for other running gathers to complete."
)

DEFAULT_GATHER_RUN_JOB_TYPE = job_run_schemas.ForeignJobType.gather_classify_tabulate


def cost_credits_guard(
    project_detail: project_schemas.ProjectDetail,
    gather: child_types.AllChildTypesUnion,
) -> None:
    """Guard to the costs and credits of the project."""
    if project_detail.has_unlimited_credits:
        return

    if project_detail.total_costs >= project_detail.total_allocated_credits:
        raise exceptions.Forbidden(NO_REMAINING_CREDITS)

    estimate_with_error_margin = (
        gather.job_run_resource_estimate.max_total_cost
        * config.settings.GATHER_COST_ESTIMATE_ERROR_MARGIN
    )

    estimated_total_cost = estimate_with_error_margin + project_detail.total_costs

    if estimated_total_cost > project_detail.total_allocated_credits:
        raise exceptions.Forbidden(ESTIMATE_OVER_REMAINING_CREDITS)

    estimated_total_cost_with_running_job_runs = (
        estimate_with_error_margin + project_detail.estimated_total_costs
    )
    if estimated_total_cost_with_running_job_runs > project_detail.total_allocated_credits:
        raise exceptions.Forbidden(ESTIMATE_INCLUDING_RUNNING_GATHERS_OVER_REMAINING_CREDITS)

    return


async def run_gather_job_run_with_costs_guard(
    session: sqlalchemy.orm.Session,
    project_id: int,
    gather_id: int,
    project_detail: project_schemas.ProjectDetail,
) -> child_types.AllChildTypesUnion:
    """Create a gather job run and run it.

    Args:
        session: The database session.
        project_id: The project id.
        gather_id: The gather id.
        project_detail: The project detail schema.
    """
    gather = child_crud.get_child_gather(session, project_id, gather_id)
    if gather is None:
        raise exceptions.GatherNotFound()

    cost_credits_guard(
        project_detail,
        gather,
    )

    _ = await job_run_crud.create_and_run_job_run(
        session,
        project_id,
        job_run_schemas.JobRunCreate(
            foreign_id=gather_id,
            foreign_job_type=job_run_schemas.ForeignJobType.gather_classify_tabulate,
            estimated_total_cost=gather.job_run_resource_estimate.max_total_cost,
        ),
    )

    gather = child_crud.get_child_gather(session, project_id, gather_id)
    # This should never happen but needed for the mypy
    assert gather is not None
    return gather
