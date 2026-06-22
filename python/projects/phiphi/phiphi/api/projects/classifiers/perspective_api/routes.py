"""Routes for Perspective API."""

import fastapi

from phiphi.api import deps
from phiphi.api.projects import deps as projects_deps
from phiphi.api.projects.classifiers.perspective_api import crud, schemas

router = fastapi.APIRouter()


@router.post(
    "/projects/{project_id}/classifiers/perspective_api",
)
async def create_perspective_api_and_run(
    session: deps.SessionDep,
    project: projects_deps.ProjectUseAccessDep,
    classifier_create: schemas.PerspectiveAPIClassifierCreate,
) -> schemas.PerspectiveAPIClassifierDetail:
    """Create and run a new perspective API classifier."""
    return await crud.create_classifier_and_run(
        session=session,
        project_id=project.id,
        classifier_create=classifier_create,
    )


@router.post(
    "/projects/{project_id}/classifiers/perspective_api/{classifier_id}/version_and_run",
)
async def create_perspective_api_version_and_run(
    session: deps.SessionDep,
    project: projects_deps.ProjectUseAccessDep,
    classifier_id: int,
    classifier_version: schemas.PerspectiveAPIVersionBase,
) -> schemas.PerspectiveAPIClassifierDetail:
    """Create a new perspective API version and run."""
    return await crud.create_version_and_run(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
        classifier_version=classifier_version,
    )
