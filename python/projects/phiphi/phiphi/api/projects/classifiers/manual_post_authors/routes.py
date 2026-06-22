"""Manual post authors routes."""

import fastapi

from phiphi.api import deps
from phiphi.api.projects import classifiers
from phiphi.api.projects import deps as project_deps
from phiphi.api.projects.classifiers import base_schemas, response_schemas
from phiphi.api.projects.classifiers.manual_post_authors import crud, schemas

router = fastapi.APIRouter()


@router.post(
    "/projects/{project_id}/classifiers/manual_post_authors",
)
def create_manual_post_authors_classifier(
    session: deps.SessionDep,
    project: project_deps.ProjectUseAccessDep,
    classifier_create: base_schemas.ClassifierWithIntermediatoryCreate,
) -> response_schemas.ClassifierDetail:
    """Create a new keyword match classifier."""
    return classifiers.crud.create_classifier(
        session=session,
        project_id=project.id,
        classifier_type=base_schemas.ClassifierType.manual_post_authors,
        classifier_create=classifier_create,
    )


@router.post(
    "/projects/{project_id}/classifiers/manual_post_authors/{classifier_id}/intermediatory_author_classes",
)
def create_intermediatory_author_class(
    session: deps.SessionDep,
    project: project_deps.ProjectUseAccessDep,
    classifier_id: int,
    create_obj: schemas.IntermediatoryAuthorClassCreate,
) -> schemas.IntermediatoryAuthorClassResponse:
    """Create an intermediatory author class."""
    return crud.create_intermediatory_author_class(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
        create_obj=create_obj,
    )


@router.delete(
    "/projects/{project_id}/classifiers/manual_post_authors/{classifier_id}/intermediatory_author_classes/{classified_post_author_id}",
)
def delete_intermediatory_author_class(
    session: deps.SessionDep,
    project: project_deps.ProjectUseAccessDep,
    classifier_id: int,
    classified_post_author_id: int,
) -> None:
    """Delete an intermediatory author class."""
    return crud.delete_intermediatory_author_class(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
        classified_post_author_id=classified_post_author_id,
    )


@router.get(
    "/projects/{project_id}/classifiers/manual_post_authors/{classifier_id}/authors/",
)
def get_post_authors_with_intermediatory_author_classes(
    session: deps.SessionDep,
    project: project_deps.ProjectViewAccessDep,
    classifier_id: int,
    start: int = 0,
    end: int = 10,
) -> schemas.AuthorsListResponse:
    """Get post authors with intermediatory author classes."""
    return crud.get_post_authors_with_intermediatory_author_classes(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
        offset=start,
        limit=end,
    )


@router.get(
    "/projects/{project_id}/classifiers/manual_post_authors/{classifier_id}/authors/{author_id}",
)
def get_post_author_with_intermediatory_author_classes(
    session: deps.SessionDep,
    project: project_deps.ProjectViewAccessDep,
    classifier_id: int,
    author_id: str,
) -> schemas.AuthorResponse:
    """Get post author with intermediatory author classes."""
    return crud.get_post_author_with_intermediatory_author_classes(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
        author_id=author_id,
    )


@router.get(
    "/projects/{project_id}/classifiers/manual_post_authors/authors/",
)
def get_authors(
    session: deps.SessionDep,
    project: project_deps.ProjectViewAccessDep,
    start: int = 0,
    end: int = 10,
) -> schemas.AuthorsListResponse:
    """Get post authors with empty intermediatory_author_classes.

    This endpoint can be used to show the possible authors that can be classified.
    """
    return crud.get_post_authors(
        session=session,
        project_id=project.id,
        offset=start,
        limit=end,
    )


@router.post(
    "/projects/{project_id}/classifiers/manual_post_authors/{classifier_id}/version_and_run",
)
async def create_version_and_run(
    session: deps.SessionDep,
    project: project_deps.ProjectUseAccessDep,
    classifier_id: int,
) -> schemas.ManualPostAuthorsClassifierDetail:
    """Create a manual post authors version and run."""
    return await crud.create_version_and_run(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
    )
