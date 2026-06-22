"""Test Danek Instagram Comments Gathers."""

import datetime

import pytest
from fastapi.testclient import TestClient

from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.gathers.danek_instagram_comments import schemas as ig_comments_schemas
from phiphi.seed import danek_instagram_comments_gather

CREATED_TIME = "2024-04-01T12:00:01"


# Make the danek cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"DANEK_COST_PER_100K_RESULTS_DICT": {"danek_instagram_comments": 50000.00}}
)
@pytest.mark.freeze_time(CREATED_TIME)
def test_create_danek_instagram_comments_gather(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test create danek instagram comments gather."""
    post_data = {
        "name": "First danek instagram comments gather",
        "post_id_list": ["1", "2"],
        "limit_comments_per_post": 10,
    }
    project_id = 1
    response = client_admin.post(
        f"/projects/{project_id}/gathers/danek_instagram_comments", json=post_data
    )
    assert response.status_code == 200
    gather = response.json()

    for key, value in post_data.items():
        assert gather[key] == value

    assert gather["created_at"] == CREATED_TIME
    # 2 posts * 10 comments = 20 results; cost = 20 * 0.5 = 10
    assert gather["job_run_resource_estimate"] == {
        "max_total_cost": 10,
        "max_gather_result_count": 20,
    }


@pytest.mark.patch_settings(
    {"DANEK_COST_PER_100K_RESULTS_DICT": {"danek_instagram_comments": 50000.00}}
)
def test_patch_danek_instagram_comments_gather(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test patch danek instagram comments gather."""
    data = {
        "name": "Updated danek instagram comments gather",
        "post_id_list": ["99"],
        "limit_comments_per_post": 100,
    }
    # Check that it is not the same as the seed values
    # just in case there are changes in the seed
    test_gather = danek_instagram_comments_gather.TEST_DANEK_INSTAGRAM_COMMENTS_GATHER[0]
    project_id = test_gather.project_id
    gather_id = test_gather.id
    dict_test_gather = test_gather.dict()
    for key, value in data.items():
        assert dict_test_gather[key] != value
    response = client_admin.patch(
        f"/projects/{project_id}/gathers/danek_instagram_comments/{gather_id}", json=data
    )
    json_response = response.json()
    assert response.status_code == 200
    for key, value in data.items():
        assert json_response[key] == value

    assert json_response["child_type"] == "danek_instagram_comments"
    # 1 post * 100 comments = 100 results; cost = 100 * 0.5 = 50
    assert json_response["job_run_resource_estimate"] == {
        "max_total_cost": 50,
        "max_gather_result_count": 100,
    }


# Unit tests for job_run_resource_estimate on DanekInstagramCommentsGatherResponse
# The formula is: max_comments * (1 + limit_child_comments_per_comment)
# i.e. top-level comments + child comments. This is already correct in the schema.
# Cost: 50000/100k = 0.5 per result
COST_DICT = {"danek_instagram_comments": 50000.0}


@pytest.mark.patch_settings({"DANEK_COST_PER_100K_RESULTS_DICT": COST_DICT})
@pytest.mark.parametrize(
    "post_ids,limit_comments,limit_child_comments,expected_result_count,expected_cost",
    [
        # No child comments: 2 posts * 10 = 20; cost = 20 * 0.5 = 10
        (["1", "2"], 10, 0, 20, 10.0),
        # With child comments: 1 post * 10 = 10; 10 * (1 + 2) = 30; cost = 15
        (["1"], 10, 2, 30, 15),
        (["1"], 10, 9, 100, 50),
        # Multiple posts with child comments: 3 * 10 = 30; 30 * (1 + 2) = 90; cost = 45
        (["1", "2", "3"], 10, 2, 90, 45.0),
    ],
)
def test_job_run_resource_estimate(
    patch_settings,
    post_ids: list,
    limit_comments: int,
    limit_child_comments: int,
    expected_result_count: int,
    expected_cost: float,
) -> None:
    """Test job_run_resource_estimate for DanekInstagramCommentsGatherResponse."""
    response = ig_comments_schemas.DanekInstagramCommentsGatherResponse(
        id=1,
        project_id=1,
        name="test gather",
        child_type=gather_schemas.ChildTypeName.danek_instagram_comments,
        created_at=datetime.datetime(2024, 1, 1),
        updated_at=datetime.datetime(2024, 1, 1),
        post_id_list=post_ids,
        limit_comments_per_post=limit_comments,
        limit_child_comments_per_comment=limit_child_comments,
    )
    assert response.job_run_resource_estimate.max_gather_result_count == expected_result_count
    assert response.job_run_resource_estimate.max_total_cost == expected_cost
