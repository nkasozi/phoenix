"""Test Apify Facebook Posts Gathers."""

import pytest
from fastapi.testclient import TestClient

from phiphi.seed import apify_facebook_posts_gather

CREATED_TIME = "2024-04-01T12:00:01"


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_facebook_posts": 50000.00}}
)
@pytest.mark.freeze_time(CREATED_TIME)
@pytest.mark.parametrize(
    (
        "limit_posts_per_account,"
        "posts_created_after,"
        "posts_created_before,"
        "expected_max_gather_result_count"
    ),
    [
        # Test with no date range
        # 10 posts per account, no date range
        (10, None, None, 20),
        # Test with date range
        # 3 posts per account, for 1 day
        (10, "2024-04-01", "2024-04-02", 6),
        # Test with date range
        # None for posts_created_before will mean today (CREATED_TIME)
        # 3 posts per account, for 1 day
        (10, "2024-03-31", None, 6),
        # Test with date range
        # But limit per account max is less then the no of days max
        # 3 posts per account, for 1 day
        (2, "2024-04-01", "2024-04-02", 4),
    ],
)
def test_create_update_job_run_resource_estimate(
    limit_posts_per_account,
    posts_created_after,
    posts_created_before,
    expected_max_gather_result_count,
    reseed_tables,
    client_admin: TestClient,
    patch_settings,
) -> None:
    """Test create apify facebook gather job_run_resource_estimate."""
    data = {
        "name": "First apify gather",
        "limit_posts_per_account": limit_posts_per_account,
        "posts_created_after": posts_created_after,
        "posts_created_before": posts_created_before,
        "account_url_list": ["https://buildup.org/", "https://buildup.org/2/"],
    }
    project_id = 1
    response = client_admin.post(f"/projects/{project_id}/gathers/apify_facebook_posts", json=data)
    assert response.status_code == 200
    gather = response.json()
    assert (
        gather["job_run_resource_estimate"]["max_gather_result_count"]
        == expected_max_gather_result_count
    )
    assert (
        gather["job_run_resource_estimate"]["max_total_cost"]
        == 0.5 * expected_max_gather_result_count
    )

    # Test the update also returns the correct job_run_resource_estimate
    expected_gather = apify_facebook_posts_gather.TEST_APIFY_FACEBOOK_POSTS_GATHER_CREATE.dict()
    for key, value in data.items():
        assert expected_gather[key] != value
    project_id = 1
    response = client_admin.patch(
        f"/projects/{project_id}/gathers/apify_facebook_posts/1", json=data
    )
    assert (
        gather["job_run_resource_estimate"]["max_gather_result_count"]
        == expected_max_gather_result_count
    )
    assert (
        gather["job_run_resource_estimate"]["max_total_cost"]
        == 0.5 * expected_max_gather_result_count
    )
