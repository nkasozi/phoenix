"""Routes for the workspaces."""

import fastapi
from phiphi.api import deps
from phiphi.api.workspaces import crud, schemas

router = fastapi.APIRouter()


@router.post("/workspaces/", response_model=schemas.WorkspaceResponse)
def create_workspace(
    workspace: schemas.WorkspaceCreate, session: deps.SessionDep
) -> schemas.WorkspaceResponse:
    """Create a new workspace."""
    try:
        return crud.create_workspace(session, workspace)
    except Exception as e:
        raise fastapi.HTTPException(status_code=400, detail=str(e))


@router.put("/workspaces/{workspace_id}", response_model=schemas.WorkspaceResponse)
def update_workspace(
    workspace_id: int, workspace: schemas.WorkspaceUpdate, session: deps.SessionDep
) -> schemas.WorkspaceResponse:
    """Update an workspace."""
    updated_workspace = crud.update_workspace(session, workspace_id, workspace)
    if updated_workspace is None:
        raise fastapi.HTTPException(status_code=404, detail="Workspace not found")
    return updated_workspace


@router.get("/workspaces/{slug}", response_model=schemas.WorkspaceResponse)
def get_workspace(slug: str, session: deps.SessionDep) -> schemas.WorkspaceResponse:
    """Get an workspace."""
    workspace = crud.get_workspace(session, slug)
    if workspace is None:
        raise fastapi.HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.get("/workspaces/", response_model=list[schemas.WorkspaceResponse])
def get_workspaces(
    session: deps.SessionDep, start: int = 0, end: int = 100
) -> list[schemas.WorkspaceResponse]:
    """Get Workspaces."""
    return crud.get_workspaces(session, start, end)


@router.get("/workspaces/slug/", response_model=schemas.SlugResponse)
def get_unique_slug(workspace_name: str, session: deps.SessionDep) -> schemas.SlugResponse:
    """Get unique slug."""
    try:
        return crud.get_unique_slug(session, workspace_name)
    except Exception as e:
        raise fastapi.HTTPException(status_code=400, detail=str(e))
