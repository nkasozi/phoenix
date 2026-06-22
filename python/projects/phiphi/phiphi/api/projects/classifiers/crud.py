"""CRUD operations for classifiers."""

import contextlib
import datetime
from typing import Generator

import sqlalchemy.orm

from phiphi.api import exceptions
from phiphi.api.projects.classifiers import base_schemas, models, response_schemas
from phiphi.api.projects.job_runs import crud as job_run_crud
from phiphi.api.projects.job_runs import schemas as job_run_schemas


def create_classifier(
    session: sqlalchemy.orm.Session,
    project_id: int,
    classifier_type: base_schemas.ClassifierType,
    classifier_create: base_schemas.ClassifierWithIntermediatoryCreate,
) -> response_schemas.ClassifierDetail:
    """Create a new classifier with an initial version.

    To make the versioning more transparent we only create versions for a classifier when
    `create_version` is called.
    """
    orm_classifier = models.Classifiers(
        project_id=project_id,
        name=classifier_create.name,
        description=classifier_create.description,
        type=classifier_type,
        archived_at=None,
    )
    session.add(orm_classifier)
    session.commit()
    session.refresh(orm_classifier)

    for class_create in classifier_create.intermediatory_classes:
        orm_intermediate_class = models.IntermediatoryClasses(
            classifier_id=orm_classifier.id,
            name=class_create.name,
            description=class_create.description,
        )
        session.add(orm_intermediate_class)

    session.commit()
    session.refresh(orm_classifier)
    return response_schemas.classifier_detail_adapter.validate_python(orm_classifier)


def get_classes(
    session: sqlalchemy.orm.Session,
    orm_classifier: models.Classifiers,
) -> list[base_schemas.ClassLabel]:
    """Get the classes for a classifier.

    This will return a dictionary of the classes for a classifier.

    Args:
        session: SQLAlchemy session.
        orm_classifier: Classifier ORM. Using a classifier ORM rather then just the id to show that
            the classifier has to exist.

    Returns:
        Classes
    """
    list_intermediatory_classes = (
        session.query(models.IntermediatoryClasses)
        .filter(models.IntermediatoryClasses.classifier_id == orm_classifier.id)
        .all()
    )

    classes = [
        base_schemas.ClassLabel.model_validate(intermediatory_class)
        for intermediatory_class in list_intermediatory_classes
    ]

    return classes


def get_orm_classifier(
    session: sqlalchemy.orm.Session,
    project_id: int,
    classifier_id: int,
) -> models.Classifiers | None:
    """Get a classifier ORM."""
    return (
        session.query(models.Classifiers)
        .filter(models.Classifiers.project_id == project_id)
        .filter(models.Classifiers.id == classifier_id)
        .one_or_none()
    )


@contextlib.contextmanager
def get_orm_classifier_with_edited_context(
    session: sqlalchemy.orm.Session,
    project_id: int,
    classifier_id: int,
) -> Generator[models.Classifiers, None, None]:
    """Get a classifier ORM last_edited_at updated at the end of context.

    The classifier has to exist and not be archived or this will raise an exception.

    This is useful when you want to update the last_edited_at field after a set of operations are
    done.

    !! Important !!
    To get the correct last_edited_at value, the ORM object should not be modified directly
    and orm.refresh() should be called after the context manager is done.
    """
    orm = (
        session.query(models.Classifiers)
        .filter(models.Classifiers.project_id == project_id)
        .filter(models.Classifiers.id == classifier_id)
        .one_or_none()
    )
    if orm is None:
        raise exceptions.ClassifierNotFound()

    if orm.archived_at is not None:
        raise exceptions.ClassifierArchived()

    yield orm
    if orm:
        orm.last_edited_at = datetime.datetime.utcnow()
        session.commit()


def get_classifier(
    session: sqlalchemy.orm.Session,
    project_id: int,
    classifier_id: int,
) -> response_schemas.ClassifierDetail | None:
    """Get a classifier with its latest version."""
    orm_classifier = get_orm_classifier(session, project_id, classifier_id)

    if orm_classifier is None:
        return None

    return response_schemas.classifier_detail_adapter.validate_python(orm_classifier)


