"""Classifier routes."""

import fastapi

from phiphi.api import deps, exceptions
from phiphi.api.projects import deps as projects_deps
from phiphi.api.projects.classifiers import base_schemas, crud, response_schemas
from phiphi.api.projects.classifiers.hugging_face import routes as hugging_face_routes
from phiphi.api.projects.classifiers.keyword_match import routes as keyword_match_routes
from phiphi.api.projects.classifiers.manual_post_authors import (
    routes as manual_post_authors_routes,
)
from phiphi.api.projects.classifiers.perspective_api import routes as perspective_api_routes

router = fastapi.APIRouter()
router.include_router(keyword_match_routes.router)
router.include_router(manual_post_authors_routes.router)
router.include_router(perspective_api_routes.router)
router.include_router(hugging_face_routes.router)


@router.get(
    "/projects/{project_id}/classifiers/{classifier_id}",
    response_model=response_schemas.ClassifierDetail,
)
def get_classifier(
    session: deps.SessionDep,
    project: projects_deps.ProjectViewAccessDep,
    classifier_id: int,
) -> response_schemas.ClassifierDetail:
    """Get a classifier."""
    classifier = crud.get_classifier(
        session=session, project_id=project.id, classifier_id=classifier_id
    )
    if classifier is None:
        raise exceptions.ClassifierNotFound()
    return classifier


@router.get(
    "/projects/{project_id}/classifiers", response_model=list[response_schemas.ClassifierSummary]
)
def get_classifiers(
    session: deps.SessionDep,
    project: projects_deps.ProjectViewAccessDep,
    start: int = 0,
    end: int = 100,
    exclude_archived: bool = False,
) -> list[response_schemas.ClassifierSummary]:
    """Get classifiers."""
    return crud.get_classifiers(
        session=session,
        project_id=project.id,
        start=start,
        end=end,
        exclude_archived=exclude_archived,
    )


@router.patch(
    "/projects/{project_id}/classifiers/{classifier_id}",
    response_model=response_schemas.ClassifierDetail,
)
def patch_classifier(
    session: deps.SessionDep,
    project: projects_deps.ProjectUseAccessDep,
    classifier_id: int,
    classifier_patch: base_schemas.ClassifierPatch,
) -> response_schemas.ClassifierDetail:
    """Patch a classifier."""
    classifier = crud.patch_classifier(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
        classifier_patch=classifier_patch,
    )
    return classifier


@router.post(
    "/projects/{project_id}/classifiers/{classifier_id}/archive",
    response_model=response_schemas.ClassifierDetail,
)
async def archive_classifier(
    session: deps.SessionDep,
    project: projects_deps.ProjectUseAccessDep,
    classifier_id: int,
) -> response_schemas.ClassifierDetail:
    """Archive a classifier."""
    classifier = await crud.archive_classifier_run_archive_job(
        session=session, project_id=project.id, classifier_id=classifier_id
    )
    return classifier


@router.post(
    "/projects/{project_id}/classifiers/{classifier_id}/restore",
    response_model=response_schemas.ClassifierDetail,
)
async def restore_classifier(
    session: deps.SessionDep,
    project: projects_deps.ProjectUseAccessDep,
    classifier_id: int,
) -> response_schemas.ClassifierDetail:
    """Restore a classifier."""
    classifier = await crud.restore_classifier_run_restore_job(
        session=session, project_id=project.id, classifier_id=classifier_id
    )
    return classifier


@router.patch(
    "/projects/{project_id}/classifiers/{classifier_id}/intermediatory_classes/{class_id}",
)
def patch_intemediatory_classes(
    session: deps.SessionDep,
    project: projects_deps.ProjectUseAccessDep,
    classifier_id: int,
    class_id: int,
    class_patch: base_schemas.IntermediatoryClassPatch,
) -> base_schemas.IntermediatoryClassResponse:
    """Patch the classes of a classifier."""
    return crud.patch_intermediatory_class(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
        class_id=class_id,
        class_patch=class_patch,
    )


@router.delete(
    "/projects/{project_id}/classifiers/{classifier_id}/intermediatory_classes/{class_id}",
)
def delete_intemediatory_classes(
    session: deps.SessionDep,
    project: projects_deps.ProjectUseAccessDep,
    classifier_id: int,
    class_id: int,
) -> None:
    """Delete the classes of a classifier."""
    return crud.delete_intermediatory_class(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
        class_id=class_id,
    )


@router.post("/projects/{project_id}/classifiers/{classifier_id}/intermediatory_classes")
def create_intemediatory_classes(
    session: deps.SessionDep,
    project: projects_deps.ProjectUseAccessDep,
    classifier_id: int,
    class_create: base_schemas.IntermediatoryClassCreate,
) -> base_schemas.IntermediatoryClassResponse:
    """Create the classes of a classifier."""
    return crud.create_intermediatory_class(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
        class_create=class_create,
    )
