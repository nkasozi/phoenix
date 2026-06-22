"""Crud functionality for manual post authors."""

from collections import defaultdict

import sqlalchemy as sa

from phiphi import utils
from phiphi.api import base_schemas, exceptions
from phiphi.api.projects.classifiers import base_schemas as classifiers_base_schemas
from phiphi.api.projects.classifiers import crud
from phiphi.api.projects.classifiers import models as classifiers_models
from phiphi.api.projects.classifiers.manual_post_authors import models, schemas
from phiphi.api.projects.job_runs import crud as job_run_crud
from phiphi.api.projects.job_runs import schemas as job_run_schemas
from phiphi.pipeline_jobs import generalised_authors

UNIQUE_ERROR_MESSAGE = "The author id and class id pair already exists."


def create_version(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
) -> schemas.ManualPostAuthorsVersionResponse:
    """Create a manual post authors version."""
    orm_classifier = crud.get_orm_classifier(session, project_id, classifier_id)
    if orm_classifier is None:
        raise exceptions.ClassifierNotFound()

    if orm_classifier.type != classifiers_base_schemas.ClassifierType.manual_post_authors:
        raise exceptions.HttpException400(
            "The classifier is not a manual post authors classifier."
        )

    classes = crud.get_classes(session, orm_classifier)
    params = get_manual_post_authors_params(session, orm_classifier)

    orm_version = classifiers_models.ClassifierVersions(
        classifier_id=orm_classifier.id,
        classes=[class_label.model_dump() for class_label in classes],
        params=params,
    )
    session.add(orm_version)
    session.commit()
    session.refresh(orm_version)
    return schemas.ManualPostAuthorsVersionResponse.model_validate(orm_version)


def get_manual_post_authors_params(
    session: sa.orm.Session,
    orm_classifier: classifiers_models.Classifiers,
) -> schemas.ManaulPostAuthorsParams:
    """Get manual post authors."""
    all_configs = orm_classifier.intermediatory_author_classes
    author_classes = []
    for orm_intermediatory_author_class in all_configs:
        author_class = schemas.AuthorClassLabel(
            class_name=orm_intermediatory_author_class.class_name,
            phoenix_platform_message_author_id=orm_intermediatory_author_class.phoenix_platform_message_author_id,
        )
        author_classes.append(author_class)
    return schemas.ManaulPostAuthorsParams(author_classes=author_classes)


async def create_version_and_run(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
) -> schemas.ManualPostAuthorsClassifierDetail:
    """Create a manual post authors version and run."""
    orm_classifier = crud.get_orm_classifier(session, project_id, classifier_id)
    if orm_classifier is None:
        raise exceptions.ClassifierNotFound()
    _ = create_version(session, project_id, classifier_id)
    _ = await job_run_crud.create_and_run_job_run(
        session,
        project_id,
        job_run_schemas.JobRunCreate(
            foreign_id=orm_classifier.id,
            foreign_job_type=job_run_schemas.ForeignJobType.classify_tabulate,
        ),
    )
    session.refresh(orm_classifier)
    return schemas.ManualPostAuthorsClassifierDetail.model_validate(orm_classifier)


def create_intermediatory_author_class(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
    create_obj: schemas.IntermediatoryAuthorClassCreate,
) -> schemas.IntermediatoryAuthorClassResponse:
    """Create an intermediatory author class."""
    with crud.get_orm_classifier_with_edited_context(
        session=session, project_id=project_id, classifier_id=classifier_id
    ) as orm_classifier:
        if orm_classifier.type != classifiers_base_schemas.ClassifierType.manual_post_authors:
            raise exceptions.HttpException400("Invalid classifier type")

        orm_intermediate_class = session.query(classifiers_models.IntermediatoryClasses).get(
            create_obj.class_id
        )

        if orm_intermediate_class is None:
            raise exceptions.IntermediatoryClassNotFound()

        try:
            orm = models.IntermediatoryAuthorClasses(
                classifier_id=orm_classifier.id,
                class_id=create_obj.class_id,
                phoenix_platform_message_author_id=create_obj.phoenix_platform_message_author_id,
            )
            session.add(orm)
            session.commit()
        except sa.exc.IntegrityError as e:
            session.rollback()
            if "unique constraint" in str(e):
                raise exceptions.HttpException400(UNIQUE_ERROR_MESSAGE)
            raise exceptions.UnknownIntegrityError()
    session.refresh(orm_classifier)
    return schemas.IntermediatoryAuthorClassResponse.model_validate(orm)


