"""Crud functionality for job runs."""

import logging
from datetime import datetime
from typing import Union

from sqlalchemy import func
from sqlalchemy.orm import Session

from phiphi.api import exceptions
from phiphi.api.projects.job_runs import models, prefect_deployment, schemas

logger = logging.getLogger(__name__)


def invalid_foreign_object_guard(
    session: Session, project_id: int, foreign_id: int, foreign_job_type: schemas.ForeignJobType
) -> None:
    """Guard to check if the foreign object exists."""
    if foreign_job_type == schemas.ForeignJobType.tabulate and foreign_id != 0:
        raise exceptions.HttpException400("Tabulate must have a foreign_id of 0")

    latest_job_run = get_latest_job_run(session, project_id, foreign_id, foreign_job_type)
    if latest_job_run and not latest_job_run.completed_at:
        raise exceptions.ForeignObjectHasActiveJobRun(foreign_id, str(foreign_job_type))


def create_job_run(
    session: Session,
    project_id: int,
    job_run_create: schemas.JobRunCreate,
) -> schemas.JobRunResponse:
    """Create a new job run.

    For the guards based on the project to be run the project detail must be provided.

    Args:
        session: The database session.
        project_id: The project id.
        job_run_create: The job run create schema.
    """
    invalid_foreign_object_guard(
        session, project_id, job_run_create.foreign_id, job_run_create.foreign_job_type
    )
    orm_job_run = models.JobRuns(
        **job_run_create.dict(),
        status=schemas.Status.awaiting_start,
        project_id=project_id,
    )
    session.add(orm_job_run)
    session.commit()
    session.refresh(orm_job_run)
    return schemas.JobRunResponse.model_validate(orm_job_run)


def update_job_run(
    session: Session,
    job_run_data: Union[
        schemas.JobRunUpdateStarted, schemas.JobRunUpdateCompleted, schemas.JobRunUpdateProcessing
    ],
) -> schemas.JobRunResponse:
    """Update a job run.

    Note that only the schemas giving in the signature are allowed to be passed in.
    """
    orm_job_run = (
        session.query(models.JobRuns).filter(models.JobRuns.id == job_run_data.id).first()
    )
    if orm_job_run:
        for field, value in job_run_data.dict(exclude={"id"}).items():
            setattr(orm_job_run, field, value)
        session.commit()

    return schemas.JobRunResponse.model_validate(orm_job_run)


def update_job_run_from_route(
    session: Session,
    project_id: int,
    job_run_id: int,
    job_run_data: schemas.JobRunUpdateRoute,
) -> schemas.JobRunResponse | None:
    """Update a job run from a fast API route (PATCH - partial update)."""
    orm_job_run = (
        session.query(models.JobRuns)
        .filter(models.JobRuns.id == job_run_id, models.JobRuns.project_id == project_id)
        .first()
    )
    if not orm_job_run:
        return None

    for field, value in job_run_data.dict(exclude_unset=True).items():
        setattr(orm_job_run, field, value)
    session.commit()
    session.refresh(orm_job_run)
    return schemas.JobRunResponse.model_validate(orm_job_run)


def replace_job_run_from_route(
    session: Session,
    project_id: int,
    job_run_id: int,
    job_run_data: schemas.JobRunReplaceRoute,
) -> schemas.JobRunResponse | None:
    """Replace a job run from a fast API route (PUT - full replacement)."""
    orm_job_run = (
        session.query(models.JobRuns)
        .filter(models.JobRuns.id == job_run_id, models.JobRuns.project_id == project_id)
        .first()
    )
    if not orm_job_run:
        return None

    # Full replacement - use dict() without exclude_unset
    for field, value in job_run_data.dict().items():
        setattr(orm_job_run, field, value)
    session.commit()
    session.refresh(orm_job_run)
    return schemas.JobRunResponse.model_validate(orm_job_run)


