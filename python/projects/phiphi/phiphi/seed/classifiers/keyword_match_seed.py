"""Classifier Keyword match seed."""

import datetime

from sqlalchemy.orm import Session

from phiphi.api.projects import classifiers
from phiphi.api.projects.classifiers import base_schemas, response_schemas
from phiphi.api.projects.classifiers.keyword_match import crud, schemas

TEST_KEYWORD_CLASSIFIER_CREATE_NO_VERSION = base_schemas.ClassifierWithIntermediatoryCreate(
    name="Test keyword match Classifier 1 no version",
    description="Test Classifier 1 Description",
    intermediatory_classes=[
        base_schemas.IntermediatoryClassCreate(
            name="Test Class 1",
            description="Test Class 1 Description",
        ),
        base_schemas.IntermediatoryClassCreate(
            name="Test Class 2",
            description="Test Class 2 Description",
        ),
    ],
)

TEST_KEYWORD_CLASSIFIER_CREATE_ARCHIVED = base_schemas.ClassifierWithIntermediatoryCreate(
    name="Test keyword match Classifier 2 Running Archived",
    description="Test Classifier 2 Description",
    intermediatory_classes=[
        base_schemas.IntermediatoryClassCreate(
            name="Test Class 1",
            description="Test Class 1 Description",
        ),
        base_schemas.IntermediatoryClassCreate(
            name="Test Class 2",
            description="Test Class 2 Description",
        ),
    ],
)

TEST_KEYWORD_CLASSIFIER_CREATE_VERSIONED = base_schemas.ClassifierWithIntermediatoryCreate(
    name="Test keyword match Classifier 3 Versioned",
    description="Test Classifier 3 Description",
    intermediatory_classes=[
        base_schemas.IntermediatoryClassCreate(
            name="Test Class 1",
            description="Test Class 1 Description",
        ),
        base_schemas.IntermediatoryClassCreate(
            name="Test Class 2",
            description="Test Class 2 Description",
        ),
    ],
)

# Needed for the console development
TEST_KEYWORD_CLASSIFIER_CREATE_VERSION_COMPLETED = base_schemas.ClassifierWithIntermediatoryCreate(
    name="Test keyword match Classifier 4 Versioned Completed",
    description="Test Classifier 4 Description",
    intermediatory_classes=[
        base_schemas.IntermediatoryClassCreate(
            name="Test Class 1",
            description="Test Class 1 Description",
        ),
        base_schemas.IntermediatoryClassCreate(
            name="Test Class 2",
            description="Test Class 2 Description",
        ),
    ],
)

# Needed for the console development
TEST_KEYWORD_CLASSIFIER_CREATE_VERSION_FAILED = base_schemas.ClassifierWithIntermediatoryCreate(
    name="Test keyword match Classifier 5 Versioned Failed",
    description="Test Classifier 5 Description",
    intermediatory_classes=[
        base_schemas.IntermediatoryClassCreate(
            name="Test Class 1",
            description="Test Class 1 Description",
        ),
        base_schemas.IntermediatoryClassCreate(
            name="Test Class 2",
            description="Test Class 2 Description",
        ),
    ],
)

# Needed for the console development
TEST_KEYWORD_CLASSIFIER_COMPLETED_ARCHIVED = base_schemas.ClassifierWithIntermediatoryCreate(
    name="Test keyword match Classifier 6 Archived Completed",
    description="Test Classifier 6 Description",
    intermediatory_classes=[
        base_schemas.IntermediatoryClassCreate(
            name="Test Class 1",
            description="Test Class 1 Description",
        ),
        base_schemas.IntermediatoryClassCreate(
            name="Test Class 2",
            description="Test Class 2 Description",
        ),
    ],
)

# Needed for the console development
TEST_KEYWORD_CLASSIFIER_FAILED_ARCHIVED = base_schemas.ClassifierWithIntermediatoryCreate(
    name="Test keyword match Classifier 7 Archived Failed",
    description="Test Classifier 7 Description",
    intermediatory_classes=[
        base_schemas.IntermediatoryClassCreate(
            name="Test Class 1",
            description="Test Class 1 Description",
        ),
        base_schemas.IntermediatoryClassCreate(
            name="Test Class 2",
            description="Test Class 2 Description",
        ),
    ],
)

# Needed for the console development
TEST_KEYWORD_CLASSIFIER_CREATE_VERSION_RESTORE_RUNNING = (
    base_schemas.ClassifierWithIntermediatoryCreate(
        name="Test keyword match Classifier 8 Versioned Restore Running",
        description="Test Classifier 8 Description",
        intermediatory_classes=[
            base_schemas.IntermediatoryClassCreate(
                name="Test Class 1",
                description="Test Class 1 Description",
            ),
            base_schemas.IntermediatoryClassCreate(
                name="Test Class 2",
                description="Test Class 2 Description",
            ),
        ],
    )
)

