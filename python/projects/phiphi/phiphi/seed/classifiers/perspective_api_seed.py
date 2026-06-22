"""Classifier Perspective api seed."""

from sqlalchemy.orm import Session

from phiphi.api.projects.classifiers import bucketing_schemas
from phiphi.api.projects.classifiers.perspective_api import crud, schemas

TEST_PERSPECTIVE_API_NOT_RUN = schemas.PerspectiveAPIClassifierCreate(
    name="Test Perspective API Classifier 1",
    description="Test Classifier 1 Description",
    latest_version=schemas.PerspectiveAPIVersionBase(
        params=schemas.PerspectiveAPIParams(
            toxicity=schemas.PerspectiveAttributeConfig(
                enabled=True,
                buckets=[
                    bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
                    bucketing_schemas.BucketThreshold(name="high", upper_threshold=1.0),
                ],
            )
        )
    ),
)

TEST_PERSPECTIVE_API_CLASSIFIERS: list[schemas.PerspectiveAPIClassifierDetail] = []


def seed_test_classifiers_perspective_api(session: Session) -> None:
    """Seed perspective api classifiers."""
    TEST_PERSPECTIVE_API_CLASSIFIERS.clear()
    classifier = crud.create_and_version(
        session=session,
        project_id=2,
        classifier_create=TEST_PERSPECTIVE_API_NOT_RUN,
    )
    TEST_PERSPECTIVE_API_CLASSIFIERS.append(classifier)