def get_job_run(
    session: Session, project_id: int, job_run_id: int
) -> schemas.JobRunResponse | None:
    """Get a job run."""
    orm_job_run = (
        session.query(models.JobRuns)
        .filter(models.JobRuns.project_id == project_id, models.JobRuns.id == job_run_id)
        .first()
    )
    if orm_job_run is None:
        return None
    return schemas.JobRunResponse.model_validate(orm_job_run)


def get_job_runs(
    session: Session,
    project_id: int,
    start: int = 0,
    end: int = 100,
    foreign_job_type: schemas.ForeignJobType | None = None,
) -> list[schemas.JobRunResponse]:
    """Get job runs."""
    query = session.query(models.JobRuns).filter(models.JobRuns.project_id == project_id)
    if foreign_job_type:
        query = query.filter(models.JobRuns.foreign_job_type == foreign_job_type)
    orm_job_runs = query.order_by(models.JobRuns.id.desc()).slice(start, end).all()
    return [schemas.JobRunResponse.model_validate(orm_job_run) for orm_job_run in orm_job_runs]


def get_latest_job_run(
    session: Session,
    project_id: int,
    foreign_id: int | None = None,
    foreign_job_type: schemas.ForeignJobType | None = None,
) -> schemas.JobRunResponse | None:
    """Get the latest job run."""
    query = session.query(models.JobRuns).filter(models.JobRuns.project_id == project_id)
    if foreign_id:
        query = query.filter(models.JobRuns.foreign_id == foreign_id)
    if foreign_job_type:
        query = query.filter(models.JobRuns.foreign_job_type == foreign_job_type)
    orm_job_run = query.order_by(models.JobRuns.id.desc()).first()
    if orm_job_run is None:
        return None
    return schemas.JobRunResponse.model_validate(orm_job_run)


async def create_and_run_job_run(
    session: Session,
    project_id: int,
    job_run_create: schemas.JobRunCreate,
) -> schemas.JobRunResponse:
    """Create a new job run and run it.

    For the guards based on the project to be run the project detail must be provided.

    Args:
        session: The database session.
        project_id: The project id.
        job_run_create: The job run create schema.
        project_detail: (Optional) The project detail schema.
            If provided, the guards for the job run based on the project will be done.
    """
    job_run = create_job_run(session, project_id, job_run_create)
    try:
        job_run = await prefect_deployment.start_deployment(
            session=session,
            name="flow_runner_flow/flow_runner_flow",
            job_run=job_run,
        )
    except Exception as e:
        job_run = update_job_run(
            session,
            schemas.JobRunUpdateCompleted(
                id=job_run.id,
                status=schemas.Status.failed,
                completed_at=datetime.now(),
            ),
        )
        logger.error("Error running deployment", exc_info=e)
    return job_run


def get_total_costs_for_project(session: Session, project_id: int) -> float:
    """Get the total costs for a project."""
    total = (
        session.query(models.JobRuns.total_cost)
        .filter(models.JobRuns.project_id == project_id)
        .with_entities(func.sum(models.JobRuns.total_cost))
        .scalar()
    )
    return total or 0.0  # Return 0.0 if total is None


def get_estimated_incomplete_costs_for_project(session: Session, project_id: int) -> float:
    """Get the estimated incomplete costs for a project."""
    estimated_incomplete = (
        session.query(models.JobRuns.estimated_total_cost)
        .filter(
            models.JobRuns.project_id == project_id,
            models.JobRuns.completed_at.is_(None),
        )
        .with_entities(func.sum(models.JobRuns.estimated_total_cost))
        .scalar()
    )
    return estimated_incomplete or 0.0  # Return 0.0 if total is None


def get_last_job_run_completed_at_for_project(
    session: Session, project_id: int
) -> datetime | None:
    """Get the last job run completed at for a project."""
    last_job_run_completed_at: models.JobRuns | None = (
        session.query(models.JobRuns)
        .filter(
            models.JobRuns.project_id == project_id,
            models.JobRuns.completed_at.isnot(None),
        )
        .order_by(models.JobRuns.id.desc())
        .first()
    )
    if last_job_run_completed_at is None:
        return None

    return last_job_run_completed_at.completed_at