# Needed for the console development
TEST_KEYWORD_CLASSIFIER_CREATE_VERSION_RESTORE_COMPLETED = (
    base_schemas.ClassifierWithIntermediatoryCreate(
        name="Test keyword match Classifier 9 Versioned Restore Completed",
        description="Test Classifier 9 Description",
        intermediatory_classes=[
            base_schemas.IntermediatoryClassCreate(
                name="Test Class 1",
                description="Test Class 1 Description",
            ),
            base_schemas.IntermediatoryClassCreate(
                name="Test Class 2",
                description="Test Class 2 Description",
            ),
        ],
    )
)

# Needed for the console development
TEST_KEYWORD_CLASSIFIER_CREATE_VERSION_RESTORE_FAILED = (
    base_schemas.ClassifierWithIntermediatoryCreate(
        name="Test keyword match Classifier 10 Versioned Restore Failed",
        description="Test Classifier 10 Description",
        intermediatory_classes=[
            base_schemas.IntermediatoryClassCreate(
                name="Test Class 1",
                description="Test Class 1 Description",
            ),
            base_schemas.IntermediatoryClassCreate(
                name="Test Class 2",
                description="Test Class 2 Description",
            ),
        ],
    )
)

# Needed for the console development
TEST_KEYWORD_CLASSIFIER_CREATE_VERSION_COMPLETED_EDITED = (
    base_schemas.ClassifierWithIntermediatoryCreate(
        name="Test keyword match Classifier 11 Versioned Completed Edited",
        description="Test Classifier 11 Description",
        intermediatory_classes=[
            base_schemas.IntermediatoryClassCreate(
                name="Test Class 1",
                description="Test Class 1 Description",
            ),
            base_schemas.IntermediatoryClassCreate(
                name="Test Class 2",
                description="Test Class 2 Description",
            ),
        ],
    )
)


TEST_KEYWORD_CLASSIFIERS: list[schemas.KeywordMatchClassifierDetail] = []


def create_archived_classifier(
    session: Session,
    project_id: int,
    classifier_create: base_schemas.ClassifierWithIntermediatoryCreate,
) -> schemas.KeywordMatchClassifierDetail:
    """Create an archived classifier."""
    classifier = classifiers.crud.create_classifier(
        session=session,
        project_id=project_id,
        classifier_type=base_schemas.ClassifierType.keyword_match,
        classifier_create=classifier_create,
    )
    crud.create_version(
        session=session,
        project_id=project_id,
        classifier_id=classifier.id,
    )
    classifiers.crud.archive_classifier(
        session=session,
        project_id=project_id,
        classifier_id=classifier.id,
    )
    classifier_archived = classifiers.crud.get_classifier(
        session=session,
        project_id=project_id,
        classifier_id=classifier.id,
    )
    # Need for mypy
    assert isinstance(classifier_archived, schemas.KeywordMatchClassifierDetail)
    return classifier_archived


def create_versioned_classifier(
    session: Session,
    project_id: int,
    classifier_create: base_schemas.ClassifierWithIntermediatoryCreate,
) -> schemas.KeywordMatchClassifierDetail:
    """Create a versioned classifier."""
    classifier = classifiers.crud.create_classifier(
        session=session,
        project_id=project_id,
        classifier_type=base_schemas.ClassifierType.keyword_match,
        classifier_create=classifier_create,
    )
    crud.create_version(
        session=session,
        project_id=project_id,
        classifier_id=classifier.id,
    )
    # Need to refresh the classifier to get the latest version
    classifier_versioned = classifiers.crud.get_classifier(
        session=session,
        project_id=project_id,
        classifier_id=classifier.id,
    )
    # Need for mypy
    assert isinstance(classifier_versioned, schemas.KeywordMatchClassifierDetail)
    return classifier_versioned


def create_test_intermediatory_class_to_keyword_config(
    session: Session,
    classifier: response_schemas.ClassifierDetail,
    class_id: int,
    musts: str,
    nots: str | None = None,
) -> None:
    """Create test intermediatory class to keyword config.

    This will update `last_edited_at` of the classifier.
    """
    intermediatory_class_to_keyword_config = schemas.IntermediatoryClassToKeywordConfigCreate(
        class_id=class_id,
        musts=musts,
        nots=nots,
    )
    crud.create_intermediatory_class_to_keyword_config(
        session=session,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        intermediatory_class_to_keyword_config=intermediatory_class_to_keyword_config,
    )


