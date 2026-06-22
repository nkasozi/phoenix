"""Routes for gathers."""

import fastapi

from phiphi.api import deps
from phiphi.api.projects import crud as projects_crud
from phiphi.api.projects import deps as project_deps
from phiphi.api.projects.gathers import (
    child_crud,
    child_routes,
    child_types,
    crud,
    manual_upload,
    run,
    schemas,
)

router = fastapi.APIRouter()
router.include_router(child_routes.router)
router.include_router(manual_upload.routes.router)


@router.get(
    "/projects/{project_id}/gathers/",
    response_model=list[schemas.GatherResponse],
    response_model_by_alias=False,
)
def get_gathers(
    session: deps.SessionDep,
    project: project_deps.ProjectViewAccessDep,
    start: int = 0,
    end: int = 100,
) -> list[schemas.GatherResponse]:
    """Get gathers."""
    return crud.get_gathers(session, project.id, start, end)


@router.get(
    "/projects/{project_id}/gathers/{gather_id}",
    response_model=child_types.AllChildTypesUnion,
    response_model_by_alias=False,
)
def get_gather(
    project: project_deps.ProjectViewAccessDep, gather_id: int, session: deps.SessionDep
) -> child_types.AllChildTypesUnion:
    """Get an apify gather."""
    gather = child_crud.get_child_gather(session, project.id, gather_id)
    if gather is None:
        raise fastapi.HTTPException(status_code=404, detail="Gather not found")
    return gather


@router.delete(
    "/projects/{project_id}/gathers/{gather_id}",
    response_model=schemas.GatherResponse,
    response_model_by_alias=False,
)
async def delete_gather(
    project: project_deps.ProjectUseAccessDep, gather_id: int, session: deps.SessionDep
) -> schemas.GatherResponse:
    """Delete a gather."""
    gather_response = await crud.delete(session, project.id, gather_id)
    return gather_response


@router.post(
    "/projects/{project_id}/gathers/{gather_id}/run",
    response_model=child_types.AllChildTypesUnion,
    response_model_by_alias=False,
)
async def run_gather(
    project_id: int,
    gather_id: int,
    session: deps.SessionDep,
    project: project_deps.ProjectUseAccessDep,
) -> child_types.AllChildTypesUnion:
    """Run a gather."""
    project_detail = projects_crud.form_project_detail(session, project)
    gather_response = await run.run_gather_job_run_with_costs_guard(
        session, project_id, gather_id, project_detail
    )
    return gather_response
