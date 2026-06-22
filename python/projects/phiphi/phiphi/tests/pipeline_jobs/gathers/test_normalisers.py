"""Tests for normalisers."""

from datetime import datetime

import pandas as pd
import pytest

from phiphi.api.projects.gathers import schemas
from phiphi.pipeline_jobs.gathers import normalise, normalisers, utils


@pytest.mark.freeze_time("2024-04-02T12:10:59.000Z")
def test_normaliser_facebook_posts(normalised_facebook_posts_df, facebook_posts_gather_fixture):
    """Test normaliser for facebook posts function.

    Note: we use the `normalise_batch` function from the `normalise` module to test the normaliser,
    as this is an easy way to test multiple records (and tests in the usage context).
    """
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


@pytest.mark.freeze_time("2024-04-02T12:10:59.000Z")
def test_normaliser_facebook_search_posts(
    normalised_facebook_search_posts_df, facebook_search_posts_gather_fixture
):
    """Test normaliser for facebook posts function.

    Note: we use the `normalise_batch` function from the `normalise` module to test the normaliser,
    as this is an easy way to test multiple records (and tests in the usage context).
    """
    batch_json = utils.load_sample_raw_data(
        child_type_name=schemas.ChildTypeName.apify_facebook_search_posts
    )

    processed_df, errors = normalise.normalise_batch(
        normaliser=normalisers.normalise_single_facebook_search_posts_json,
        batch_json=batch_json,
        gather_id=facebook_search_posts_gather_fixture.id,
        gather_child_type=facebook_search_posts_gather_fixture.child_type,
        gather_batch_id=3,
        gathered_at=datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
    )
    assert processed_df is not None
    pd.testing.assert_frame_equal(processed_df, normalised_facebook_search_posts_df)
    assert len(errors) == 1
    assert errors[0] == batch_json[-1]


@pytest.mark.freeze_time("2024-04-02T12:10:59.000Z")
def test_normaliser_facebook_comments(
    normalised_facebook_comments_df, facebook_comments_gather_fixture
):
    """Test normaliser for facebook posts function.

    Note: we use the `normalise_batch` function from the `normalise` module to test the normaliser,
    as this is an easy way to test multiple records (and tests in the usage context).
    """
    batch_json = utils.load_sample_raw_data(
        child_type_name=schemas.ChildTypeName.apify_facebook_comments,
    )

    processed_df, errors = normalise.normalise_batch(
        normaliser=normalisers.normalise_single_facebook_comments_json,
        batch_json=batch_json,
        gather_id=facebook_comments_gather_fixture.id,
        gather_child_type=facebook_comments_gather_fixture.child_type,
        gather_batch_id=3,
        gathered_at=datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
    )
    assert processed_df is not None
    pd.testing.assert_frame_equal(processed_df, normalised_facebook_comments_df)
    assert len(errors) == 2
    assert errors[0] == batch_json[-2]
    assert errors[1] == batch_json[-1]


@pytest.mark.freeze_time("2024-04-02T12:10:59.000Z")
def test_normaliser_tiktok_accounts_posts(
    normalised_tiktok_accounts_posts_df, tiktok_accounts_posts_gather_fixture
):
    """Test normaliser for tiktok accounts posts function.

    Note: we use the `normalise_batch` function from the `normalise` module to test the normaliser,
    as this is an easy way to test multiple records (and tests in the usage context).
    """
    batch_json = utils.load_sample_raw_data(
        child_type_name=schemas.ChildTypeName.apify_tiktok_accounts_posts,
    )

    processed_df, errors = normalise.normalise_batch(
        # all tiktok posts gathers are normalised the same way
        normaliser=normalisers.normalise_single_tiktok_posts_json,
        batch_json=batch_json,
        gather_id=tiktok_accounts_posts_gather_fixture.id,
        gather_child_type=tiktok_accounts_posts_gather_fixture.child_type,
        gather_batch_id=3,
        gathered_at=datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
    )
    assert processed_df is not None
    pd.testing.assert_frame_equal(processed_df, normalised_tiktok_accounts_posts_df)
    assert len(errors) == 2
    assert errors[0] == batch_json[-2]
    assert errors[1] == batch_json[-1]