def update_last_edit_at_classifier(
    session: Session,
    classifier: response_schemas.ClassifierDetail,
    add_timedelta: datetime.timedelta,
) -> schemas.KeywordMatchClassifierDetail:
    """Update the last edited at of the classifier."""
    orm_classifier = classifiers.crud.get_orm_classifier(
        session=session,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    assert orm_classifier
    base_date = datetime.datetime.now()
    if orm_classifier.last_edited_at is not None:
        base_date = orm_classifier.last_edited_at
    orm_classifier.last_edited_at = base_date + add_timedelta
    session.commit()
    classifier_versioned = classifiers.crud.get_classifier(
        session=session,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    # Need for mypy
    assert isinstance(classifier_versioned, schemas.KeywordMatchClassifierDetail)
    return classifier_versioned


def seed_test_classifier_keyword_match(session: Session) -> None:
    """Seed test keyword match classifier."""
    # Need to clear the list before seeding other wise every seed will add to the list
    TEST_KEYWORD_CLASSIFIERS.clear()
    classifiers_to_create = [TEST_KEYWORD_CLASSIFIER_CREATE_NO_VERSION]
    project_id = 1

    for classifier_create in classifiers_to_create:
        classifier = classifiers.crud.create_classifier(
            session=session,
            project_id=project_id,
            classifier_type=base_schemas.ClassifierType.keyword_match,
            classifier_create=classifier_create,
        )
        # Create intermediatory class to keyword config
        create_test_intermediatory_class_to_keyword_config(
            session=session,
            classifier=classifier,
            class_id=classifier.intermediatory_classes[0].id,
            musts="test1",
        )
        create_test_intermediatory_class_to_keyword_config(
            session=session,
            classifier=classifier,
            class_id=classifier.intermediatory_classes[1].id,
            musts="test2",
        )
        # Need to refresh the classifier to get the most updated orm
        classifier_with_intermediatory = classifiers.crud.get_classifier(
            session=session,
            project_id=project_id,
            classifier_id=classifier.id,
        )
        # Need for mypy
        assert isinstance(classifier_with_intermediatory, schemas.KeywordMatchClassifierDetail)
        TEST_KEYWORD_CLASSIFIERS.append(classifier_with_intermediatory)

    archived_classifier = create_archived_classifier(
        session=session,
        project_id=project_id,
        classifier_create=TEST_KEYWORD_CLASSIFIER_CREATE_ARCHIVED,
    )
    TEST_KEYWORD_CLASSIFIERS.append(archived_classifier)

    versioned_classifiers = [
        TEST_KEYWORD_CLASSIFIER_CREATE_VERSIONED,
        TEST_KEYWORD_CLASSIFIER_CREATE_VERSION_COMPLETED,
        TEST_KEYWORD_CLASSIFIER_CREATE_VERSION_FAILED,
    ]

    for classifier_create in versioned_classifiers:
        classifier_with_version = create_versioned_classifier(
            session=session,
            project_id=project_id,
            classifier_create=classifier_create,
        )
        TEST_KEYWORD_CLASSIFIERS.append(classifier_with_version)

    archived_classifiers = [
        TEST_KEYWORD_CLASSIFIER_COMPLETED_ARCHIVED,
        TEST_KEYWORD_CLASSIFIER_FAILED_ARCHIVED,
    ]
    for classifier_create in archived_classifiers:
        archived_classifier = create_archived_classifier(
            session=session,
            project_id=project_id,
            classifier_create=classifier_create,
        )
        TEST_KEYWORD_CLASSIFIERS.append(archived_classifier)

    # Job runs will be added in seed/job_runs.py
    versioned_classifiers_restored = [
        TEST_KEYWORD_CLASSIFIER_CREATE_VERSION_RESTORE_RUNNING,
        TEST_KEYWORD_CLASSIFIER_CREATE_VERSION_RESTORE_COMPLETED,
        TEST_KEYWORD_CLASSIFIER_CREATE_VERSION_RESTORE_FAILED,
        TEST_KEYWORD_CLASSIFIER_CREATE_VERSION_COMPLETED_EDITED,
    ]

    for classifier_create in versioned_classifiers_restored:
        classifier_with_version = create_versioned_classifier(
            session=session,
            project_id=project_id,
            classifier_create=classifier_create,
        )
        TEST_KEYWORD_CLASSIFIERS.append(classifier_with_version)

    TEST_KEYWORD_CLASSIFIERS[10] = update_last_edit_at_classifier(
        session=session,
        classifier=TEST_KEYWORD_CLASSIFIERS[10],
        add_timedelta=datetime.timedelta(seconds=1),
    )
