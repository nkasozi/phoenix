"""Tests for the normalise module."""

from datetime import datetime
from unittest import mock

import pandas as pd
import pytest
from prefect.logging import disable_run_logger as disable_prefect_run_logger

from phiphi import config
from phiphi.api.projects.gathers import schemas
from phiphi.pipeline_jobs import constants as pipeline_jobs_constants
from phiphi.pipeline_jobs import dataframe_writers
from phiphi.pipeline_jobs.gathers import (
    apify,
    gather_batch_write_managers,
    normalise,
    normalisers,
    utils,
)


@pytest.mark.freeze_time("2024-04-02T12:10:59.000Z")
def test_normalise_batch(normalised_facebook_posts_df, facebook_posts_gather_fixture):
    """Test normalise_batch function."""
    batch_json = utils.load_sample_raw_data(
        child_type_name=schemas.ChildTypeName.apify_facebook_posts
    )

    processed_df, errors = normalise.normalise_batch(
        normaliser=normalisers.normalise_single_facebook_posts_json,
        batch_json=batch_json,
        gather_id=facebook_posts_gather_fixture.id,
        gather_child_type=facebook_posts_gather_fixture.child_type,
        gather_batch_id=3,
        gathered_at=datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
    )
    assert processed_df is not None
    pd.testing.assert_frame_equal(processed_df, normalised_facebook_posts_df)
    assert len(errors) == 1
    assert errors[0] == batch_json[-1]


@pytest.mark.skip(reason="Currently normalise can't read from a local dataframe.")
@pytest.mark.patch_settings(
    {
        "USE_MOCK_APIFY": True,
        "USE_MOCK_BQ": True,
        "APIFY_API_KEYS": {"main": "dummy_key"},
    }
)
def test_normalise_batches(
    tmpdir,
    patch_settings,
    mocker,
    facebook_posts_gather_fixture,
    normalised_facebook_posts_df,
    freezer,
):
    """Test normalise_batches function."""
    # Set up mock BigQuery root directory
    mocker.patch.object(config.settings, "MOCK_BQ_ROOT_DIR", str(tmpdir))

    freezer.move_to("2024-04-01T12:00:00.000Z")
    # First, run the scrape and batch download results function
    writer_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=1,
            job_run_id=1,
            gather_type=facebook_posts_gather_fixture.gather_type,
        ),
        df_writer=dataframe_writers.DummyWriter(),
        max_mb_batch_size=3,
    )
    _ = apify.scrape.apify_scrape_and_add_to_write_manager(
        gather=facebook_posts_gather_fixture,
        write_manager=writer_manager,
    )

    # TODO: find a way to have normalise read from the dataframe in memory

    freezer.move_to("2024-04-02T12:10:59.000Z")
    # Now, run the normalise_batches function
    with disable_prefect_run_logger():
        normalise.normalise_batches.fn(
            gather_job_run_pairs=[(facebook_posts_gather_fixture.id, 1)],
            bigquery_dataset="test_dataset",
        )

    # Check that the normalized data was written to the correct Parquet file
    parquet_file_path = tmpdir.join(
        "test_dataset", f"{pipeline_jobs_constants.GENERALISED_MESSAGES_TABLE_NAME}.parquet"
    )
    assert parquet_file_path.check()

    # Alter expected DataFrame to match that now using multiple batches
    normalised_facebook_posts_df["gather_batch_id"] = [0, 0, 0, 1, 1, 1, 2, 2]

    # Load the parquet file and verify its contents
    processed_df = pd.read_parquet(parquet_file_path)
    pd.testing.assert_frame_equal(processed_df, normalised_facebook_posts_df)


@pytest.mark.skip(reason="Currently normalise can't read from a local dataframe.")
@mock.patch("phiphi.pipeline_jobs.gathers.utils.load_sample_raw_data")
@pytest.mark.patch_settings(
    {
        "USE_MOCK_APIFY": True,
        "USE_MOCK_BQ": True,
        "APIFY_API_KEYS": {"main": "dummy_key"},
    }
)
def test_normalise_error_batch(
    mock_load_sample_raw_data,
    tmpdir,
    patch_settings,
    mocker,
    tiktok_accounts_posts_gather_fixture,
    normalised_facebook_posts_df,
    freezer,
):
    """Test normalise_batches does not crash when a batch only has error data in it."""
    # Set up mock BigQuery root directory
    mocker.patch.object(config.settings, "MOCK_BQ_ROOT_DIR", str(tmpdir))
    mock_load_sample_raw_data.return_value = [
        {
            "url": "https://www.tiktok.com/channel/@username",
            "input": "https://www.tiktok.com/channel/@username",
            "error": "The provided profile URL is not a valid TikTok profile URL: }",
        },
    ]
    freezer.move_to("2024-04-01T12:00:00.000Z")
    # First, run the scrape and batch download results function
    writer_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=1,
            job_run_id=1,
            gather_type=tiktok_accounts_posts_gather_fixture.gather_type,
        ),
        df_writer=dataframe_writers.DummyWriter(),
        max_mb_batch_size=3,
    )
    _ = apify.scrape.apify_scrape_and_add_to_write_manager(
        gather=tiktok_accounts_posts_gather_fixture,
        write_manager=writer_manager,
    )
    # TODO: find a way to have normalise read from the dataframe in memory

    freezer.move_to("2024-04-02T12:10:59.000Z")
    # Now, run the normalise_batches function
    with disable_prefect_run_logger():
        normalise.normalise_batches.fn(
            gather_job_run_pairs=[(tiktok_accounts_posts_gather_fixture.id, 1)],
            bigquery_dataset="test_dataset",
        )

    # Check that no error was thrown, and no normalized data was written as the raw data was not
    # valid
    parquet_file_path = tmpdir.join(
        "test_dataset", f"{pipeline_jobs_constants.GENERALISED_MESSAGES_TABLE_NAME}.parquet"
    )
    assert not parquet_file_path.check()