@pytest.mark.freeze_time("2024-04-02T12:10:59.000Z")
def test_normaliser_tiktok_hashtags_posts(
    normalised_tiktok_hashtags_posts_df, tiktok_hashtags_posts_gather_fixture
):
    """Test normaliser for tiktok hashtags posts function.

    Note: we use the `normalise_batch` function from the `normalise` module to test the normaliser,
    as this is an easy way to test multiple records (and tests in the usage context).
    """
    batch_json = utils.load_sample_raw_data(
        child_type_name=schemas.ChildTypeName.apify_tiktok_hashtags_posts,
    )

    processed_df, errors = normalise.normalise_batch(
        # all tiktok posts gathers are normalised the same way
        normaliser=normalisers.normalise_single_tiktok_posts_json,
        batch_json=batch_json,
        gather_id=tiktok_hashtags_posts_gather_fixture.id,
        gather_child_type=tiktok_hashtags_posts_gather_fixture.child_type,
        gather_batch_id=3,
        gathered_at=datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
    )
    assert processed_df is not None
    pd.testing.assert_frame_equal(processed_df, normalised_tiktok_hashtags_posts_df)
    assert len(errors) == 0


@pytest.mark.freeze_time("2024-04-02T12:10:59.000Z")
def test_normaliser_tiktok_searches_posts(
    normalised_tiktok_searches_posts_df, tiktok_searches_posts_gather_fixture
):
    """Test normaliser for tiktok searches posts function.

    Note: we use the `normalise_batch` function from the `normalise` module to test the normaliser,
    as this is an easy way to test multiple records (and tests in the usage context).
    """
    batch_json = utils.load_sample_raw_data(
        child_type_name=schemas.ChildTypeName.apify_tiktok_searches_posts,
    )

    processed_df, errors = normalise.normalise_batch(
        # all tiktok posts gathers are normalised the same way
        normaliser=normalisers.normalise_single_tiktok_posts_json,
        batch_json=batch_json,
        gather_id=tiktok_searches_posts_gather_fixture.id,
        gather_child_type=tiktok_searches_posts_gather_fixture.child_type,
        gather_batch_id=3,
        gathered_at=datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
    )
    assert processed_df is not None
    pd.testing.assert_frame_equal(processed_df, normalised_tiktok_searches_posts_df)
    assert len(errors) == 0


@pytest.mark.freeze_time("2024-04-02T12:10:59.000Z")
def test_normaliser_tiktok_comments(normalised_tiktok_comments_df, tiktok_comments_gather_fixture):
    """Test normaliser for tiktok comments function.

    Note: we use the `normalise_batch` function from the `normalise` module to test the normaliser,
    as this is an easy way to test multiple records (and tests in the usage context).
    """
    batch_json = utils.load_sample_raw_data(
        child_type_name=schemas.ChildTypeName.apify_tiktok_comments,
    )

    processed_df, errors = normalise.normalise_batch(
        normaliser=normalisers.normalise_single_tiktok_comments_json,
        batch_json=batch_json,
        gather_id=tiktok_comments_gather_fixture.id,
        gather_child_type=tiktok_comments_gather_fixture.child_type,
        gather_batch_id=3,
        gathered_at=datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
    )
    assert processed_df is not None
    pd.testing.assert_frame_equal(processed_df, normalised_tiktok_comments_df)
    assert len(errors) == 1
    assert errors[0] == batch_json[-1]


@pytest.mark.freeze_time("2024-04-02T12:10:59.000Z")
def test_normaliser_x_simple_searches_posts_comments(
    normalised_x_simple_searches_posts_comments_df,
    x_simple_searches_posts_comments_gather_fixture,
):
    """Test normaliser for X simple searches posts and comments function.

    Note: we use the `normalise_batch` function from the `normalise` module to test the normaliser,
    as this is an easy way to test multiple records (and tests in the usage context).

    This test verifies:
    1. Regular posts are handled correctly
    2. Reply tweets become comments with proper parent/root relationships
    3. Quote tweets become comments AND extract quoted tweets as separate posts
    4. Stats are mapped correctly (like_count, share_count, comment_count)
    """
    batch_json = utils.load_sample_raw_data(
        child_type_name=schemas.ChildTypeName.apify_x_simple_searches_posts_comments
    )

    processed_df, errors = normalise.normalise_batch(
        normaliser=normalisers.normalise_single_x_advanced_searches_posts_comments_json,
        batch_json=batch_json,
        gather_id=x_simple_searches_posts_comments_gather_fixture.id,
        gather_child_type=x_simple_searches_posts_comments_gather_fixture.child_type,
        gather_batch_id=3,
        gathered_at=datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
    )

    assert processed_df is not None
    pd.testing.assert_frame_equal(processed_df, normalised_x_simple_searches_posts_comments_df)
    # 2 errors: tweet with null author and tweet with author missing id
    assert len(errors) == 2


