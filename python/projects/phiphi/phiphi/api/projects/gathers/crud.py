"""Gather crud functionality.

This module contains the crud functionality for gathers.

Be aware that it does not check for the existence of Projects this should be done in the
routes/code that uses module.
"""

import sqlalchemy.orm

from phiphi.api import exceptions
from phiphi.api.projects.gathers import models, schemas
from phiphi.api.projects.job_runs import crud as job_run_crud
from phiphi.api.projects.job_runs import schemas as job_run_schemas


def get_gather(
    session: sqlalchemy.orm.Session, project_id: int, gather_id: int
) -> schemas.GatherResponse | None:
    """Get an apify gather."""
    orm_gather = get_orm_gather(session, project_id, gather_id)
    if orm_gather is None:
        return None
    return schemas.GatherResponse.model_validate(orm_gather)


def get_orm_gather(
    session: sqlalchemy.orm.Session, project_id: int, gather_id: int
) -> models.Gather | None:
    """Get a gather orm model."""
    orm_gather = (
        session.query(models.Gather)
        .filter(
            models.Gather.project_id == project_id,
            models.Gather.id == gather_id,
        )
        .first()
    )
    return orm_gather


def get_gathers(
    session: sqlalchemy.orm.Session,
    project_id: int,
    start: int = 0,
    end: int = 100,
) -> list[schemas.GatherResponse]:
    """Retrieve all gathers and relations."""
    gathers = (
        session.query(models.Gather)
        .filter(models.Gather.project_id == project_id)
        .order_by(models.Gather.id.desc())
        .slice(start, end)
        .all()
    )

    if not gathers:
        return []
    return [schemas.GatherResponse.model_validate(gather) for gather in gathers]


async def delete(
    session: sqlalchemy.orm.Session, project_id: int, gather_id: int
) -> schemas.GatherResponse:
    """Delete a gather."""
    orm_gather = get_orm_gather(session, project_id, gather_id)
    if orm_gather is None:
        raise exceptions.GatherNotFound()

    delete_job_run_response = await job_run_crud.create_and_run_job_run(
        session,
        project_id,
        job_run_schemas.JobRunCreate(
            foreign_id=gather_id,
            foreign_job_type=job_run_schemas.ForeignJobType.delete_gather_tabulate,
        ),
    )

    orm_gather.delete_job_run_id = delete_job_run_response.id
    session.commit()
    return schemas.GatherResponse.model_validate(orm_gather)
