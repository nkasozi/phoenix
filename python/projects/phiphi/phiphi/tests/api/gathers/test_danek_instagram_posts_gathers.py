"""Test Danek Facebook Searches Posts Gathers."""

import datetime

import pytest
from fastapi.testclient import TestClient

from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.gathers.danek_instagram_posts import schemas as ig_posts_schemas
from phiphi.seed import danek_instagram_posts_gather

CREATED_TIME = "2024-04-01T12:00:01"
UPDATE_TIME = "2024-04-01T12:00:02"


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"DANEK_COST_PER_100K_RESULTS_DICT": {"danek_instagram_posts": 50000.00}}
)
@pytest.mark.freeze_time(CREATED_TIME)
def test_create_danek_instagram_posts_gather(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test create danek instagrams posts gather."""
    post_data = {
        "name": "First apify gather",
        "account_username_list": ["phoenix", "howtobuildup"],
        "limit_posts_per_account": 10,
        "posts_created_after": "2022-01-01T00:00:00+00:00",
    }
    project_id = 1
    response = client_admin.post(
        f"/projects/{project_id}/gathers/danek_instagram_posts", json=post_data
    )
    assert response.status_code == 200
    gather = response.json()

    for key, value in post_data.items():
        assert gather[key] == value

    # These are automatically set
    assert gather["created_at"] == CREATED_TIME
    assert gather["job_run_resource_estimate"] == {
        "max_total_cost": 10,
        "max_gather_result_count": 20,
    }


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"DANEK_COST_PER_100K_RESULTS_DICT": {"danek_instagram_posts": 50000.00}}
)
@pytest.mark.freeze_time(CREATED_TIME)
def test_create_invalid_datetime(reseed_tables, client_admin: TestClient, patch_settings) -> None:
    """Test create danek instagram posts gather."""
    post_data = {
        "name": "First apify gather",
        "account_username_list": ["phoenix", "howtobuildup"],
        "limit_posts_per_account": 10,
        "posts_created_after": "20225252",
    }
    project_id = 1
    response = client_admin.post(
        f"/projects/{project_id}/gathers/danek_instagram_posts", json=post_data
    )
    assert response.status_code == 422
    json_response = response.json()
    assert "Value error, Datetime" in json_response["detail"][0]["msg"]


@pytest.mark.patch_settings(
    {"DANEK_COST_PER_100K_RESULTS_DICT": {"danek_instagram_posts": 50000.00}}
)
def test_patch_danek_instagram_posts(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test patch danek instagram posts gather."""
    data = {
        "name": "Updated apify gather",
        "account_username_list": ["example"],
        "limit_posts_per_account": 100,
        "posts_created_after": "2022-02-01T00:00:00+00:00",
    }
    # Check that it is not the same as the seed values
    # just in case there are changes in the seed
    test_gather = danek_instagram_posts_gather.TEST_DANEK_INSTAGRAM_POSTS_GATHER[0]
    project_id = test_gather.project_id
    gather_id = test_gather.id
    dict_test_gather = test_gather.dict()
    for key, value in data.items():
        assert dict_test_gather[key] != value
    response = client_admin.patch(
        f"/projects/{project_id}/gathers/danek_instagram_posts/{gather_id}", json=data
    )
    json_response = response.json()
    assert response.status_code == 200
    for key, value in data.items():
        assert json_response[key] == value

    assert json_response["child_type"] == "danek_instagram_posts"
    assert json_response["job_run_resource_estimate"] == {
        "max_total_cost": 50,
        "max_gather_result_count": 100,
    }


# Unit tests for job_run_resource_estimate on DanekInstagramPostsGatherResponse
# Posts cost: 50000/100k = 0.5 per post; Comments cost: 20000/100k = 0.2 per comment
COST_DICT = {"danek_instagram_posts": 50000.0, "danek_instagram_comments": 20000.0}


@pytest.mark.patch_settings({"DANEK_COST_PER_100K_RESULTS_DICT": COST_DICT})
@pytest.mark.parametrize(
    "accounts,scrape_comments,limit_child_comments,expected_result_count,expected_cost",
    [
        # No comments: 1 account * 10 posts = 10 results; cost = 10 * 0.5 = 5
        (["a"], 0, 0, 10, 5.0),
        # scrape_comments=5: posts=10, comments=10*5=50; cost=5+10=15
        (["a"], 5, 0, 60, 15.0),
        # Both fields: posts=10, comments=10*3*(1+2)=90; cost=5+18=23
        (["a"], 3, 2, 100, 23.0),
        # Multiple accounts: 3 accounts * 10 posts = 30; comments=30*5=150; cost=15+30=45
        (["a", "b", "c"], 5, 0, 180, 45.0),
    ],
)
def test_job_run_resource_estimate(
    patch_settings,
    accounts: list,
    scrape_comments: int,
    limit_child_comments: int,
    expected_result_count: int,
    expected_cost: float,
) -> None:
    """Test job_run_resource_estimate for DanekInstagramPostsGatherResponse."""
    response = ig_posts_schemas.DanekInstagramPostsGatherResponse(
        id=1,
        project_id=1,
        name="test gather",
        child_type=gather_schemas.ChildTypeName.danek_instagram_posts,
        created_at=datetime.datetime(2024, 1, 1),
        updated_at=datetime.datetime(2024, 1, 1),
        account_username_list=accounts,
        limit_posts_per_account=10,
        scrape_comments_count_per_post=scrape_comments,
        limit_child_comments_per_comment=limit_child_comments,
    )
    assert response.job_run_resource_estimate.max_gather_result_count == expected_result_count
    assert response.job_run_resource_estimate.max_total_cost == expected_cost