def test_flatten_danek_instagram_posts_basic():
    """Test that valid nodes are extracted and returned as (node, None) tuples."""
    json_blob = {
        "items": [
            {"node": {"id": "1", "text": "post1"}},
            {"node": {"id": "2", "text": "post2"}},
        ]
    }

    result = list(normalise.flatten_danek_instagram_posts(json_blob))

    assert result == [
        ({"id": "1", "text": "post1"}, None),
        ({"id": "2", "text": "post2"}, None),
    ]


def test_flatten_danek_instagram_posts_handles_invalid_nodes():
    """Test that malformed items are preserved as (None, error) tuples instead of being dropped."""
    json_blob = {
        "items": [
            {"node": {"id": "1"}},
            {"node": None},
            {"not_node": {"id": "2"}},
            {"node": "not_a_dict"},
        ]
    }

    result = list(normalise.flatten_danek_instagram_posts(json_blob))

    assert result == [
        ({"id": "1"}, None),
        (None, {"node": None}),
        (None, {"not_node": {"id": "2"}}),
        (None, {"node": "not_a_dict"}),
    ]


def test_flatten_danek_instagram_posts_no_items_key():
    """Test that a dict without 'items' is treated as a single valid node."""
    json_blob = {"id": "standalone_post"}

    result = list(normalise.flatten_danek_instagram_posts(json_blob))

    assert result == [(json_blob, None)]


def test_flatten_danek_instagram_posts_empty_input():
    """Test that empty input yields a single error tuple."""
    result = list(normalise.flatten_danek_instagram_posts({}))

    assert result == [(None, {})]


def test_prepare_batch_json_flattens_danek_instagram_posts():
    """Test that nested 'items' structures are flattened into a list of valid nodes only."""
    batch_json = [
        {
            "items": [
                {"node": {"id": "1"}},
                {"node": {"id": "2"}},
            ]
        },
        {
            "items": [
                {"node": {"id": "3"}},
            ]
        },
    ]

    result, _ = normalise.prepare_batch_json_for_normalisation(
        batch_json,
        schemas.ChildTypeName.danek_instagram_posts,
    )

    assert result == [
        {"id": "1"},
        {"id": "2"},
        {"id": "3"},
    ]


def test_prepare_batch_json_filters_invalid_entries():
    """Test that invalid nodes and non-dict blobs are excluded from the flattened output."""
    batch_json = [
        {"items": [{"node": {"id": "1"}}, {"node": None}]},
        "invalid_entry",
        123,
    ]

    result, errors = normalise.prepare_batch_json_for_normalisation(
        batch_json,
        schemas.ChildTypeName.danek_instagram_posts,
    )

    # Only valid nodes should remain
    assert result == [{"id": "1"}]
    assert errors == [
        {"node": None},
        "invalid_entry",
        123,
    ]


def test_prepare_batch_json_passthrough_for_other_types():
    """Test that non-Instagram gather types return the input unchanged."""
    batch_json = [{"id": "1"}, {"id": "2"}]

    result, _ = normalise.prepare_batch_json_for_normalisation(
        batch_json,
        schemas.ChildTypeName.apify_facebook_posts,
    )

    assert result == batch_json


def test_prepare_batch_json_flattens_danek_instagram_child_comments():
    """Test that 'child_comments' are flattened and inherit parent_post_id."""
    batch_json = [
        {
            "parent_post_id": "post1",
            "child_comments": [
                {"pk": "c1", "text": "reply1"},
                {"pk": "c2", "text": "reply2"},
            ],
        },
        {
            "parent_post_id": "post2",
            "child_comments": [
                {"pk": "c3", "text": "reply3"},
            ],
        },
    ]

    result, _ = normalise.prepare_batch_json_for_normalisation(
        batch_json,
        schemas.ChildTypeName.danek_instagram_posts,
    )

    assert result == [
        {"pk": "c1", "text": "reply1", "parent_post_id": "post1"},
        {"pk": "c2", "text": "reply2", "parent_post_id": "post1"},
        {"pk": "c3", "text": "reply3", "parent_post_id": "post2"},
    ]


def test_prepare_batch_json_handles_invalid_child_comments():
    """Test malformed child comments are separated into results and errors."""
    batch_json = [
        {
            "parent_post_id": "post1",
            "child_comments": [
                {"pk": "c1"},
                "invalid",
            ],
        }
    ]

    result, errors = normalise.prepare_batch_json_for_normalisation(
        batch_json,
        schemas.ChildTypeName.danek_instagram_posts,
    )

    # Only valid dicts go into result
    assert result == [
        {"pk": "c1", "parent_post_id": "post1"},
    ]

    # Invalid entries are captured as errors
    assert errors == [
        "invalid",
    ]


def test_prepare_batch_json_mixed_items_and_child_comments():
    """Test flattening mixed comments and child comments with parent_post_id propagation."""
    batch_json = [
        {
            "parent_post_id": "post1",
            "items": [
                {"node": {"id": "1"}},
            ],
        },
        {
            "parent_post_id": "post2",
            "child_comments": [
                {"pk": "c1"},
                {"pk": "c2"},
            ],
        },
    ]

    result, _ = normalise.prepare_batch_json_for_normalisation(
        batch_json,
        schemas.ChildTypeName.danek_instagram_comments,
    )

    assert result == [
        {"id": "1", "parent_post_id": "post1"},
        {"pk": "c1", "parent_post_id": "post2"},
        {"pk": "c2", "parent_post_id": "post2"},
    ]
