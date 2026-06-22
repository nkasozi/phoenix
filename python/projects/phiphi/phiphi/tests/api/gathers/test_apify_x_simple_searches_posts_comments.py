"""Minimal tests for ApifyXSimpleSearchesPostsCommentsGather serialization."""

import datetime

import pytest
from fastapi.testclient import TestClient

from phiphi.api.projects import gathers
from phiphi.api.projects.gathers import apify_x_simple_searches_posts_comments as apify_x
from phiphi.seed import apify_x_simple_searches_posts_comments_gather as apify_x_seed


def _mk_instance(**overrides):
    """Helper to build a minimal valid Response instance with overrides."""
    base = dict(
        name="Example",
        id=1,
        created_at=datetime.datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
        updated_at=datetime.datetime.fromisoformat("2024-04-01T12:00:00.000Z"),
        project_id=123,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_x_simple_searches_posts_comments,
        handle_list=["nasa"],
        keywords_list=["mars"],
        limit_results_per_search=25,
        posts_created_after=None,
        posts_created_before=None,
        sort=None,
        location_near=None,
    )
    base.update(overrides)
    return apify_x.schemas.ApifyXSimpleSearchesPostsCommentsGatherResponse(**base)  # type: ignore[arg-type]


CREATED_TIME = "2024-06-01T12:00:01"


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_x_simple_searches_posts_comments": 50000.00}}
)
@pytest.mark.parametrize(
    "post_data",
    [
        {
            "name": "First apify X simple gather",
            "limit_results_per_search": 100,
            "handle_list": ["nasa", "spacex"],
            "keywords_list": ["mars", "exploration"],
        },
    ],
)
@pytest.mark.freeze_time(CREATED_TIME)
def test_create_apify_x_simple_searches_posts_comments_gather(
    reseed_tables, client_admin: TestClient, post_data, patch_settings
) -> None:
    """Test create apify X simple searches posts comments gather."""
    project_id = 2
    response = client_admin.post(
        f"/projects/{project_id}/gathers/apify_x_simple_searches_posts_comments", json=post_data
    )
    assert response.status_code == 200
    gather = response.json()

    for key, value in post_data.items():
        assert gather[key] == value

    # These are automatically set
    assert gather["created_at"] == CREATED_TIME
    # 2 handles * 2 keyword * 100 per search = 200 results
    assert gather["job_run_resource_estimate"] == {
        "max_total_cost": 200.0,
        "max_gather_result_count": 400,
    }


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_x_simple_searches_posts_comments": 50000.00}}
)
def test_patch_apify_x_simple_searches_posts_comments(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test patch apify X simple searches posts comments gather."""
    data = {
        "name": "Updated apify X simple gather",
        "handle_list": ["esa"],
        "keywords_list": ["launch"],
        "limit_results_per_search": 2,
    }
    test_gather = apify_x_seed.TEST_APIFY_X_SIMPLE_SEARCHES_POSTS_COMMENTS_GATHERS[0]
    project_id = test_gather.project_id
    gather_id = test_gather.id
    dict_test_gather = test_gather.dict()
    for key, value in data.items():
        assert dict_test_gather[key] != value

    response = client_admin.patch(
        f"/projects/{project_id}/gathers/apify_x_simple_searches_posts_comments/{gather_id}",
        json=data,
    )
    assert response.status_code == 200
    gather = response.json()

    assert gather["name"] == data["name"]
    assert gather["handle_list"] == data["handle_list"]
    assert gather["keywords_list"] == data["keywords_list"]
    assert gather["limit_results_per_search"] == data["limit_results_per_search"]
    # 1 handle * 1 keyword * 2 per search = 2 results
    assert gather["job_run_resource_estimate"] == {
        "max_total_cost": 1,
        "max_gather_result_count": 2,
    }


def test_serialize_both_handles_and_keywords():
    """Test serialization with both handles and keywords.

    - creates from:handle + keywords queries.
    """
    instance = _mk_instance(
        handle_list=["nasa", "spacex"], keywords_list=["mars exploration", "exploration"]
    )
    out = instance.serialize_to_apify_input()

    assert out == {
        "searchTerms": [
            "from:nasa mars exploration",
            "from:nasa exploration",
            "from:spacex mars exploration",
            "from:spacex exploration",
        ],
        "maxItems": 25,
        "includeSearchTerms": True,
        "sort": "Latest",
    }
    # Internal fields should not be present
    assert "handle_list" not in out
    assert "keywords_list" not in out
    assert "limit_results_per_search" not in out
    assert instance.job_run_resource_estimate.max_gather_result_count == 100


def test_serialize_handles_only():
    """Test serialization with only handles - creates from:handle queries."""
    instance = _mk_instance(handle_list=["nasa", "spacex"], keywords_list=[])
    out = instance.serialize_to_apify_input()

    assert out == {
        "searchTerms": ["from:nasa", "from:spacex"],
        "maxItems": 25,
        "includeSearchTerms": True,
        "sort": "Latest",
    }
    assert instance.job_run_resource_estimate.max_gather_result_count == 50


def test_serialize_keywords_only():
    """Test serialization with only keywords - uses keywords as search terms."""
    instance = _mk_instance(handle_list=[], keywords_list=["mars exploration", "space mission"])
    out = instance.serialize_to_apify_input()

    assert out == {
        "searchTerms": ["mars exploration", "space mission"],
        "maxItems": 25,
        "includeSearchTerms": True,
        "sort": "Latest",
    }
    assert instance.job_run_resource_estimate.max_gather_result_count == 50


def test_serialize_with_date_filters():
    """Test serialization with date filters."""
    instance = _mk_instance(
        handle_list=["nasa"],
        keywords_list=["mars", "exploration"],
        posts_created_after="2024-01-01",
        posts_created_before="2024-01-31",
    )
    out = instance.serialize_to_apify_input()

    assert out["searchTerms"] == [
        "from:nasa mars since:2024-01-01 until:2024-01-31",
        "from:nasa exploration since:2024-01-01 until:2024-01-31",
    ]
    assert out["maxItems"] == 25
    assert instance.job_run_resource_estimate.max_gather_result_count == 50


def test_serialize_with_location_filter():
    """Test serialization with location filter."""
    instance = _mk_instance(
        handle_list=["nasa", "spacex"], keywords_list=["mars"], location_near="Houston"
    )
    out = instance.serialize_to_apify_input()

    assert out["searchTerms"] == [
        "from:nasa mars near:Houston",
        "from:spacex mars near:Houston",
    ]
    assert out["maxItems"] == 25
    assert instance.job_run_resource_estimate.max_gather_result_count == 50


def test_serialize_with_all_filters():
    """Test serialization with date and location filters combined."""
    instance = _mk_instance(
        handle_list=["nasa", "spacex"],
        keywords_list=["mars", "exploration"],
        posts_created_after="2024-01-01T12:34:56+00:00",
        posts_created_before="2024-01-31",
        location_near="Houston",
    )
    out = instance.serialize_to_apify_input()

    assert out["searchTerms"] == [
        "from:nasa mars since:2024-01-01_12:34:56_UTC until:2024-01-31 near:Houston",
        "from:nasa exploration since:2024-01-01_12:34:56_UTC until:2024-01-31 near:Houston",
        "from:spacex mars since:2024-01-01_12:34:56_UTC until:2024-01-31 near:Houston",
        "from:spacex exploration since:2024-01-01_12:34:56_UTC until:2024-01-31 near:Houston",
    ]
    assert out["maxItems"] == 25
    assert instance.job_run_resource_estimate.max_gather_result_count == 100


def test_serialize_custom_sort():
    """Test serialization with custom sort order."""
    instance = _mk_instance(handle_list=["nasa"], keywords_list=["mars"], sort="Top")
    out = instance.serialize_to_apify_input()

    assert out["sort"] == "Top"
    assert instance.job_run_resource_estimate.max_gather_result_count == 25


def test_serialize_empty_lists():
    """Test serialization with empty handle and keyword lists."""
    instance = _mk_instance(handle_list=[], keywords_list=[])
    out = instance.serialize_to_apify_input()

    assert out == {
        "searchTerms": [""],
        "maxItems": 25,
        "includeSearchTerms": True,
        "sort": "Latest",
    }
    assert instance.job_run_resource_estimate.max_gather_result_count == 25


def test_serialize_multiple_handles_single_keyword():
    """Test serialization with multiple handles and single keyword."""
    instance = _mk_instance(
        handle_list=["nasa", "spacex", "esa"],
        keywords_list=["launch"],
        limit_results_per_search=10,
    )
    out = instance.serialize_to_apify_input()

    assert out == {
        "searchTerms": ["from:nasa launch", "from:spacex launch", "from:esa launch"],
        "maxItems": 10,
        "includeSearchTerms": True,
        "sort": "Latest",
    }
    assert instance.job_run_resource_estimate.max_gather_result_count == 30
