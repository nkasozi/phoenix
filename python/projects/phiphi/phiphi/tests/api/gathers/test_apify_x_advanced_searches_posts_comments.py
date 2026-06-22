"""Tests for Apify x gather."""

import datetime

import pytest
from fastapi.testclient import TestClient

from phiphi.api.projects import gathers
from phiphi.api.projects.gathers import apify_x_advanced_searches_posts_comments as apify_x
from phiphi.seed import apify_x_advanced_searches_posts_comments_gather as apify_x_seed

CREATED_TIME = "2024-06-01T12:00:01"


def _mk_instance(**overrides):
    """Helper to build a minimal valid Response instance with overrides."""
    base = dict(
        name="Example",
        id=1,
        created_at=datetime.datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
        updated_at=datetime.datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
        project_id=123,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_x_advanced_searches_posts_comments,
        search_list=["from:nasa -is:retweet lang:en"],
        limit_results_per_search=25,
        posts_created_after=None,
        posts_created_before=None,
    )
    base.update(overrides)
    return (
        apify_x.schemas.ApifyXAdvancedSearchesPostsCommentsGatherResponse(**base)  # type: ignore[arg-type]
    )


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_x_advanced_searches_posts_comments": 50000.00}}
)
@pytest.mark.parametrize(
    "post_data",
    [
        {
            "name": "First apify X gather",
            "limit_results_per_search": 1000,
            "search_list": ["from:nasa -is:retweet lang:en", "from:spacex"],
        },
    ],
)
@pytest.mark.freeze_time(CREATED_TIME)
def test_create_apify_x_advanced_searches_posts_comments_gather(
    reseed_tables, client_admin: TestClient, post_data, patch_settings
) -> None:
    """Test create apify X advanced searches posts comments gather."""
    project_id = 1
    response = client_admin.post(
        f"/projects/{project_id}/gathers/apify_x_advanced_searches_posts_comments", json=post_data
    )
    assert response.status_code == 200
    gather = response.json()

    for key, value in post_data.items():
        assert gather[key] == value

    # These are automatically set
    assert gather["created_at"] == CREATED_TIME
    assert gather["job_run_resource_estimate"] == {
        "max_total_cost": 1000,
        "max_gather_result_count": 2000,
    }


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_x_advanced_searches_posts_comments": 50000.00}}
)
def test_patch_apify_x_advanced_searches_posts_comments(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test patch apify X advanced searches posts comments gather."""
    data = {
        "name": "Updated apify X gather",
        "search_list": ["from:twitter"],
        "limit_results_per_search": 1,
    }
    test_gather = apify_x_seed.TEST_APIFY_X_ADV_SEARCHES_POSTS_COMMENTS_GATHERS[0]
    project_id = test_gather.project_id
    gather_id = test_gather.id
    dict_test_gather = test_gather.dict()
    for key, value in data.items():
        assert dict_test_gather[key] != value
    response = client_admin.patch(
        f"/projects/{project_id}/gathers/apify_x_advanced_searches_posts_comments/{gather_id}",
        json=data,
    )
    assert response.status_code == 200
    gather = response.json()

    assert gather["name"] == data["name"]
    assert gather["search_list"] == data["search_list"]
    assert gather["limit_results_per_search"] == data["limit_results_per_search"]
    assert gather["job_run_resource_estimate"] == {
        "max_total_cost": 0.5,
        "max_gather_result_count": 1,
    }


def test_serialize_required_only():
    """Test serialize with only required fields.

    - search_list → searchTerms (unchanged)
    - maxItems = len(search_list) * limit_results_per_search
    - includeSearchTerms=True, sort='Latest'
    - internal fields are not present
    """
    instance = _mk_instance()
    out = instance.serialize_to_apify_input()

    assert out == {
        "searchTerms": ["from:nasa -is:retweet lang:en"],
        "maxItems": 25,  # 1 * 25
        "includeSearchTerms": True,
        "sort": "Latest",
    }
    # internal fields should not leak to actor
    assert "limit_results_per_search" not in out
    assert "posts_created_after" not in out
    assert "posts_created_before" not in out


def test_serialize_set_sort():
    """Test serialize with sort set."""
    instance = _mk_instance(sort="Top")
    out = instance.serialize_to_apify_input()
    assert out["sort"] == "Top"


def test_serialize_set_sort_invalid():
    """Test serialize with sort set."""
    with pytest.raises(ValueError):
        _ = _mk_instance(sort="invalid")


def test_serialize_with_since_date_only():
    """Date-only 'after' becomes since:YYYY-MM-DD appended to every query."""
    instance = _mk_instance(posts_created_after="2024-01-01")
    out = instance.serialize_to_apify_input()

    assert out["searchTerms"] == ["from:nasa -is:retweet lang:en since:2024-01-01"]
    assert out["maxItems"] == 25
    assert out["includeSearchTerms"] is True
    assert out["sort"] == "Latest"
    assert "limit_results_per_search" not in out


def test_serialize_with_until_date_only():
    """Date-only 'before' becomes until:YYYY-MM-DD appended to every query."""
    instance = _mk_instance(posts_created_before="2024-01-31")
    out = instance.serialize_to_apify_input()

    assert out["searchTerms"] == ["from:nasa -is:retweet lang:en until:2024-01-31"]
    assert out["maxItems"] == 25
    assert out["includeSearchTerms"] is True
    assert out["sort"] == "Latest"


def test_serialize_with_since_and_until_datetimes():
    """Datetime inputs are formatted as *_UTC, per the guide."""
    # Use explicit timezones to verify normalization to UTC with _HH:MM:SS_UTC.
    instance = _mk_instance(
        posts_created_after="2024-01-01T12:34:56+00:00",
        posts_created_before="2024-01-31T23:59:59+00:00",
    )
    out = instance.serialize_to_apify_input()

    assert out["searchTerms"] == [
        "from:nasa -is:retweet lang:en since:2024-01-01_12:34:56_UTC until:2024-01-31_23:59:59_UTC"
    ]
    assert out["maxItems"] == 25
    assert out["includeSearchTerms"] is True
    assert out["sort"] == "Latest"


def test_serialize_multiple_queries_with_window():
    """All queries get the same since/until suffix; maxItems scales with count."""
    queries = ["from:nasa", "from:who min_faves:50 -is:retweet"]
    instance = _mk_instance(
        search_list=queries,
        limit_results_per_search=10,
        posts_created_after="2024-02-01",
        posts_created_before="2024-02-15T05:06:07+00:00",
    )
    out = instance.serialize_to_apify_input()

    expected_suffix = "since:2024-02-01 until:2024-02-15_05:06:07_UTC"
    assert out["searchTerms"] == [f"{q} {expected_suffix}" for q in queries]
    # 2 queries * 10 per query
    assert out["maxItems"] == 10
    assert out["includeSearchTerms"] is True
    assert out["sort"] == "Latest"