@pytest.mark.freeze_time("2024-04-02T12:10:59.000Z")
def test_normaliser_x_advanced_searches_posts_comments(
    normalised_x_advanced_searches_posts_comments_df,
    x_advanced_searches_posts_comments_gather_fixture,
):
    """Test normaliser for X advanced searches posts and comments function.

    Note: we use the `normalise_batch` function from the `normalise` module to test the normaliser,
    as this is an easy way to test multiple records (and tests in the usage context).

    This test verifies:
    1. Regular posts are handled correctly
    2. Reply tweets become comments with proper parent/root relationships
    3. Quote tweets become comments AND extract quoted tweets as separate posts
    4. Stats are mapped correctly (like_count, share_count, comment_count)
    """
    batch_json = utils.load_sample_raw_data(
        child_type_name=schemas.ChildTypeName.apify_x_advanced_searches_posts_comments
    )

    processed_df, errors = normalise.normalise_batch(
        normaliser=normalisers.normalise_single_x_advanced_searches_posts_comments_json,
        batch_json=batch_json,
        gather_id=x_advanced_searches_posts_comments_gather_fixture.id,
        gather_child_type=x_advanced_searches_posts_comments_gather_fixture.child_type,
        gather_batch_id=3,
        gathered_at=datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
    )

    assert processed_df is not None
    pd.testing.assert_frame_equal(processed_df, normalised_x_advanced_searches_posts_comments_df)
    # 2 errors: tweet with null author and tweet with author missing id
    assert len(errors) == 2


def test_normaliser_x_individual_record_types():
    """Test individual record type handling for X normalizer."""
    # Test regular post (not reply, not quote)
    regular_post = {
        "id": "tweet_id_1",
        "author": {"id": "author_id_1", "userName": "user_name_1"},
        "fullText": "Regular tweet text",
        "url": "https://x.com/user_name_1/status/tweet_id_1",
        "createdAt": "Fri Jan 31 16:47:08 +0000 2025",
        "likeCount": 100,
        "retweetCount": 50,
        "replyCount": 25,
        "quoteCount": 10,
        "isReply": False,
        "isQuote": False,
    }

    result = normalisers.normalise_single_x_advanced_searches_posts_comments_json(regular_post)
    assert result is not None
    assert result["data_type"] == "posts"
    assert result["pi_platform_parent_message_id"] is None
    assert result["pi_platform_root_message_id"] is None
    assert result["like_count"] == 100
    assert result["share_count"] == 50
    assert result["comment_count"] == 35  # quote + reply counts

    # Test reply tweet
    reply_tweet = {
        "id": "tweet_id_2",
        "author": {"id": "author_id_1", "userName": "user_name_1"},
        "fullText": "Reply tweet text",
        "url": "https://x.com/user_name_1/status/tweet_id_2",
        "createdAt": "Thu Jan 30 23:05:43 +0000 2025",
        "likeCount": 23,
        "retweetCount": 4,
        "replyCount": 1,
        "quoteCount": 0,
        "isReply": True,
        "inReplyToId": "in_reply_to_id_1",
        "conversationId": "tweet_id_3",
        "isQuote": False,
    }

    result = normalisers.normalise_single_x_advanced_searches_posts_comments_json(reply_tweet)
    assert result is not None
    assert result["data_type"] == "comments"
    assert result["pi_platform_parent_message_id"] == "in_reply_to_id_1"
    assert result["pi_platform_root_message_id"] == "tweet_id_3"

    # Test quote tweet
    quote_tweet = {
        "id": "tweet_id_2",
        "author": {"id": "author_id_1", "userName": "user_name_1"},
        "fullText": "Quote tweet text",
        "url": "https://x.com/user_name_1/status/tweet_id_2",
        "createdAt": "Thu Jan 30 23:05:43 +0000 2025",
        "likeCount": 23,
        "retweetCount": 4,
        "replyCount": 1,
        "quoteCount": 0,
        "isReply": False,
        "isQuote": True,
        "conversationId": "tweet_id_3",
        "quote": {
            "id": "quote_id_1",
            "author": {"id": "author_id_1", "userName": "user_name_1"},
            "text": "Original quoted text",
            "createdAt": "Wed Jan 29 16:21:13 +0000 2025",
            "likeCount": 7794,
            "retweetCount": 1383,
            "replyCount": 428,
            "quoteCount": 146,
        },
    }

    result = normalisers.normalise_single_x_advanced_searches_posts_comments_json(quote_tweet)
    assert result is not None
    assert result["data_type"] == "comments"  # Quote tweet becomes a comment
    assert result["pi_platform_parent_message_id"] == "quote_id_1"  # Parent is the quoted tweet

    # Test extracting quoted tweet as separate post
    quoted_post = normalisers.extract_quoted_tweet_as_post(quote_tweet)
    assert quoted_post is not None
    assert quoted_post["data_type"] == "posts"
    assert quoted_post["pi_platform_message_id"] == "quote_id_1"
    assert quoted_post["pi_text"] == "Original quoted text"
    assert quoted_post["like_count"] == 7794


