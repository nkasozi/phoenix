"""Test Apify TikTok Hashtags Posts Gathers."""

import datetime

import pytest
from fastapi.testclient import TestClient

from phiphi.api.projects import gathers
from phiphi.seed import apify_tiktok_hashtags_posts_gather

CREATED_TIME = "2024-04-01T12:00:01"


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_tiktok_hashtags_posts": 50000.00}}
)
@pytest.mark.parametrize(
    "post_data",
    [
        {
            "name": "First apify gather",
            "limit_posts_per_hashtag": 1000,
            "hashtag_list": ["example", "test"],
        },
    ],
)
@pytest.mark.freeze_time(CREATED_TIME)
def test_create_apify_tiktok_hashtags_posts_gather(
    reseed_tables, client_admin: TestClient, post_data, patch_settings
) -> None:
    """Test create apify TikTok hashtags posts gather."""
    project_id = 1
    response = client_admin.post(
        f"/projects/{project_id}/gathers/apify_tiktok_hashtags_posts", json=post_data
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
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_tiktok_hashtags_posts": 50000.00}}
)
def test_patch_apify_tiktok_hashtags_posts(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test patch apify TikTok hashtags posts gather."""
    data = {
        "name": "Updated apify gather",
        "hashtag_list": ["example"],
        "limit_posts_per_hashtag": 1,
    }
    test_gather = apify_tiktok_hashtags_posts_gather.TEST_APIFY_TIKTOK_HASHTAGS_POSTS_GATHERS[0]
    project_id = test_gather.project_id
    gather_id = test_gather.id
    dict_test_gather = test_gather.dict()
    for key, value in data.items():
        assert dict_test_gather[key] != value
    response = client_admin.patch(
        f"/projects/{project_id}/gathers/apify_tiktok_hashtags_posts/{gather_id}", json=data
    )
    assert response.status_code == 200
    gather = response.json()

    assert gather["name"] == data["name"]
    assert gather["hashtag_list"] == data["hashtag_list"]
    assert gather["limit_posts_per_hashtag"] == data["limit_posts_per_hashtag"]
    assert gather["job_run_resource_estimate"] == {
        "max_total_cost": 0.5,
        "max_gather_result_count": 1,
    }


def test_serialize_tiktok_hashtags_posts_gather_response_with_all_fields_1():
    """Test that ApifyTikTokHashtagsPostsGatherResponse serializes correctly."""
    instance = gathers.apify_tiktok_hashtags_posts.schemas.ApifyTikTokHashtagsPostsGatherResponse(
        name="Example",
        limit_posts_per_hashtag=10,
        hashtag_list=["example", "test"],
        proxy_country_to_gather_from="US",
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=123,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_tiktok_hashtags_posts,
    )

    output_dict = instance.serialize_to_apify_input()

    expected_output_dict = {
        "resultsPerPage": 10,
        "hashtags": ["example", "test"],
        "proxyCountryCode": "US",
        "searchSection": gathers.constants.TIKTOK_POST_SEARCH_SECTION,
    }

    assert expected_output_dict == output_dict


def test_serialize_tiktok_hashtags_posts_gather_response_with_required_fields_only():
    """Test that serialize to Apify correctly omits fields when they are not provided."""
    instance = gathers.apify_tiktok_hashtags_posts.schemas.ApifyTikTokHashtagsPostsGatherResponse(
        name="Example",
        limit_posts_per_hashtag=10,
        hashtag_list=["example", "test"],
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=123,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_tiktok_hashtags_posts,
    )

    output_dict = instance.serialize_to_apify_input()

    expected_keys = ["resultsPerPage", "hashtags", "searchSection"]
    assert all(key in output_dict for key in expected_keys)
    assert "oldestPostDate" not in output_dict
    assert "scrapeLastNDays" not in output_dict
    assert "proxyCountryCode" not in output_dict

    expected_output_dict = {
        "resultsPerPage": 10,
        "hashtags": ["example", "test"],
        "searchSection": gathers.constants.TIKTOK_POST_SEARCH_SECTION,
    }

    assert expected_output_dict == output_dict
