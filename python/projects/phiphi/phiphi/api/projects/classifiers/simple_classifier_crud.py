"""Shared CRUD for simple, versioned classifiers.

Simple classifiers are those that do not require intermediary tables that store user changes before
a classifier version is created. See `phiphi.api.projects.classifiers.crud` for more complex
classifiers.
"""

from typing import TypeVar

import sqlalchemy as sa

from phiphi.api import exceptions
from phiphi.api.projects import classifiers
from phiphi.api.projects.classifiers import base_schemas
from phiphi.api.projects.job_runs import crud as job_run_crud
from phiphi.api.projects.job_runs import schemas as job_run_schemas

T_Detail = TypeVar("T_Detail", bound=base_schemas.ClassifierDetailBase)
T_Create = TypeVar("T_Create", bound=base_schemas.ClassifierCreateWithVersion)
T_Version = TypeVar("T_Version", bound=base_schemas.ClassifierSimpleVersionBase)


async def create_classifier_and_run(
    session: sa.orm.Session,
    project_id: int,
    classifier_create: T_Create,
    classifier_type: classifiers.base_schemas.ClassifierType,
    detail_schema_cls: type[T_Detail],
) -> T_Detail:
    """Create a classifier and run job."""
    orm_classifier = create_and_version_orm(
        session, project_id, classifier_create, classifier_type
    )
    _ = await job_run_crud.create_and_run_job_run(
        session,
        project_id,
        job_run_schemas.JobRunCreate(
            foreign_id=orm_classifier.id,
            foreign_job_type=job_run_schemas.ForeignJobType.classify_tabulate,
        ),
    )
    session.refresh(orm_classifier)
    return detail_schema_cls.model_validate(orm_classifier)


def create_and_version_orm(
    session: sa.orm.Session,
    project_id: int,
    classifier_create: T_Create,
    classifier_type: classifiers.base_schemas.ClassifierType,
) -> classifiers.models.Classifiers:
    """Create a classifier and version ORM object."""
    orm_classifier = classifiers.models.Classifiers(
        project_id=project_id,
        name=classifier_create.name,
        description=classifier_create.description,
        type=classifier_type,
        archived_at=None,
    )
    session.add(orm_classifier)
    session.commit()
    session.refresh(orm_classifier)

    _ = create_version(session, orm_classifier, classifier_create.latest_version)
    session.refresh(orm_classifier)
    return orm_classifier


def create_and_version(
    session: sa.orm.Session,
    project_id: int,
    classifier_create: T_Create,
    classifier_type: classifiers.base_schemas.ClassifierType,
    detail_schema_cls: type[T_Detail],
) -> T_Detail:
    """Create a classifier and version."""
    orm_classifier = create_and_version_orm(
        session, project_id, classifier_create, classifier_type
    )
    return detail_schema_cls.model_validate(orm_classifier)


def create_version(
    session: sa.orm.Session,
    orm_classifier: classifiers.models.Classifiers,
    classifier_version: T_Version,
) -> classifiers.models.ClassifierVersions:
    """Create a classifier version."""
    dict_version = classifier_version.model_dump()
    orm_version = classifiers.models.ClassifierVersions(
        classifier_id=orm_classifier.id,
        classes=dict_version["classes"],
        params=dict_version["params"],
    )
    session.add(orm_version)
    session.commit()
    session.refresh(orm_version)
    return orm_version


async def create_version_and_run(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
    version_schema: T_Version,
    detail_schema_cls: type[T_Detail],
) -> T_Detail:
    """Create a new version and run a classification job.

    Args:
        session: SQLAlchemy session.
        project_id: ID of the project.
        classifier_id: ID of the existing classifier.
        version_schema: Pydantic schema for the new version.
        detail_schema_cls: Class for the detail schema to return.

    Returns:
        An instance of the detail schema with updated classifier data.

    Raises:
        exceptions.ClassifierNotFound: If no classifier with given ID exists.
    """
    orm_classifier = classifiers.crud.get_orm_classifier(session, project_id, classifier_id)
    if orm_classifier is None:
        raise exceptions.ClassifierNotFound()

    create_version(session, orm_classifier, version_schema)
    await job_run_crud.create_and_run_job_run(
        session,
        project_id,
        job_run_schemas.JobRunCreate(
            foreign_id=orm_classifier.id,
            foreign_job_type=job_run_schemas.ForeignJobType.classify_tabulate,
        ),
    )
    session.refresh(orm_classifier)
    return detail_schema_cls.model_validate(orm_classifier)
