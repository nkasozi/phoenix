"""Tests for the manual_uplaod normalise module."""

import json
from datetime import datetime

import pandas as pd
import pytest

from phiphi.api.projects.gathers import schemas
from phiphi.pipeline_jobs import generalised_messages
from phiphi.pipeline_jobs.gathers import manual_upload, normalise, normalisers
from phiphi.tests.pipeline_jobs.gathers.manual_upload import conftest

FROZEN_TIME = "2024-04-02T12:10:59.000Z"


@pytest.mark.freeze_time(FROZEN_TIME)
def test_normaliser_manual_upload():
    """Test normaliser for facebook posts function.

    Note: we use the `normalise_batch` function from the `normalise` module to test the normaliser,
    as there are differences in the way the normalise works for manual_upload.
    """
    input_df = conftest.create_mock_manual_upload_df(3)
    input_df["comment_parent_post_id_pi"] = ["post_msg0", "post_msg1", "post_msg2"]
    # In the gather flow the manual uploaded data is first converted to json and then loaded back
    # This emulates that.
    batch_json = json.loads(manual_upload.to_json(input_df))
    gather_id = 1

    gathered_at = datetime.fromisoformat("2024-04-01T12:00:00.000Z")

    processed_df, errors = normalise.normalise_batch(
        normaliser=normalisers.normalise_single_manual_upload_json,
        batch_json=batch_json,
        gather_id=gather_id,
        gather_child_type=schemas.ChildTypeName.manual_upload,
        gather_batch_id=3,
        gathered_at=datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
    )
    assert len(errors) == 0
    assert processed_df is not None
    expected_df = pd.DataFrame(
        {
            "platform": ["facebook", "facebook", "facebook"],
            "data_type": ["posts", "posts", "posts"],
            "pi_platform_message_id": ["msg0", "msg1", "msg2"],
            "pi_platform_message_author_id": ["author0", "author1", "author2"],
            "pi_platform_message_author_name": ["Test Author 0", "Test Author 1", "Test Author 2"],
            "pi_platform_parent_message_id": [None, None, None],
            "pi_platform_root_message_id": ["post_msg0", "post_msg1", "post_msg2"],
            "pi_text": ["Test message 0", "Test message 1", "Test message 2"],
            "pi_platform_message_url": [
                "http://example.com/0",
                "http://example.com/1",
                "http://example.com/2",
            ],
            "platform_message_last_updated_at": [FROZEN_TIME] * 3,
            "phoenix_platform_message_id": [
                normalisers.anonymize("msg0"),
                normalisers.anonymize("msg1"),
                normalisers.anonymize("msg2"),
            ],
            "phoenix_platform_message_author_id": [
                normalisers.anonymize("author0"),
                normalisers.anonymize("author1"),
                normalisers.anonymize("author2"),
            ],
            "phoenix_platform_parent_message_id": [None, None, None],
            "phoenix_platform_root_message_id": [
                normalisers.anonymize("post_msg0"),
                normalisers.anonymize("post_msg1"),
                normalisers.anonymize("post_msg2"),
            ],
            "like_count": [10, 11, 12],
            "share_count": [5, 6, 7],
            "comment_count": [3, 4, 5],
            "tiktok_post_plays": [2, 3, 4],
            "x_post_retweeted_id": [None, None, None],
            "x_is_quote": [None, None, None],
            "x_is_reply": [None, None, None],
        }
    )

    # Alter expected DataFrame to match that now using multiple batches
    expected_df["gather_id"] = gather_id
    expected_df["gather_batch_id"] = 3
    expected_df["gathered_at"] = gathered_at
    expected_df["phoenix_processed_at"] = datetime.fromisoformat(FROZEN_TIME)
    expected_df["gather_type"] = schemas.ChildTypeName.manual_upload
    for column in ["platform_message_last_updated_at", "gathered_at", "phoenix_processed_at"]:
        expected_df[column] = expected_df[column].astype("datetime64[ms, UTC]")  # type: ignore[call-overload]
    expected_df = generalised_messages.coerce_optional_values(expected_df)
    # Need to reorder the columns
    expected_df = expected_df[processed_df.columns]
    pd.testing.assert_frame_equal(processed_df, expected_df)