def get_pipeline_classifier(
    session: sqlalchemy.orm.Session,
    project_id: int,
    classifier_id: int,
) -> response_schemas.ClassifierPipeline | None:
    """Get a pipeline classifiers for a project.

    Pipeline classifiers are classifiers that have at least one version and are not archived.
    """
    orm_classifier = (
        session.query(models.Classifiers)
        .filter(models.Classifiers.project_id == project_id)
        .filter(models.Classifiers.id == classifier_id)
        .filter(models.Classifiers.archived_at.is_(None))
        .first()
    )

    if orm_classifier is None:
        return None

    # Pipeline classifiers must have a version
    if orm_classifier.latest_version is None:
        return None

    return response_schemas.classifier_pipeline_adapter.validate_python(orm_classifier)


def get_pipeline_classifiers(
    session: sqlalchemy.orm.Session,
    project_id: int,
    include_single_run_classifiers: bool = False,
) -> list[response_schemas.ClassifierPipeline]:
    """Get a list of pipeline classifiers for a project.

    Pipeline classifiers are classifiers that have at least one version and are not archived.

    By default single run classified are not included. This is because they are not used in the
    pipeline when we need to re run a classifier for a gather.

    Args:
        session: SQLAlchemy session.
        project_id: Project ID.
        include_single_run_classifiers: Include single run classifiers.

    Returns:
        List of pipeline classifiers.
    """
    query = (
        session.query(models.Classifiers)
        .filter(models.Classifiers.project_id == project_id)
        .filter(models.Classifiers.archived_at.is_(None))
    )
    if not include_single_run_classifiers:
        query = query.filter(
            models.Classifiers.type.notin_(base_schemas.SINGLE_RUN_CLASSIFIER_TYPES)
        )

    orm_classifiers = (
        query
        # The order will be the order that they where added
        .order_by(models.Classifiers.id.asc()).all()
    )

    return [
        response_schemas.classifier_pipeline_adapter.validate_python(orm_classifier)
        for orm_classifier in orm_classifiers
        # Pipeline classifiers have to have at least one version
        if orm_classifier.latest_version is not None
    ]


def get_classifiers(
    session: sqlalchemy.orm.Session,
    project_id: int,
    start: int = 0,
    end: int = 10,
    exclude_archived: bool = False,
) -> list[response_schemas.ClassifierSummary]:
    """Get a list of classifiers for a project."""
    query = session.query(models.Classifiers).filter(models.Classifiers.project_id == project_id)
    if exclude_archived:
        query = query.filter(models.Classifiers.archived_at.is_(None))

    # Order and limit have to be after the where
    query = query.order_by(models.Classifiers.id.desc()).slice(start, end)
    return [
        response_schemas.ClassifierSummary.model_validate(orm_classifier)
        for orm_classifier in query.all()
    ]


def patch_classifier(
    session: sqlalchemy.orm.Session,
    project_id: int,
    classifier_id: int,
    classifier_patch: base_schemas.ClassifierPatch,
) -> response_schemas.ClassifierDetail:
    """Patch a classifier."""
    with get_orm_classifier_with_edited_context(
        session, project_id, classifier_id
    ) as orm_classifier:
        for key, value in classifier_patch.dict(exclude_unset=True).items():
            setattr(orm_classifier, key, value)

        session.commit()

    session.refresh(orm_classifier)
    return response_schemas.classifier_detail_adapter.validate_python(orm_classifier)


def archive_classifier(
    session: sqlalchemy.orm.Session,
    project_id: int,
    classifier_id: int,
) -> models.Classifiers:
    """Archive a classifier."""
    orm_classifier = get_orm_classifier(session, project_id, classifier_id)

    if orm_classifier is None:
        raise exceptions.ClassifierNotFound()

    if orm_classifier.latest_version is None:
        raise exceptions.HttpException400("Classifier has no versions and cannot be archived.")

    orm_classifier.archived_at = datetime.datetime.utcnow()
    session.commit()
    session.refresh(orm_classifier)

    return orm_classifier


async def archive_classifier_run_archive_job(
    session: sqlalchemy.orm.Session,
    project_id: int,
    classifier_id: int,
) -> response_schemas.ClassifierDetail:
    """Archive a classifier and run the classifier archive job."""
    orm_classifier = archive_classifier(session, project_id, classifier_id)

    _ = await job_run_crud.create_and_run_job_run(
        session,
        project_id,
        job_run_schemas.JobRunCreate(
            foreign_id=orm_classifier.id,
            foreign_job_type=job_run_schemas.ForeignJobType.classifier_archive,
        ),
    )
    return response_schemas.classifier_detail_adapter.validate_python(orm_classifier)