@pytest.mark.freeze_time("2024-04-02T12:10:59.000Z")
def test_normaliser_danek_facebook_searches_posts(
    normalised_danek_facebook_searches_posts_df, danek_facebook_searches_posts_gather_fixture
):
    """Test normaliser for danek facebook posts function.

    Note: we use the `normalise_batch` function from the `normalise` module to test the normaliser,
    as this is an easy way to test multiple records (and tests in the usage context).
    """
    batch_json = utils.load_sample_raw_data(
        child_type_name=schemas.ChildTypeName.danek_facebook_searches_posts
    )

    processed_df, errors = normalise.normalise_batch(
        normaliser=normalisers.normalise_single_danek_facebook_searches_posts_json,
        batch_json=batch_json,
        gather_id=danek_facebook_searches_posts_gather_fixture.id,
        gather_child_type=danek_facebook_searches_posts_gather_fixture.child_type,
        gather_batch_id=3,
        gathered_at=datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
    )
    assert processed_df is not None
    pd.testing.assert_frame_equal(processed_df, normalised_danek_facebook_searches_posts_df)
    assert len(errors) == 1
    assert errors[0] == batch_json[-1]


@pytest.mark.freeze_time("2024-04-02T12:10:59.000Z")
def test_normaliser_danek_instagram_posts(
    normalised_danek_instagram_posts_df, danek_instagram_posts_gather_fixture
):
    """Test normaliser for danek instagram posts function.

    Note: we use the `normalise_batch` function from the `normalise` module to test the normaliser,
    as this is an easy way to test multiple records (and tests in the usage context).
    """
    batch_json = utils.load_sample_raw_data(
        child_type_name=schemas.ChildTypeName.danek_instagram_posts
    )
    batch_json_flattened, flatten_errors = normalise.prepare_batch_json_for_normalisation(
        batch_json, schemas.ChildTypeName.danek_instagram_posts
    )
    processed_df, errors = normalise.normalise_batch(
        normaliser=normalisers.normalise_single_danek_instagram_posts_json,
        batch_json=batch_json_flattened,
        gather_id=danek_instagram_posts_gather_fixture.id,
        gather_child_type=danek_instagram_posts_gather_fixture.child_type,
        gather_batch_id=3,
        gathered_at=datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
    )
    assert processed_df is not None
    assert len(flatten_errors) == 0
    pd.testing.assert_frame_equal(processed_df, normalised_danek_instagram_posts_df)


@pytest.mark.freeze_time("2024-04-02T12:10:59.000Z")
def test_normaliser_danek_instagram_comments(
    normalised_danek_instagram_comments_df, danek_instagram_comments_gather_fixture
):
    """Test normaliser for Danek Instagram comments.

    Uses `normalise_batch` to process multiple comment records and verify
    that the output matches the expected normalized DataFrame.
    """
    batch_json = utils.load_sample_raw_data(
        child_type_name=schemas.ChildTypeName.danek_instagram_comments
    )

    batch_json_flattened, flatten_errors = normalise.prepare_batch_json_for_normalisation(
        batch_json, schemas.ChildTypeName.danek_instagram_comments
    )
    processed_df, errors = normalise.normalise_batch(
        normaliser=normalisers.normalise_single_instagram_comments_json,
        batch_json=batch_json_flattened,
        gather_id=danek_instagram_comments_gather_fixture.id,
        gather_child_type=danek_instagram_comments_gather_fixture.child_type,
        gather_batch_id=3,
        gathered_at=datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
    )

    assert processed_df is not None
    assert len(flatten_errors) == 0
    assert len(errors) == 0
    pd.testing.assert_frame_equal(processed_df, normalised_danek_instagram_comments_df)
