"""Tests for the Danek Instagram posts scraper."""

import datetime
from unittest import mock

from phiphi.api.projects import gathers
from phiphi.api.projects.gathers import schemas
from phiphi.pipeline_jobs import dataframe_writers
from phiphi.pipeline_jobs.gathers import gather_batch_write_managers, utils
from phiphi.pipeline_jobs.gathers.danek import instagram_posts_scraper

# Unix timestamps used across tests
# 2025-06-01T00:00:00Z
NEWER_THAN_CUTOFF_TAKEN_AT = 1748736000
# 2024-01-01T00:00:00Z
OLDER_THAN_CUTOFF_TAKEN_AT = 1704067200
# 2025-01-01T00:00:00Z  (the cutoff itself)
CUTOFF_ISO = "2025-01-01T00:00:00+00:00"
# Exactly at the cutoff boundary
AT_CUTOFF_TAKEN_AT = 1735689600


def make_page_response(taken_at_values: list, after_cursor: str | None = None) -> dict:
    """Build a mock Instagram posts page response with the given taken_at values."""
    return {
        "items": [
            {"node": {"taken_at": ts, "pk": str(i), "id": str(i), "user": {"id": "u1"}}}
            for i, ts in enumerate(taken_at_values)
        ],
        "after_cursor": after_cursor,
    }


# --- make_posts_created_after_stop_condition unit tests ---
# Basic tests use page_number=2 to bypass the first-page pinned-post skip; page=1 behaviour
# is covered separately by the pinned-post tests below.


def test_stop_condition_returns_false_when_items_empty():
    """Stop condition should not trigger on an empty items list."""
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(CUTOFF_ISO)
    assert condition({"items": []}, 2) is False


def test_stop_condition_returns_false_when_no_items_key():
    """Stop condition should not trigger when items key is absent."""
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(CUTOFF_ISO)
    assert condition({}, 2) is False


def test_stop_condition_returns_false_when_all_posts_newer():
    """Stop condition should not trigger when all posts are newer than the cutoff."""
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(CUTOFF_ISO)
    result = make_page_response([NEWER_THAN_CUTOFF_TAKEN_AT, NEWER_THAN_CUTOFF_TAKEN_AT])
    assert condition(result, 2) is False


def test_stop_condition_returns_true_when_oldest_post_older():
    """Stop condition should trigger when the oldest post is before the cutoff."""
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(CUTOFF_ISO)
    result = make_page_response([NEWER_THAN_CUTOFF_TAKEN_AT, OLDER_THAN_CUTOFF_TAKEN_AT])
    assert condition(result, 2) is True


def test_stop_condition_does_not_trigger_at_exact_cutoff():
    """A post exactly at the cutoff timestamp should not trigger the stop condition."""
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(CUTOFF_ISO)
    result = make_page_response([AT_CUTOFF_TAKEN_AT])
    assert condition(result, 2) is False


def test_stop_condition_handles_missing_node():
    """Items without a node key should be skipped; no stop if remaining items are newer."""
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(CUTOFF_ISO)
    result = {
        "items": [
            {"node": {"taken_at": NEWER_THAN_CUTOFF_TAKEN_AT, "pk": "1", "id": "1"}},
            {"no_node_here": True},
        ]
    }
    assert condition(result, 2) is False


def test_stop_condition_handles_all_items_missing_node():
    """If no items have a valid node, stop condition should not trigger."""
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(CUTOFF_ISO)
    result = {"items": [{"no_node": True}, {"also_no_node": True}]}
    assert condition(result, 2) is False


def test_stop_condition_handles_missing_taken_at_in_node():
    """Nodes without taken_at should be skipped; no stop if remaining items are newer."""
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(CUTOFF_ISO)
    result = {
        "items": [
            {"node": {"taken_at": NEWER_THAN_CUTOFF_TAKEN_AT, "pk": "1"}},
            {"node": {"pk": "2"}},  # no taken_at
        ]
    }
    assert condition(result, 2) is False


def test_stop_condition_ignores_first_3_items_on_first_page():
    """Pinned posts at the top of the first page should not trigger the stop condition."""
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(CUTOFF_ISO)
    # First 3 items are old (pinned posts), remaining items are newer
    result = make_page_response(
        [OLDER_THAN_CUTOFF_TAKEN_AT] * 3 + [NEWER_THAN_CUTOFF_TAKEN_AT] * 3
    )
    assert condition(result, 1) is False


def test_stop_condition_triggers_on_first_page_after_skipping_pinned():
    """Stop condition should still trigger if non-pinned items on the first page are old."""
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(CUTOFF_ISO)
    # First 3 old (pinned), 4th item also old (not pinned)
    result = make_page_response([OLDER_THAN_CUTOFF_TAKEN_AT] * 4)
    assert condition(result, 1) is True


def test_stop_condition_first_page_fewer_than_pinned_count():
    """If the first page has fewer items than the skip count, no items remain to check."""
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(CUTOFF_ISO)
    result = make_page_response([OLDER_THAN_CUTOFF_TAKEN_AT] * 2)
    assert condition(result, 1) is False


def test_stop_condition_checks_all_items_on_subsequent_pages():
    """On page 2+, the pinned-post skip does not apply — all items are checked."""
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(CUTOFF_ISO)
    newer_page = make_page_response([NEWER_THAN_CUTOFF_TAKEN_AT] * 6)
    older_page = make_page_response([OLDER_THAN_CUTOFF_TAKEN_AT] * 3)
    assert condition(newer_page, 1) is False
    # Page 2: first 3 items are old — would be skipped on page 1 but not here
    assert condition(older_page, 2) is True


