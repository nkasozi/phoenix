"""Test Danek Facebook Searches Posts Gathers."""

import pytest
from fastapi.testclient import TestClient

from phiphi.seed import danek_facebook_searches_posts_gather

CREATED_TIME = "2024-04-01T12:00:01"
UPDATE_TIME = "2024-04-01T12:00:02"


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"DANEK_COST_PER_100K_RESULTS_DICT": {"danek_facebook_searches_posts": 50000.00}}
)
@pytest.mark.freeze_time(CREATED_TIME)
def test_create_danek_facebook_searches_posts_gather(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test create danek facebook searches posts gather."""
    post_data = {
        "name": "First apify gather",
        "search_list": ["phoenix", "howtobuildup"],
        "stop_scraping_per_search_after_count": 10,
        "proxy_country_to_gather_from": "us",
        "posts_created_after": "2022-01-01T00:00:00+00:00",
        "posts_created_before": "2022-01-31",
        "recent_posts": True,
    }
    project_id = 1
    response = client_admin.post(
        f"/projects/{project_id}/gathers/danek_facebook_searches_posts", json=post_data
    )
    assert response.status_code == 200
    gather = response.json()

    for key, value in post_data.items():
        if key == "posts_created_before":
            assert gather[key] == "2022-01-31T00:00:00+00:00"
        else:
            assert gather[key] == value

    # These are automatically set
    assert gather["created_at"] == CREATED_TIME
    assert gather["job_run_resource_estimate"] == {
        "max_total_cost": 10,
        "max_gather_result_count": 20,
    }


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"DANEK_COST_PER_100K_RESULTS_DICT": {"danek_facebook_searches_posts": 50000.00}}
)
@pytest.mark.freeze_time(CREATED_TIME)
def test_create_invalid_datetime(reseed_tables, client_admin: TestClient, patch_settings) -> None:
    """Test create danek facebook searches posts gather."""
    post_data = {
        "name": "First apify gather",
        "search_list": ["phoenix", "howtobuildup"],
        "stop_scraping_per_search_after_count": 10,
        "proxy_country_to_gather_from": "us",
        "posts_created_after": "2022-01-02T00:00:00+00:00",
        "posts_created_before": "2022-01-01",
        "recent_posts": True,
    }
    project_id = 1
    response = client_admin.post(
        f"/projects/{project_id}/gathers/danek_facebook_searches_posts", json=post_data
    )
    assert response.status_code == 422
    json_response = response.json()
    assert (
        "posts_created_before must be after posts_created_after"
        in json_response["detail"][0]["msg"]
    )


@pytest.mark.patch_settings(
    {"DANEK_COST_PER_100K_RESULTS_DICT": {"danek_facebook_searches_posts": 50000.00}}
)
def test_patch_danek_facebook_searches_posts(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test patch danek facebook searches posts gather."""
    data = {
        "name": "Updated apify gather",
        "search_list": ["example"],
        "stop_scraping_per_search_after_count": 100,
        "proxy_country_to_gather_from": "ca",
        "posts_created_after": "2022-02-01T00:00:00+00:00",
        "posts_created_before": "2022-02-28",
        "recent_posts": False,
    }
    # Check that it is not the same as the seed values
    # just in case there are changes in the seed
    test_gather = danek_facebook_searches_posts_gather.TEST_DANEK_FACEBOOK_SEARCHES_POSTS_GATHER[0]
    project_id = test_gather.project_id
    gather_id = test_gather.id
    dict_test_gather = test_gather.dict()
    for key, value in data.items():
        assert dict_test_gather[key] != value
    response = client_admin.patch(
        f"/projects/{project_id}/gathers/danek_facebook_searches_posts/{gather_id}", json=data
    )
    json_response = response.json()
    assert response.status_code == 200
    for key, value in data.items():
        if key == "posts_created_before":
            assert json_response[key] == "2022-02-28T00:00:00+00:00"
        else:
            assert json_response[key] == value

    assert json_response["child_type"] == "danek_facebook_searches_posts"
    assert json_response["job_run_resource_estimate"] == {
        "max_total_cost": 50,
        "max_gather_result_count": 100,
    }
