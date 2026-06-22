"""Test Apify Facebook Posts Gathers."""

import datetime

import pytest
from fastapi.testclient import TestClient

from phiphi.api.projects import gathers
from phiphi.api.projects.gathers import child_crud
from phiphi.seed import apify_facebook_comments_gather

CREATED_TIME = "2024-04-01T12:00:01"
UPDATE_TIME = "2024-04-01T12:00:02"


def test_get_gather_crud(client: TestClient, reseed_tables) -> None:
    """Test getting gathers."""
    gather = child_crud.get_child_gather(reseed_tables, 2, 4)
    assert gather
    # Needed for mypy to pass
    assert isinstance(
        gather, gathers.apify_facebook_comments.schemas.ApifyFacebookCommentsGatherResponse
    )
    assert gather.id == 4
    assert gather.project_id == 2
    assert gather.child_type == "apify_facebook_comments"
    assert gather.limit_comments_per_post == 1000


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_facebook_comments": 50000.00}}
)
@pytest.mark.freeze_time(CREATED_TIME)
def test_create_apify_facebook_comments_gather(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test create apify facebook comment gather."""
    data = {
        "name": "First apify gather",
        "limit_comments_per_post": 1000,
        "sort_comments_by": "facebook_default",
        "post_url_list": ["https://buildup.org/", "https://buildup.org/2/"],
        "include_comment_replies": True,
    }
    project_id = 1
    response = client_admin.post(
        f"/projects/{project_id}/gathers/apify_facebook_comments", json=data
    )
    assert response.status_code == 200
    gather = response.json()

    assert gather["name"] == data["name"]
    assert gather["project_id"] == project_id
    assert gather["sort_comments_by"] == data["sort_comments_by"]
    assert gather["limit_comments_per_post"] == data["limit_comments_per_post"]
    assert gather["include_comment_replies"] == data["include_comment_replies"]
    assert gather["post_url_list"] == data["post_url_list"]
    assert gather["created_at"] == CREATED_TIME
    assert gather["job_run_resource_estimate"] == {
        "max_total_cost": 1000,
        "max_gather_result_count": 2000,
    }


@pytest.mark.freeze_time(CREATED_TIME)
def test_child_type_type_apify_facebook_comments(reseed_tables, client_admin: TestClient) -> None:
    """Test create apify facebook comment gather."""
    data = {
        "name": "First apify gather",
        "limit_comments_per_post": 1000,
        "sort_comments_by": "facebook_default",
        "post_url_list": ["https://buildup.org/"],
        "include_comment_replies": True,
    }
    project_id = 1
    response = client_admin.post(
        f"/projects/{project_id}/gathers/apify_facebook_comments", json=data
    )
    json_response = response.json()
    assert response.status_code == 200
    assert json_response["child_type"] == "apify_facebook_comments"


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_facebook_comments": 50000.00}}
)
def test_patch_apify_facebook_comments(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test patch apify facebook comment gather."""
    data = {
        "name": "Updated apify gather",
        "limit_comments_per_post": 1,
        "sort_comments_by": "most_relevant",
        "post_url_list": ["https://buildup.org/2/"],
        "include_comment_replies": True,
    }
    # Check that it is not the same as the seed values
    # just in case there are changes in the seed
    expected_gather = (
        apify_facebook_comments_gather.TEST_APIFY_FACEBOOK_COMMENTS_GATHER_CREATE.dict()
    )
    for key, value in data.items():
        assert expected_gather[key] != value
    project_id = 2
    response = client_admin.patch(
        f"/projects/{project_id}/gathers/apify_facebook_comments/4/", json=data
    )
    json_response = response.json()
    assert response.status_code == 200
    for key, value in data.items():
        assert json_response[key] == value
    assert json_response["job_run_resource_estimate"] == {
        "max_total_cost": 0.5,
        "max_gather_result_count": 1,
    }


def test_patch_apify_facebook_comments_invalid(reseed_tables, client_admin: TestClient) -> None:
    """Test patch apify facebook comment gather invalid."""
    data = {
        "child_type": "apify_facebook_comments",
        "not_included_allowed": "not_allowed",
    }
    project_id = 2
    for key, value in data.items():
        response = client_admin.patch(
            f"/projects/{project_id}/gathers/apify_facebook_comments/4/", json={key: value}
        )
        assert response.status_code == 422


def test_serialize_facebook_comment_gather_response_with_all_fields():
    """Test that ApifyFacebookCommentsGatherResponse serializes correctly."""
    instance = gathers.apify_facebook_comments.schemas.ApifyFacebookCommentsGatherResponse(
        name="Example",
        limit_comments_per_post=25,
        post_url_list=[
            "https://www.facebook.com/post1",
            "https://www.facebook.com/post2",
        ],
        sort_comments_by=gathers.apify_facebook_comments.schemas.FacebookCommentSortOption.most_relevant,
        include_comment_replies=True,
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=123,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_facebook_comments,
    )

    output_dict = instance.serialize_to_apify_input()

    expected_output_dict = {
        "resultsLimit": 25,
        "startUrls": [
            {"url": "https://www.facebook.com/post1"},
            {"url": "https://www.facebook.com/post2"},
        ],
        "viewOption": "RANKED_THREADED",
        "includeNestedComments": True,
    }

    assert expected_output_dict == output_dict


def test_serialize_facebook_comment_gather_response_with_required_fields_only():
    """Test that serialize to Apify correctly omits fields when they are not provided."""
    instance = gathers.apify_facebook_comments.schemas.ApifyFacebookCommentsGatherResponse(
        name="Example",
        limit_comments_per_post=25,
        post_url_list=[
            "https://www.facebook.com/post1",
            "https://www.facebook.com/post2",
        ],
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=123,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_facebook_comments,
    )

    output_dict = instance.serialize_to_apify_input()

    # Checking if the keys related to the sort option and nested comments are not present
    # since they weren't initialized.
    expected_keys = ["resultsLimit", "startUrls"]
    assert all(key in output_dict for key in expected_keys)
    assert "viewOption" not in output_dict
    assert "includeNestedComments" not in output_dict

    expected_output_dict = {
        "resultsLimit": 25,
        "startUrls": [
            {"url": "https://www.facebook.com/post1"},
            {"url": "https://www.facebook.com/post2"},
        ],
    }

    assert expected_output_dict == output_dict