def test_stop_condition_accepts_timezone_naive_cutoff():
    """A timezone-naive cutoff string should be treated as UTC."""
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(
        "2025-01-01T00:00:00"
    )
    result = make_page_response([OLDER_THAN_CUTOFF_TAKEN_AT])
    assert condition(result, 2) is True


def test_stop_condition_against_sample_data():
    """Stop condition works correctly against the real sanitized sample data structure."""
    pages = utils.load_sample_raw_data(schemas.ChildTypeName.danek_instagram_posts)
    page = pages[0]  # taken_at range: 2025-12-09 → 2026-02-27

    # Cutoff before all posts: none are old enough to stop
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(
        "2025-01-01T00:00:00+00:00"
    )
    assert condition(page, 2) is False

    # Cutoff after all posts: oldest post predates cutoff → stop
    condition = instagram_posts_scraper.make_posts_created_after_stop_condition(
        "2026-12-01T00:00:00+00:00"
    )
    assert condition(page, 2) is True


# --- scrape_instagram_posts_and_add_to_write_manager integration tests ---


def _make_write_manager(
    gather: gathers.danek_instagram_posts.schemas.DanekInstagramPostsGatherResponse,
) -> gather_batch_write_managers.GatherBatchWriteManager:
    return gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=gather.id,
            job_run_id=1,
            gather_type=gather.child_type,
        ),
        df_writer=dataframe_writers.DummyWriter(),
    )


def _make_single_username_gather(
    posts_created_after: str | None = CUTOFF_ISO,
) -> gathers.danek_instagram_posts.schemas.DanekInstagramPostsGatherResponse:
    """Build a minimal single-username gather for scraper integration tests."""
    return gathers.danek_instagram_posts.schemas.DanekInstagramPostsGatherResponse(
        name="Example",
        id=1,
        project_id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.danek_instagram_posts,
        account_username_list=["testuser"],
        limit_posts_per_account=20,
        posts_created_after=posts_created_after,
        scrape_comments_count_per_post=0,
        limit_child_comments_per_comment=0,
    )


@mock.patch("phiphi.utils.get_danek_api_token")
def test_scrape_stops_when_page_contains_old_posts(mock_token, requests_mock):
    """Pagination stops when a page's oldest post predates posts_created_after.

    Page 1 (all newer): returns a cursor → would normally continue.
    Page 2 (contains old post): has a cursor, but stop condition fires → page 3 never requested.
    """
    mock_token.return_value = "token"
    gather = _make_single_username_gather()

    page_1 = make_page_response([NEWER_THAN_CUTOFF_TAKEN_AT], after_cursor="cursor_abc")
    # page_2 has a cursor — without the stop condition pagination would continue to page_3
    page_2 = make_page_response(
        [NEWER_THAN_CUTOFF_TAKEN_AT, OLDER_THAN_CUTOFF_TAKEN_AT], after_cursor="cursor_def"
    )
    page_3 = make_page_response([NEWER_THAN_CUTOFF_TAKEN_AT])

    requests_mock.post(
        instagram_posts_scraper.DEFAULT_URL,
        [{"json": page_1}, {"json": page_2}, {"json": page_3}],
    )

    write_manager = _make_write_manager(gather)
    instagram_posts_scraper.scrape_instagram_posts_and_add_to_write_manager(
        gather=gather, write_manager=write_manager
    )

    # Stop condition fires after page_2 — page_3 must not be requested
    assert len(requests_mock.request_history) == 2
    assert write_manager.complete_write().total_items_processed == 2


@mock.patch("phiphi.utils.get_danek_api_token")
def test_scrape_continues_when_all_posts_newer(mock_token, requests_mock):
    """Pagination continues normally when all posts are newer than posts_created_after."""
    mock_token.return_value = "token"
    gather = _make_single_username_gather()

    page_1 = make_page_response([NEWER_THAN_CUTOFF_TAKEN_AT], after_cursor="cursor_abc")
    page_2 = make_page_response([NEWER_THAN_CUTOFF_TAKEN_AT])  # no cursor → natural end

    requests_mock.post(instagram_posts_scraper.DEFAULT_URL, [{"json": page_1}, {"json": page_2}])

    write_manager = _make_write_manager(gather)
    instagram_posts_scraper.scrape_instagram_posts_and_add_to_write_manager(
        gather=gather, write_manager=write_manager
    )

    assert len(requests_mock.request_history) == 2
    assert write_manager.complete_write().total_items_processed == 2


@mock.patch("phiphi.utils.get_danek_api_token")
def test_scrape_without_posts_created_after(mock_token, requests_mock):
    """When posts_created_after is None, all pages are fetched with no date stopping."""
    mock_token.return_value = "token"
    gather = _make_single_username_gather(posts_created_after=None)

    page = make_page_response([OLDER_THAN_CUTOFF_TAKEN_AT])
    requests_mock.post(instagram_posts_scraper.DEFAULT_URL, json=page)

    write_manager = _make_write_manager(gather)
    instagram_posts_scraper.scrape_instagram_posts_and_add_to_write_manager(
        gather=gather, write_manager=write_manager
    )

    # Old posts should not stop pagination — scraper runs to natural end (no cursor)
    assert len(requests_mock.request_history) == 1
    assert write_manager.complete_write().total_items_processed == 1
