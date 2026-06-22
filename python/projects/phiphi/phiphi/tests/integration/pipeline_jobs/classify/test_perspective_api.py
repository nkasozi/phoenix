"""Integration test for the Perspective API classification module.

This test verifies the Perspective API classification flow by:
1) Writing a small set of deduplicated messages to BigQuery.
2) Adding some rows to `classified_messages` beforehand, to simulate:
   - One message already classified by this same classifier/version (should be skipped).
   - One message classified by a different classifier; should *not* be skipped for this classifier.
   And adding a row to `classified_messages_errors` beforehand, to simulate:
   - One message that was already added as an error (should be skipped).
3) Defining a `perspective_api`-type classifier with multiple enabled attributes.
4) Patching:
   - The batch size to 2, forcing multiple fetches from BigQuery.
   - The actual Perspective API calls (to return mocked responses).
   - The `get_unclassified_messages` function to track the number of times a batch is pulled.
5) Invoking the classification flow.
6) Checking that only the unclassified messages get classified (and that we see two batches),
   and verifying the resulting rows in `classified_messages` match our expectation.
"""

import datetime
import json
from unittest.mock import patch

import pandas as pd
import pandas_gbq
import pytest
from pandas.testing import assert_frame_equal

from phiphi import config
from phiphi.pipeline_jobs import constants
from phiphi.pipeline_jobs import utils as pipeline_jobs_utils
from phiphi.pipeline_jobs.classify import flow as classify_flow
from phiphi.pipeline_jobs.classify import perspective_api


