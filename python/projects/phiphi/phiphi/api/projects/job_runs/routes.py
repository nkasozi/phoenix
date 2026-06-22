"""JobRun routes."""

import logging

import fastapi

from phiphi.api import deps
from phiphi.api.projects import deps as project_deps
from phiphi.api.projects.job_runs import crud, schemas

router = fastapi.APIRouter()

logger = logging.getLogger(__name__)


@router.get("/projects/{project_id}/job_runs/{id}", response_model=schemas.JobRunResponse)
def get_job_run(
    project: project_deps.ProjectViewAccessDep, id: int, session: deps.SessionDep
) -> schemas.JobRunResponse:
    """Get a Project Job Run."""
    job_run = crud.get_job_run(session, project.id, id)
    if job_run is None:
        raise fastapi.HTTPException(status_code=404, detail="Job Run not found")
    return job_run


@router.get("/projects/{project_id}/job_runs/", response_model=list[schemas.JobRunResponse])
def get_job_runs(
    project: project_deps.ProjectViewAccessDep,
    session: deps.SessionDep,
    start: int = 0,
    end: int = 100,
    foreign_job_type: schemas.ForeignJobType | None = None,
) -> list[schemas.JobRunResponse]:
    """Get Project Job Runs."""
    return crud.get_job_runs(session, project.id, start, end, foreign_job_type)


@router.patch("/projects/{project_id}/job_runs/{job_run_id}")
def update_job_run(
    admin_user: deps.AdminOnlyUser,
    project_id: int,
    job_run_id: int,
    job_run: schemas.JobRunUpdateRoute,
    session: deps.SessionDep,
) -> schemas.JobRunResponse:
    """Partially update a JobRun."""
    updated_job_run = crud.update_job_run_from_route(session, project_id, job_run_id, job_run)
    if updated_job_run is None:
        raise fastapi.HTTPException(status_code=404, detail="Job Run not found")
    return updated_job_run


@router.put("/projects/{project_id}/job_runs/{job_run_id}")
def replace_job_run(
    admin_user: deps.AdminOnlyUser,
    project_id: int,
    job_run_id: int,
    job_run: schemas.JobRunReplaceRoute,
    session: deps.SessionDep,
) -> schemas.JobRunResponse:
    """Fully replace a JobRun."""
    replaced_job_run = crud.replace_job_run_from_route(session, project_id, job_run_id, job_run)
    if replaced_job_run is None:
        raise fastapi.HTTPException(status_code=404, detail="Job Run not found")
    return replaced_job_run
