"""Classifier Manual Post Authors seed."""

from sqlalchemy.orm import Session

from phiphi.api.projects import classifiers
from phiphi.api.projects.classifiers import base_schemas
from phiphi.api.projects.classifiers.manual_post_authors import crud, schemas

TEST_MANUAL_POST_AUTHORS_CREATE_NO_VERSION = base_schemas.ClassifierWithIntermediatoryCreate(
    name="Test manual_post_authors Classifier 1 no version",
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

TEST_MANUAL_POST_AUTHORS_CREATE_NO_VERSION_CLASSIFIED = (
    base_schemas.ClassifierWithIntermediatoryCreate(
        name="Test manual_post_authors Classifier 2 no version with intermediatory author classes",
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
)

TEST_MANUAL_POST_AUTHORS_CREATE_VERSION = base_schemas.ClassifierWithIntermediatoryCreate(
    name="Test manual_post_authors Classifier 3 version with intermediatory author classes",
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

TEST_MANUAL_POST_AUTHORS_CLASSIFIERS: list[schemas.ManualPostAuthorsClassifierDetail] = []


def create_intermediatory_author_classes(
    session: Session,
    classifier: schemas.ManualPostAuthorsClassifierDetail,
    intermediatory_author_class_creates: list[schemas.IntermediatoryAuthorClassCreate],
) -> schemas.ManualPostAuthorsClassifierDetail:
    """Create intermediatory classified post authors."""
    for create_obj in intermediatory_author_class_creates:
        _ = crud.create_intermediatory_author_class(
            session=session,
            project_id=classifier.project_id,
            classifier_id=classifier.id,
            create_obj=create_obj,
        )

    # Refresh classifier
    classifier_with_intermediatory = classifiers.crud.get_classifier(
        session, classifier.project_id, classifier.id
    )
    # Needed for mypy
    assert isinstance(classifier_with_intermediatory, schemas.ManualPostAuthorsClassifierDetail)
    return classifier_with_intermediatory


def seed_test_classifiers_manual_post_authors(session: Session) -> None:
    """Seed test classifiers."""
    TEST_MANUAL_POST_AUTHORS_CLASSIFIERS.clear()
    project_id = 2

    classifiers_create = [
        TEST_MANUAL_POST_AUTHORS_CREATE_NO_VERSION,
        TEST_MANUAL_POST_AUTHORS_CREATE_NO_VERSION_CLASSIFIED,
        TEST_MANUAL_POST_AUTHORS_CREATE_VERSION,
    ]

    for classifier_create in classifiers_create:
        classifier = classifiers.crud.create_classifier(
            session=session,
            project_id=project_id,
            classifier_type=base_schemas.ClassifierType.manual_post_authors,
            classifier_create=classifier_create,
        )
        assert isinstance(classifier, schemas.ManualPostAuthorsClassifierDetail)
        TEST_MANUAL_POST_AUTHORS_CLASSIFIERS.append(classifier)

    classifier_indexes_to_create_intermediatory = [1, 2]
    for index in classifier_indexes_to_create_intermediatory:
        classifier_to_create_intermediatory = TEST_MANUAL_POST_AUTHORS_CLASSIFIERS[index]
        TEST_MANUAL_POST_AUTHORS_CLASSIFIERS[index] = create_intermediatory_author_classes(
            session=session,
            classifier=classifier_to_create_intermediatory,
            intermediatory_author_class_creates=[
                schemas.IntermediatoryAuthorClassCreate(
                    class_id=classifier_to_create_intermediatory.intermediatory_classes[0].id,
                    # Using `id_1` as this is in the
                    # pipeline_jobs/sample_data/generalised_post_authors.json
                    phoenix_platform_message_author_id="id_1",
                ),
                schemas.IntermediatoryAuthorClassCreate(
                    class_id=classifier_to_create_intermediatory.intermediatory_classes[1].id,
                    # Using `id_1` as this is in the
                    # pipeline_jobs/sample_data/generalised_post_authors.json
                    phoenix_platform_message_author_id="id_1",
                ),
                schemas.IntermediatoryAuthorClassCreate(
                    class_id=classifier_to_create_intermediatory.intermediatory_classes[0].id,
                    phoenix_platform_message_author_id="id_3",
                ),
            ],
        )

    classifier_indexes_to_create_version = [2]
    for index in classifier_indexes_to_create_version:
        classifier_to_create_version = TEST_MANUAL_POST_AUTHORS_CLASSIFIERS[index]
        crud.create_version(
            session=session,
            project_id=project_id,
            classifier_id=classifier_to_create_version.id,
        )
        # Need to refresh the classifier to get the latest version
        classifier_versioned = classifiers.crud.get_classifier(
            session=session,
            project_id=project_id,
            classifier_id=classifier.id,
        )
        # Need for mypy
        assert isinstance(classifier_versioned, schemas.ManualPostAuthorsClassifierDetail)
        TEST_MANUAL_POST_AUTHORS_CLASSIFIERS[index] = classifier_versioned