def restore_classifier(
    session: sqlalchemy.orm.Session,
    project_id: int,
    classifier_id: int,
) -> response_schemas.ClassifierDetail:
    """Restore a classifier."""
    orm_classifier = get_orm_classifier(session, project_id, classifier_id)

    if orm_classifier is None:
        raise exceptions.ClassifierNotFound()

    orm_classifier.archived_at = None
    session.commit()
    session.refresh(orm_classifier)
    return response_schemas.classifier_detail_adapter.validate_python(orm_classifier)


async def restore_classifier_run_restore_job(
    session: sqlalchemy.orm.Session,
    project_id: int,
    classifier_id: int,
) -> response_schemas.ClassifierDetail:
    """Restore a classifier and run the classifier restore job."""
    orm_classifier = restore_classifier(session, project_id, classifier_id)

    _ = await job_run_crud.create_and_run_job_run(
        session,
        project_id,
        job_run_schemas.JobRunCreate(
            foreign_id=orm_classifier.id,
            foreign_job_type=job_run_schemas.ForeignJobType.classifier_restore,
        ),
    )
    return response_schemas.classifier_detail_adapter.validate_python(orm_classifier)


def patch_intermediatory_class(
    session: sqlalchemy.orm.Session,
    project_id: int,
    classifier_id: int,
    class_id: int,
    class_patch: base_schemas.IntermediatoryClassPatch,
) -> base_schemas.IntermediatoryClassResponse:
    """Patch a class."""
    with get_orm_classifier_with_edited_context(
        session, project_id, classifier_id
    ) as orm_classifier:
        orm_class = (
            session.query(models.IntermediatoryClasses)
            .filter(models.IntermediatoryClasses.classifier_id == orm_classifier.id)
            .filter(models.IntermediatoryClasses.id == class_id)
            .one_or_none()
        )

        if orm_class is None:
            raise exceptions.IntermediatoryClassNotFound()
        try:
            for key, value in class_patch.dict(exclude_unset=True).items():
                setattr(orm_class, key, value)

            session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            session.rollback()
            if "unique constraint" in str(e).lower():
                raise exceptions.IntermediatoryClassNameConflict()
            raise exceptions.UnknownIntegrityError()

    session.refresh(orm_class)
    return base_schemas.IntermediatoryClassResponse.model_validate(orm_class)


def delete_intermediatory_class(
    session: sqlalchemy.orm.Session,
    project_id: int,
    classifier_id: int,
    class_id: int,
) -> None:
    """Delete an intermediatory class."""
    with get_orm_classifier_with_edited_context(
        session, project_id, classifier_id
    ) as orm_classifier:
        orm_class = (
            session.query(models.IntermediatoryClasses)
            .filter(models.IntermediatoryClasses.classifier_id == orm_classifier.id)
            .filter(models.IntermediatoryClasses.id == class_id)
            .one_or_none()
        )

        if orm_class is None:
            raise exceptions.IntermediatoryClassNotFound()

        session.delete(orm_class)
        session.commit()


def create_intermediatory_class(
    session: sqlalchemy.orm.Session,
    project_id: int,
    classifier_id: int,
    class_create: base_schemas.IntermediatoryClassCreate,
) -> base_schemas.IntermediatoryClassResponse:
    """Create an intermediatory class."""
    with get_orm_classifier_with_edited_context(
        session, project_id, classifier_id
    ) as orm_classifier:
        try:
            # Attempt to add an object that may violate the unique constraint
            orm_class = models.IntermediatoryClasses(
                classifier_id=orm_classifier.id,
                name=class_create.name,
                description=class_create.description,
            )
            session.add(orm_class)
            session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            session.rollback()
            if "unique constraint" in str(e).lower():
                raise exceptions.IntermediatoryClassNameConflict()
            raise exceptions.UnknownIntegrityError()

    session.refresh(orm_class)
    return base_schemas.IntermediatoryClassResponse.model_validate(orm_class)
