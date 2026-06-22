"""Perspective API crud functionality."""

import sqlalchemy as sa

from phiphi.api.projects import classifiers
from phiphi.api.projects.classifiers import simple_classifier_crud
from phiphi.api.projects.classifiers.perspective_api import schemas


async def create_classifier_and_run(
    session: sa.orm.Session,
    project_id: int,
    classifier_create: schemas.PerspectiveAPIClassifierCreate,
) -> schemas.PerspectiveAPIClassifierDetail:
    """Create a perspective API classifier."""
    return await simple_classifier_crud.create_classifier_and_run(
        session,
        project_id,
        classifier_create,
        classifiers.base_schemas.ClassifierType.perspective_api,
        schemas.PerspectiveAPIClassifierDetail,
    )


def create_and_version(
    session: sa.orm.Session,
    project_id: int,
    classifier_create: schemas.PerspectiveAPIClassifierCreate,
) -> schemas.PerspectiveAPIClassifierDetail:
    """Create a perspective API classifier and version."""
    return simple_classifier_crud.create_and_version(
        session,
        project_id,
        classifier_create,
        classifiers.base_schemas.ClassifierType.perspective_api,
        schemas.PerspectiveAPIClassifierDetail,
    )


async def create_version_and_run(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
    classifier_version: schemas.PerspectiveAPIVersionBase,
) -> schemas.PerspectiveAPIClassifierDetail:
    """Create a Perspective API version and run classification."""
    return await simple_classifier_crud.create_version_and_run(
        session,
        project_id,
        classifier_id,
        classifier_version,
        schemas.PerspectiveAPIClassifierDetail,
    )