def delete_intermediatory_author_class(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
    classified_post_author_id: int,
) -> None:
    """Delete an intermediatory author class."""
    with crud.get_orm_classifier_with_edited_context(
        session=session, project_id=project_id, classifier_id=classifier_id
    ) as orm_classifier:
        if orm_classifier.type != classifiers_base_schemas.ClassifierType.manual_post_authors:
            raise exceptions.HttpException400("Invalid classifier type")

        orm = (
            session.query(models.IntermediatoryAuthorClasses)
            .filter(models.IntermediatoryAuthorClasses.id == classified_post_author_id)
            .first()
        )
        if orm is None:
            raise exceptions.HttpException404("Intermediatory classified post author not found")
        session.delete(orm)
        session.commit()
    session.refresh(orm_classifier)
    return None


def get_post_authors_with_intermediatory_author_classes(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
    offset: int = 0,
    limit: int = 10,
) -> schemas.AuthorsListResponse:
    """Retrieve post authors with intermediatory_author_classes.

    Args:
        session (sa.orm.Session): The database session.
        project_id (int): The project id.
        classifier_id (int): The classifier id.
        offset (int, optional): Offset for pagination. Defaults to 0.
        limit (int, optional): Limit for pagination. Defaults to 10.

    Returns:
        schemas.AuthorsListResponse: The list of post authors with intermediatory_author_classes.
    """
    orm_classifier = crud.get_orm_classifier(
        session=session, project_id=project_id, classifier_id=classifier_id
    )
    if orm_classifier is None:
        raise exceptions.ClassifierNotFound()

    if orm_classifier.type != classifiers_base_schemas.ClassifierType.manual_post_authors:
        raise exceptions.HttpException400("Invalid classifier type")

    project_namespace = utils.get_project_namespace(project_id)
    post_authors_count = generalised_authors.get_total_count_post_authors(
        project_namespace=project_namespace
    )
    if post_authors_count == 0:
        return schemas.AuthorsListResponse(
            authors=[],
            meta=base_schemas.ListMeta(total_count=0, start_index=0, end_index=0),
        )

    post_authors_df = generalised_authors.get_post_authors(
        project_namespace=project_namespace, offset=offset, limit=limit
    )
    # Get list of phoenix_platform_message_author_ids from post_authors_df
    list_of_ids = post_authors_df["phoenix_platform_message_author_id"].tolist()

    # Query classified post authors filtered by the IDs
    intermediatory_author_classes = (
        session.query(models.IntermediatoryAuthorClasses)
        .filter(models.IntermediatoryAuthorClasses.classifier_id == orm_classifier.id)
        .filter(
            models.IntermediatoryAuthorClasses.phoenix_platform_message_author_id.in_(list_of_ids)
        )
        .all()
    )

    # Organize intermediatory author classes by phoenix_platform_message_author_id
    author_classes_dict = defaultdict(list)
    for item in intermediatory_author_classes:
        pid = item.phoenix_platform_message_author_id
        author_classes_dict[pid].append(
            schemas.IntermediatoryAuthorClassResponse.model_validate(item)
        )

    # Build response
    results = []
    for idx, row in post_authors_df.iterrows():
        pid = row["phoenix_platform_message_author_id"]
        intermediatory_author_classes_responses = author_classes_dict.get(pid, [])
        response = schemas.AuthorResponse(
            phoenix_platform_message_author_id=row["phoenix_platform_message_author_id"],
            pi_platform_message_author_id=row["pi_platform_message_author_id"],
            pi_platform_message_author_name=row["pi_platform_message_author_name"],
            phoenix_processed_at=row["phoenix_processed_at"],
            platform=row["platform"],
            post_count=row["post_count"],
            intermediatory_author_classes=intermediatory_author_classes_responses,
        )
        results.append(response)
    start_index = offset
    possible_end_index = offset + limit
    end_index = min(possible_end_index, post_authors_count)
    return schemas.AuthorsListResponse(
        authors=results,
        meta=base_schemas.ListMeta(
            total_count=post_authors_count, start_index=start_index, end_index=end_index
        ),
    )


