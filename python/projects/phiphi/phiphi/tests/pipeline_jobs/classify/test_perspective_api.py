"""Unit tests for the Perspective API classifier pipeline."""

import datetime
import logging
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from google.cloud import bigquery

from phiphi import utils
from phiphi.api.projects.classifiers import base_schemas, bucketing_schemas
from phiphi.api.projects.classifiers.perspective_api import schemas
from phiphi.pipeline_jobs.classify import perspective_api

utils.init_logging()

logger = logging.getLogger(__name__)


def manual_test_perspective_api_classify_message():
    """Manually test the perspective api call.

    To use this test:
    - ensure that a valid PERSPECTIVE_API_KEY is set in the config

    To use with docker environment:
    - in terminal `make up`
    - in new terminal `make bash_in_api`
    - Run the function:
    ```
    python -c \
        "from phiphi.tests.pipeline_jobs.classify import test_perspective_api; \
        test_perspective_api.manual_test_perspective_api_classify_message()"
    ```
    """
    text = "You are really not a nice person and I am going to get you."
    message_id = "12345"
    classifier = schemas.PerspectiveAPIClassifierPipeline(
        id=1,
        project_id=1,
        name="Test Classifier",
        description="Test classifier for Perspective API",
        type=base_schemas.ClassifierType.perspective_api,
        latest_version=schemas.PerspectiveAPIVersionResponse(
            classifier_id=1,
            created_at=datetime.datetime(2021, 1, 1, 0, 0, 0),
            updated_at=datetime.datetime(2021, 1, 1, 0, 0, 0),
            version_id=1,
            params=schemas.PerspectiveAPIParams(
                toxicity=schemas.PerspectiveAttributeConfig(
                    enabled=True,
                    buckets=[
                        bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
                        bucketing_schemas.BucketThreshold(name="high", upper_threshold=1.0),
                    ],
                ),
                severe_toxicity=schemas.PerspectiveAttributeConfig(
                    enabled=False,
                    buckets=[
                        bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
                        bucketing_schemas.BucketThreshold(name="high", upper_threshold=1.0),
                    ],
                ),
            ),
        ),
    )
    logger.info("Running manual_test_perspective_api_classify_message")
    logger.info(f"Text: {text}")
    logger.info(f"Message ID: {message_id}")
    logger.info(f"Classifier: {classifier}")
    response = perspective_api.classify_message(text, message_id, classifier)
    logger.info("Completed manual_test_perspective_api_classify_message with result:")
    logger.info(response)


@pytest.fixture
def test_classifier():
    """Return a test Perspective API classifier."""
    return schemas.PerspectiveAPIClassifierPipeline(
        id=1,
        project_id=1,
        name="Test Classifier",
        description="Test classifier for Perspective API",
        type=base_schemas.ClassifierType.perspective_api,
        latest_version=schemas.PerspectiveAPIVersionResponse(
            classifier_id=1,
            created_at=datetime.datetime(2021, 1, 1, 0, 0, 0),
            updated_at=datetime.datetime(2021, 1, 1, 0, 0, 0),
            version_id=1,
            params=schemas.PerspectiveAPIParams(
                toxicity=schemas.PerspectiveAttributeConfig(
                    enabled=True,
                    buckets=[
                        bucketing_schemas.BucketThreshold(name="low", upper_threshold=0.5),
                        bucketing_schemas.BucketThreshold(name="high", upper_threshold=1.0),
                    ],
                )
            ),
        ),
    )


@pytest.fixture
def mock_bigquery_client():
    """Return a mocked BigQuery client."""
    return Mock(spec=bigquery.Client)


@pytest.fixture
def mock_api_response():
    """Return a valid mock Perspective API response."""
    return perspective_api.PerspectiveAPIResponse(
        attribute_scores={
            "TOXICITY": perspective_api.PerspectiveAPIAttributeScore(
                summary_score=perspective_api.PerspectiveAPIAttributeSummaryScore(
                    value=0.8,
                    type="PROBABILITY",
                ),
                span_scores=[],
            )
        },
        languages=["en"],
    )


def test_extract_enabled_attributes(test_classifier):
    """Test extracting enabled attributes from the classifier params."""
    enabled_attrs = perspective_api.extract_enabled_attributes(
        test_classifier.latest_version.params
    )
    assert enabled_attrs == ["toxicity"]


def test_map_score_to_class(test_classifier):
    """Test mapping a score to a class name."""
    attribute_config = test_classifier.latest_version.params.toxicity
    class_name = perspective_api.map_score_to_class(0.8, "toxicity", attribute_config)
    assert class_name == "high_toxicity"


@patch("phiphi.pipeline_jobs.classify.perspective_api.call_perspective_api")
def test_classify_message(mock_call_api, test_classifier, mock_api_response):
    """Test classifying a message."""
    mock_call_api.return_value = mock_api_response

    result = perspective_api.classify_message(
        text="This is a test message.",
        message_id="12345",
        classifier=test_classifier,
    )
    assert len(result) == 1
    assert result[0]["class_name"] == "high_toxicity"
    assert result[0]["phoenix_platform_message_id"] == "12345"


def test_form_classified_messages_df():
    """Test forming a classified messages dataframe."""
    class_dicts = [
        {
            "phoenix_platform_message_id": "12345",
            "class_name": "high_toxicity",
            "attribute": "toxicity",
            "class_probability": 0.8,
        },
        {
            "phoenix_platform_message_id": "12345",
            "class_name": "high_flirtation",
            "attribute": "flirtation",
            "class_probability": 0.99,
        },
    ]
    expected_df = pd.DataFrame(
        {
            "classifier_id": [1, 1],
            "classifier_version_id": [1, 1],
            "class_name": ["high_toxicity", "high_flirtation"],
            "class_probability": [0.8, 0.99],
            "phoenix_platform_message_id": ["12345", "12345"],
            "job_run_id": [42, 42],
        }
    )
    result_df = perspective_api.form_classified_messages_df(
        class_dicts, classifier_id=1, classifier_version_id=1, job_run_id=42
    )
    pd.testing.assert_frame_equal(result_df, expected_df)