@pytest.mark.integration
@pytest.mark.asyncio
async def test_perspective_api_task(tmp_bq_project):
    """Test Perspective API classification flow.

    Steps:
      1) Write five deduplicated messages to BigQuery:
         - msg_1, msg_2, msg_3 (unclassified by our target classifier).
         - msg_already_classified (already classified by the same classifier).
         - msg_different_classifier (classified by a *different* classifier).
      2) Add pre-existing rows in `classified_messages` for:
         - msg_already_classified with classifier_id=101 / version=2 (so it will be skipped).
         - msg_different_classifier with classifier_id=999 / version=1 (doesn't skip for 101/2).
      3) Define a `perspective_api` classifier with two attributes (toxicity, insult).
      4) Patch:
         - BATCH_SIZE=2 (forcing two fetches for the 4 unclassified messages).
         - `perspective_api.call_perspective_api` to mock the API.
         - `perspective_api.get_unclassified_messages` to count how many times it's called.
      5) Invoke `classify_flow.classify_flow`.
      6) Assert the API was called exactly 4 times (one per newly unclassified message).
      7) Assert `get_unclassified_messages` was called exactly twice (two batches).
      8) Assert final `classified_messages` in BQ matches the expected DataFrame.
      9) Assert final `classified_messages_errors` in BQ matches the expected DataFrame.
    """
    # We do real BQ operations, so check that it's enabled
    if config.settings.USE_MOCK_BQ:
        raise Exception(
            "This test requires USE_MOCK_BQ to be set to False. "
            "Please set this in python/projects/phiphi/docker_env.dev."
        )

    # 1) Create five generalised messages - minimal columns required for test:
    generalised_messages_df = pd.DataFrame(
        {
            "pi_text": [
                "I love puppies",  # unclassified => should classify
                "You are dumb",  # unclassified => should classify
                "I hate everyone and everything",  # unclassified => should classify
                "I love cats",  # already classified by classifier 101 v2 => skip
                "I love dogs",  # already classified by a different classifier => should classify
                "PERPECTIVE_API_ERROR",  # should return an error data row
                "I was already errored",  # should be skipped due to existing error row
            ],
            "phoenix_platform_message_id": [
                "msg_1",
                "msg_2",
                "msg_3",
                "msg_already_classified",
                "msg_different_classifier",
                "msg_error",
                "msg_already_errored",
            ],
        }
    )

    pipeline_jobs_utils.write_data(
        df=generalised_messages_df,
        dataset=tmp_bq_project,
        table=constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME,
    )

    # 2) Insert pre-existing classified rows
    #    - msg_already_classified by classifier_id=101/version=2 => skip re-classification
    #      (2 rows, since that classifier has 2 enabled attributes)
    #    - msg_different_classifier by classifier_id=999/version=1 => should *not* skip
    pre_existing_classified_df = pd.DataFrame(
        {
            "phoenix_platform_message_id": [
                "msg_already_classified",
                "msg_already_classified",
                "msg_different_classifier",
            ],
            "classifier_id": [101, 101, 999],
            "classifier_version_id": [2, 2, 1],
            "class_name": ["high_toxicity", "high_insult", "other_classifier_class"],
            "class_probability": [0.9, 0.95, 0.5],
            "job_run_id": [999, 999, 88],
        }
    )
    pipeline_jobs_utils.write_data(
        df=pre_existing_classified_df,
        dataset=tmp_bq_project,
        table=constants.CLASSIFIED_MESSAGES_TABLE_NAME,
    )
    # Also insert a pre-existing error row for a message that will be skipped
    pre_existing_errors_df = pd.DataFrame(
        {
            "phoenix_platform_message_id": ["msg_already_errored"],
            "classifier_id": [101],
            "classifier_version_id": [2],
            "job_run_id": [777],
            "error_json": [
                json.dumps({"errors": [{"status_code": 500, "error_message": "boom"}]})
            ],
        }
    )
    pipeline_jobs_utils.write_data(
        df=pre_existing_errors_df,
        dataset=tmp_bq_project,
        table=constants.CLASSIFIED_MESSAGES_ERRORS_TABLE_NAME,
    )

    # 3) Define a classifier with two attributes
    test_perspective_api_classifier = {
        "id": 101,
        "project_id": 42,
        "name": "Test Perspective Classifier (Batch)",
        "description": "Classifier that detects toxicity & insults.",
        "type": "perspective_api",
        "latest_version": {
            "version_id": 2,
            "classifier_id": 101,
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
            "params": {
                "toxicity": {
                    "enabled": True,
                    "buckets": [
                        {"name": "low", "upper_threshold": 0.4},
                        {"name": "medium", "upper_threshold": 0.7},
                        {"name": "high", "upper_threshold": 1.0},
                    ],
                },
                "insult": {
                    "enabled": True,
                    "buckets": [
                        {"name": "low", "upper_threshold": 0.4},
                        {"name": "medium", "upper_threshold": 0.8},
                        {"name": "high", "upper_threshold": 1.0},
                    ],
                },
            },
        },
    }

    # Mock the Perspective API for each text we expect to classify:
    # (msg_1, msg_2, msg_3, msg_different_classifier)
    def mock_call_perspective_api(
        text: str, attributes: list
    ) -> perspective_api.PerspectiveAPIResponse | perspective_api.PerspectiveAPIErrorResponse:
        if text == "I love puppies":
            return perspective_api.PerspectiveAPIResponse(
                attribute_scores={
                    "TOXICITY": perspective_api.PerspectiveAPIAttributeScore(
                        summary_score=perspective_api.PerspectiveAPIAttributeSummaryScore(
                            value=0.1, type="PROBABILITY"
                        )
                    ),
                    "INSULT": perspective_api.PerspectiveAPIAttributeScore(
                        summary_score=perspective_api.PerspectiveAPIAttributeSummaryScore(
                            value=0.2, type="PROBABILITY"
                        )
                    ),
                },
                languages=["en"],
            )
        elif text == "You are dumb":
            return perspective_api.PerspectiveAPIResponse(
                attribute_scores={
                    "TOXICITY": perspective_api.PerspectiveAPIAttributeScore(
                        summary_score=perspective_api.PerspectiveAPIAttributeSummaryScore(
                            value=0.5, type="PROBABILITY"
                        )
                    ),
                    "INSULT": perspective_api.PerspectiveAPIAttributeScore(
                        summary_score=perspective_api.PerspectiveAPIAttributeSummaryScore(
                            value=0.6, type="PROBABILITY"
                        )
                    ),
                },
                languages=["en"],
            )
        elif text == "I hate everyone and everything":
            return perspective_api.PerspectiveAPIResponse(
                attribute_scores={
                    "TOXICITY": perspective_api.PerspectiveAPIAttributeScore(
                        summary_score=perspective_api.PerspectiveAPIAttributeSummaryScore(
                            value=0.9, type="PROBABILITY"
                        )
                    ),
                    "INSULT": perspective_api.PerspectiveAPIAttributeScore(
                        summary_score=perspective_api.PerspectiveAPIAttributeSummaryScore(
                            value=0.95, type="PROBABILITY"
                        )
                    ),
                },
                languages=["en"],
            )
        elif text == "I love dogs":
            return perspective_api.PerspectiveAPIResponse(
                attribute_scores={
                    "TOXICITY": perspective_api.PerspectiveAPIAttributeScore(
                        summary_score=perspective_api.PerspectiveAPIAttributeSummaryScore(
                            value=0.2, type="PROBABILITY"
                        )
                    ),
                    "INSULT": perspective_api.PerspectiveAPIAttributeScore(
                        summary_score=perspective_api.PerspectiveAPIAttributeSummaryScore(
                            value=0.25, type="PROBABILITY"
                        )
                    ),
                },
                languages=["en"],
            )
        elif text == "PERPECTIVE_API_ERROR":
            return perspective_api.PerspectiveAPIErrorResponse(
                payload={
                    "comment": {"text": text},
                    "requestedAttributes": {"TOXICITY": {}, "INSULT": {}},
                },
                errors=[
                    perspective_api.PerspectiveAPISingleErrorResponse(
                        status_code=429,
                        response_json={"error": {"code": 429, "message": "Rate limit exceeded"}},
                        error_message="Rate limit exceeded while calling Perspective API",
                    ),
                    perspective_api.PerspectiveAPISingleErrorResponse(
                        status_code=500,
                        response_json={"error": {"code": 500, "message": "Internal server error"}},
                        error_message="Internal error on Perspective API",
                    ),
                ],
            )
        else:
            # If we ever get here with text we didn't expect, raise an error
            # This catches if the functionality attempts to classify a message is shouldn't
            raise ValueError(f"Unexpected text passed to mocked API: {text}")

    # We'll track calls to `get_unclassified_messages` so we can confirm it was called twice
    real_get_unclassified_messages = perspective_api.get_unclassified_messages

    def wrapped_get_unclassified_messages(*args, **kwargs):
        return real_get_unclassified_messages(*args, **kwargs)

    with (
        patch.object(
            perspective_api, "call_perspective_api", side_effect=mock_call_perspective_api
        ) as mock_api,
        patch.object(perspective_api, "BATCH_SIZE", new=2),
        patch.object(
            perspective_api,
            "get_unclassified_messages",
            side_effect=wrapped_get_unclassified_messages,
        ) as mock_get_unclass,
    ):
        # 5) Invoke the classification flow
        await classify_flow.classify_flow(
            classifier_dict=test_perspective_api_classifier,
            project_namespace=tmp_bq_project,
            job_run_id=1234,
        )

        # 6) Assert we called the API exactly 5 times (one per newly unclassified message)
        assert mock_api.call_count == 5

        # 7) Confirm get_unclassified_messages was called twice (due to BATCH_SIZE=2, 4 messages)
        #    The first 2 unclassified messages in the first batch,
        #    then the last 2 in the second batch
        #    then one last message that is only an error
        assert mock_get_unclass.call_count == 3

    # 8) Check final contents of `classified_messages`
    actual_classified_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {tmp_bq_project}.{constants.CLASSIFIED_MESSAGES_TABLE_NAME}"
    )

    # We expect:
    #   - 2 old rows for msg_already_classified (classifier_id=101, version=2)
    #   - 1 old row for msg_different_classifier (classifier_id=999, version=1)
    #   - 2 new rows for msg_1 (toxicity & insult)
    #   - 2 new rows for msg_2
    #   - 2 new rows for msg_3
    #   - 2 new rows for msg_different_classifier (since it's unclassified by 101/2)
    # Total = 11 rows.
    # We'll build the expected DataFrame:
    expected_data = [
        # Pre-existing: msg_already_classified (2 rows)
        {
            "classifier_id": 101,
            "classifier_version_id": 2,
            "class_name": "high_toxicity",
            "phoenix_platform_message_id": "msg_already_classified",
            "job_run_id": 999,
            "class_probability": 0.9,
        },
        {
            "classifier_id": 101,
            "classifier_version_id": 2,
            "class_name": "high_insult",
            "phoenix_platform_message_id": "msg_already_classified",
            "job_run_id": 999,
            "class_probability": 0.95,
        },
        # Pre-existing: msg_different_classifier (1 row)
        {
            "classifier_id": 999,
            "classifier_version_id": 1,
            "class_name": "other_classifier_class",
            "phoenix_platform_message_id": "msg_different_classifier",
            "job_run_id": 88,
            "class_probability": 0.5,
        },
        # Newly classified for msg_1
        {
            "classifier_id": 101,
            "classifier_version_id": 2,
            "class_name": "low_toxicity",
            "phoenix_platform_message_id": "msg_1",
            "job_run_id": 1234,
            "class_probability": 0.1,
        },
        {
            "classifier_id": 101,
            "classifier_version_id": 2,
            "class_name": "low_insult",
            "phoenix_platform_message_id": "msg_1",
            "job_run_id": 1234,
            "class_probability": 0.2,
        },
        # Newly classified for msg_2
        {
            "classifier_id": 101,
            "classifier_version_id": 2,
            "class_name": "medium_toxicity",
            "phoenix_platform_message_id": "msg_2",
            "job_run_id": 1234,
            "class_probability": 0.5,
        },
        {
            "classifier_id": 101,
            "classifier_version_id": 2,
            "class_name": "medium_insult",
            "phoenix_platform_message_id": "msg_2",
            "job_run_id": 1234,
            "class_probability": 0.6,
        },
        # Newly classified for msg_3
        {
            "classifier_id": 101,
            "classifier_version_id": 2,
            "class_name": "high_toxicity",
            "phoenix_platform_message_id": "msg_3",
            "job_run_id": 1234,
            "class_probability": 0.9,
        },
        {
            "classifier_id": 101,
            "classifier_version_id": 2,
            "class_name": "high_insult",
            "phoenix_platform_message_id": "msg_3",
            "job_run_id": 1234,
            "class_probability": 0.95,
        },
        # Newly classified for msg_different_classifier
        {
            "classifier_id": 101,
            "classifier_version_id": 2,
            "class_name": "low_toxicity",
            "phoenix_platform_message_id": "msg_different_classifier",
            "job_run_id": 1234,
            "class_probability": 0.2,
        },
        {
            "classifier_id": 101,
            "classifier_version_id": 2,
            "class_name": "low_insult",
            "phoenix_platform_message_id": "msg_different_classifier",
            "job_run_id": 1234,
            "class_probability": 0.25,
        },
    ]
    expected_df = pd.DataFrame(expected_data)
    # Sort both actual and expected by a consistent key to compare
    sort_cols = [
        "classifier_id",
        "classifier_version_id",
        "class_name",
        "phoenix_platform_message_id",
        "job_run_id",
    ]
    actual_sorted = actual_classified_df.sort_values(by=sort_cols).reset_index(drop=True)
    expected_sorted = expected_df.sort_values(by=sort_cols).reset_index(drop=True)

    print(actual_sorted["class_name"])
    print(expected_sorted["class_name"])
    assert_frame_equal(
        actual_sorted,
        expected_sorted,
        check_dtype=False,
    )

    # 9) Check final contents of `classified_messages_errors`
    actual_errors_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {tmp_bq_project}.{constants.CLASSIFIED_MESSAGES_ERRORS_TABLE_NAME} "
        "ORDER BY phoenix_platform_message_id"
    )
    assert len(actual_errors_df) == 2  # pre-existing + new error
    error_row = actual_errors_df.iloc[1]
    assert error_row["phoenix_platform_message_id"] == "msg_error"
    assert error_row["classifier_id"] == 101
    assert error_row["classifier_version_id"] == 2
    assert error_row["job_run_id"] == 1234
    parsed_error = json.loads(error_row["error_json"])
    assert parsed_error["errors"][0]["status_code"] == 429
    assert "Rate limit exceeded" in parsed_error["errors"][0]["error_message"]
    assert parsed_error["errors"][1]["status_code"] == 500
    assert "Internal error" in parsed_error["errors"][1]["error_message"]
