"""Routes for the projects."""

import logging

import fastapi

from phiphi.api import deps
from phiphi.api.projects import credit_allocations, crud, schemas, user_project_associations
from phiphi.api.projects import deps as project_deps

router = fastapi.APIRouter()

logger = logging.getLogger(__name__)


@router.post("/projects/", response_model=schemas.ProjectResponse)
async def create_project(
    admin_user: deps.AdminOnlyUser, project: schemas.ProjectCreate, session: deps.SessionDep
) -> schemas.ProjectResponse:
    """Create a new project."""
    logger.info(f"Creating project: {project}")
    project_response = await crud.create_project_with_external_resources(
        session, admin_user.id, project
    )
    return project_response


@router.put("/projects/{project_id}")
def update_project(
    admin_user: deps.AdminOnlyUser,
    project_id: int,
    project: schemas.ProjectUpdate,
    session: deps.SessionDep,
) -> schemas.ProjectResponse:
    """Update an project."""
    updated_project = crud.update_project(session, project_id, project)
    if updated_project is None:
        raise fastapi.HTTPException(status_code=404, detail="Project not found")
    return updated_project


@router.put("/projects/{project_id}/checklist")
def update_project_checklist(
    project: project_deps.ProjectUseAccessDep,
    checklist: schemas.ProjectChecklistUpdate,
    session: deps.SessionDep,
) -> schemas.ProjectResponse:
    """Update project checklist."""
    updated_project = crud.update_project_checklist(session, project.id, checklist)
    if updated_project is None:
        raise fastapi.HTTPException(status_code=404, detail="Project not found")
    return updated_project


@router.get("/projects/{project_id}")
def get_project_detail(
    project: project_deps.ProjectViewAccessDep, session: deps.SessionDep
) -> schemas.ProjectDetail:
    """Get an Project."""
    project = crud.form_project_detail(session, project)
    return project


@router.get("/projects/", response_model=list[schemas.ProjectListResponse])
def get_projects(
    user: deps.CurrentUser, session: deps.SessionDep, end: int | None = None, start: int = 0
) -> list[schemas.ProjectListResponse]:
    """Get Projects."""
    if user.is_admin():
        return crud.get_all_projects(session, end=end, start=start)

    return crud.get_user_projects(session, user.id, end=end, start=start)


@router.delete("/projects/{project_id}")
def delete_project(
    admin_user: deps.AdminOnlyUser, project_id: int, session: deps.SessionDep
) -> None:
    """Delete an project."""
    crud.delete_project(session, project_id, delete_project_db=True)
    return None


@router.post("/projects/{project_id}/users/{user_id}")
def add_user_to_project(
    admin_user: deps.AdminOnlyUser,
    project_id: int,
    user_id: int,
    create_obj: user_project_associations.UserProjectAssociationCreate,
    session: deps.SessionDep,
) -> user_project_associations.UserProjectAssociationResponse:
    """Add a user to a project."""
    return user_project_associations.create_user_project_association(
        session, project_id, user_id, create_obj
    )


@router.delete("/projects/{project_id}/users/{user_id}")
def remove_user_from_project(
    admin_user: deps.AdminOnlyUser, project_id: int, user_id: int, session: deps.SessionDep
) -> None:
    """Remove a user from a project."""
    user_project_associations.delete_user_project_association(session, project_id, user_id)
    return None


# Get for all users in a project
@router.get(
    "/projects/{project_id}/users/",
    response_model=list[user_project_associations.UserProjectAssociationResponse],
)
def get_users_in_project(
    admin_user: deps.AdminOnlyUser, project_id: int, session: deps.SessionDep
) -> list[user_project_associations.UserProjectAssociationResponse]:
    """Get all users in a project."""
    return user_project_associations.get_user_project_associations(session, project_id)


@router.post("/projects/{project_id}/credit_allocations/")
def create_credit_allocation(
    user: deps.AdminOnlyUser,
    project_id: int,
    credit_allocation: credit_allocations.CreditAllocationCreate,
    session: deps.SessionDep,
) -> credit_allocations.CreditAllocationResponse:
    """Create a credit allocation.

    This route is only accessible to admin users.
    """
    return credit_allocations.create_credit_allocation(
        session, user.id, project_id, credit_allocation
    )


@router.get("/projects/{project_id}/credit_allocations/")
def get_credit_allocations(
    user: deps.AdminOnlyUser,
    project_id: int,
    session: deps.SessionDep,
) -> list[credit_allocations.CreditAllocationResponse]:
    """Get all credit allocations for a project.

    Only admins can view credit allocations.
    """
    return credit_allocations.get_credit_allocations(session, project_id)