def get_post_authors(
    session: sa.orm.Session,
    project_id: int,
    offset: int = 0,
    limit: int = 10,
) -> schemas.AuthorsListResponse:
    """Retrieve post authors with empty intermediatory_author_classes.

    Args:
        session (sa.orm.Session): The database session.
        project_id (int): The project id.
        offset (int, optional): Offset for pagination. Defaults to 0.
        limit (int, optional): Limit for pagination. Defaults to 10.

    Returns:
        schemas.AuthorsListResponse: The list of post authors with empty
            intermediatory_author_classes.
    """
    project_namespace = utils.get_project_namespace(project_id)
    post_authors_count = generalised_authors.get_total_count_post_authors(
        project_namespace=project_namespace
    )
    if post_authors_count == 0:
        return schemas.AuthorsListResponse(
            authors=[],
            meta=base_schemas.ListMeta(total_count=0, start_index=0, end_index=0),
        )

    post_authors_df = generalised_authors.get_post_authors(
        project_namespace=project_namespace, offset=offset, limit=limit
    )

    # Build response
    results = []
    for idx, row in post_authors_df.iterrows():
        response = schemas.AuthorResponse(
            phoenix_platform_message_author_id=row["phoenix_platform_message_author_id"],
            pi_platform_message_author_id=row["pi_platform_message_author_id"],
            pi_platform_message_author_name=row["pi_platform_message_author_name"],
            phoenix_processed_at=row["phoenix_processed_at"],
            platform=row["platform"],
            post_count=row["post_count"],
        )
        results.append(response)
    start_index = offset
    possible_end_index = offset + limit
    end_index = min(possible_end_index, post_authors_count)
    return schemas.AuthorsListResponse(
        authors=results,
        meta=base_schemas.ListMeta(
            total_count=post_authors_count, start_index=start_index, end_index=end_index
        ),
    )


def get_post_author_with_intermediatory_author_classes(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
    author_id: str,
) -> schemas.AuthorResponse:
    """Retrieve post author with intermediatory_author_classes.

    Args:
        session (sa.orm.Session): The database session.
        project_id (int): The project id.
        classifier_id (int): The classifier id.
        author_id (int): The author id.

    Returns:
        schemas.AuthorResponse: The post author with intermediatory_author_classes.
    """
    orm_classifier = crud.get_orm_classifier(
        session=session, project_id=project_id, classifier_id=classifier_id
    )
    if orm_classifier is None:
        raise exceptions.ClassifierNotFound()

    if orm_classifier.type != classifiers_base_schemas.ClassifierType.manual_post_authors:
        raise exceptions.HttpException400("Invalid classifier type")

    project_namespace = utils.get_project_namespace(project_id)
    post_authors_count = generalised_authors.get_total_count_post_authors(
        project_namespace=project_namespace
    )
    if post_authors_count == 0:
        raise exceptions.HttpException404("Post author not found")

    author = generalised_authors.get_author(
        project_namespace=project_namespace, phoenix_platform_message_author_id=author_id
    )

    if author is None:
        raise exceptions.HttpException404("Post author not found")

    # Query classified post authors filtered by the IDs
    intermediatory_author_classes = (
        session.query(models.IntermediatoryAuthorClasses)
        .filter(models.IntermediatoryAuthorClasses.classifier_id == orm_classifier.id)
        .filter(models.IntermediatoryAuthorClasses.phoenix_platform_message_author_id == author_id)
        .all()
    )

    intermediatory_author_classes_responses = [
        schemas.IntermediatoryAuthorClassResponse.model_validate(item)
        for item in intermediatory_author_classes
    ]

    return schemas.AuthorResponse(
        phoenix_platform_message_author_id=author["phoenix_platform_message_author_id"],
        pi_platform_message_author_id=author["pi_platform_message_author_id"],
        pi_platform_message_author_name=author["pi_platform_message_author_name"],
        phoenix_processed_at=author["phoenix_processed_at"],
        platform=author["platform"],
        post_count=author["post_count"],
        intermediatory_author_classes=intermediatory_author_classes_responses,
    )
