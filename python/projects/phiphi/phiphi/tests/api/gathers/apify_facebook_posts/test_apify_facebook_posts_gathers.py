"""Test Apify Facebook Posts Gathers."""

import datetime

import pytest
from fastapi.testclient import TestClient

from phiphi.api.projects import gathers
from phiphi.api.projects.gathers import child_crud
from phiphi.seed import apify_facebook_posts_gather

CREATED_TIME = "2024-04-01T12:00:01"
UPDATE_TIME = "2024-04-01T12:00:02"


def test_get_gather_crud(client: TestClient, reseed_tables) -> None:
    """Test getting gathers."""
    gather = child_crud.get_child_gather(reseed_tables, 1, 1)
    assert gather
    # Needed for mypy to pass
    assert isinstance(
        gather, gathers.apify_facebook_posts.schemas.ApifyFacebookPostsGatherResponse
    )
    assert gather.id == 1
    assert gather.project_id == 1
    assert gather.child_type == "apify_facebook_posts"
    assert gather.limit_posts_per_account == 1000


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_facebook_posts": 50000.00}}
)
@pytest.mark.freeze_time(CREATED_TIME)
@pytest.mark.parametrize(
    "posts_created_after,posts_created_before,expected_posts_created_after,expected_posts_created_before",
    [
        # Next day is allowed as it is one day
        ("2021-4-8", "2021-4-9", "2021-04-08T00:00:00Z", "2021-04-09T00:00:00Z"),
        # One year is allowed
        ("2021-4-8", "2022-4-8", "2021-04-08T00:00:00Z", "2022-04-08T00:00:00Z"),
        # just a nice date to check
        ("2021-4-8", "2021-5-9", "2021-04-08T00:00:00Z", "2021-05-09T00:00:00Z"),
        # ISO format with time zon
        (
            "2021-4-8T12:00:00+01:00",
            "2021-4-9T12:00:30Z",
            # Converted to UTC
            "2021-04-08T11:00:00Z",
            "2021-04-09T12:00:30Z",
        ),
    ],
)
def test_create_apify_facebook_posts_gather(
    posts_created_after,
    posts_created_before,
    expected_posts_created_after,
    expected_posts_created_before,
    reseed_tables,
    client_admin: TestClient,
    patch_settings,
) -> None:
    """Test create apify facebook gather."""
    data = {
        "name": "First apify gather",
        "limit_posts_per_account": 1000,
        "posts_created_after": posts_created_after,
        "posts_created_before": posts_created_before,
        "account_url_list": ["https://buildup.org/", "https://buildup.org/2/"],
    }
    project_id = 1
    response = client_admin.post(f"/projects/{project_id}/gathers/apify_facebook_posts", json=data)
    assert response.status_code == 200
    gather = response.json()

    assert gather["name"] == data["name"]
    assert gather["project_id"] == project_id
    assert gather["account_url_list"] == data["account_url_list"]
    assert gather["limit_posts_per_account"] == data["limit_posts_per_account"]
    assert gather["posts_created_after"] == expected_posts_created_after
    assert gather["posts_created_before"] == expected_posts_created_before
    assert gather["created_at"] == CREATED_TIME
    # Tested in its own module
    assert "job_run_resource_estimate" in gather
    gather_id = gather["id"]
    response = client_admin.get(f"/projects/{project_id}/gathers/{gather_id}")
    assert response.status_code == 200
    gather_2 = response.json()
    assert gather == gather_2


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_facebook_posts": 50000.00}}
)
def test_patch_apify_facebook_posts(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test patch apify facebook comment gather."""
    data = {
        "name": "Updated apify gather",
        "limit_posts_per_account": 1,
        "account_url_list": ["https://buildup.org/2/"],
        "posts_created_after": "2021-4-8T12:00:00+01:00",
        "posts_created_before": "2022-3-5",
    }
    # Check that it is not the same as the seed values
    # just in case there are changes in the seed
    expected_gather = apify_facebook_posts_gather.TEST_APIFY_FACEBOOK_POSTS_GATHER_CREATE.dict()
    for key, value in data.items():
        assert expected_gather[key] != value
    project_id = 1
    response = client_admin.patch(
        f"/projects/{project_id}/gathers/apify_facebook_posts/1/", json=data
    )
    assert response.status_code == 200
    gather = response.json()
    assert gather["name"] == data["name"]
    assert gather["project_id"] == project_id
    assert gather["account_url_list"] == data["account_url_list"]
    assert gather["limit_posts_per_account"] == data["limit_posts_per_account"]
    # Converted to UTC
    assert gather["posts_created_after"] == "2021-04-08T11:00:00Z"
    # Considered to be mid night UTC of the given date
    assert gather["posts_created_before"] == "2022-03-05T00:00:00Z"

    # Tested in it's own module
    assert "job_run_resource_estimate" in gather


def test_patch_apify_facebook_posts_optional(reseed_tables, client_admin: TestClient) -> None:
    """Test patch apify facebook comment gather check optional."""
    data = {
        "limit_posts_per_account": 2,
    }
    project_id = 1
    response = client_admin.patch(
        f"/projects/{project_id}/gathers/apify_facebook_posts/1/", json=data
    )
    json_response = response.json()
    assert response.status_code == 200
    expected_gather = apify_facebook_posts_gather.TEST_APIFY_FACEBOOK_POSTS_GATHER_CREATE.dict()
    expected_gather["limit_posts_per_account"] = 2
    for key, value in expected_gather.items():
        assert json_response[key] == value


def test_patch_apify_facebook_posts_invalid(reseed_tables, client_admin: TestClient) -> None:
    """Test patch apify facebook comment gather posts invalid."""
    data = {
        # values that we shouldn't be able to set in the model
        "child_type": "apify",
        "created_at": "2024-01-01",
        # Not in any schema
        "not_included_allowed": 2,
    }
    project_id = 1
    for key, value in data.items():
        response = client_admin.patch(
            f"/projects/{project_id}/gathers/apify_facebook_posts/1/", json={key: value}
        )
        assert response.status_code == 422


@pytest.mark.freeze_time(CREATED_TIME)
def test_data_type_apify_facebook_posts(reseed_tables, client_admin: TestClient) -> None:
    """Test create apify facebook gather."""
    data = {
        "name": "First apify gather",
        "limit_posts_per_account": 1000,
        "posts_created_after": "2022-3-5",
        "posts_created_before": "2022-5-8",
        "account_url_list": ["https://buildup.org/"],
    }
    project_id = 1
    response = client_admin.post(f"/projects/{project_id}/gathers/apify_facebook_posts", json=data)
    json_response = response.json()
    assert response.status_code == 200
    assert json_response["child_type"] == "apify_facebook_posts"


@pytest.mark.freeze_time(CREATED_TIME)
def test_invalid_date_posts_created_after(reseed_tables, client_admin: TestClient) -> None:
    """Test create invalid apify facebook gather."""
    data = {
        "name": "First apify gather",
        "limit_posts_per_account": 1000,
        "posts_created_after": "2022-3-100",
        "posts_created_before": "2022-5-8",
        "account_url_list": ["https://buildup.org/"],
    }
    project_id = 1
    response = client_admin.post(f"/projects/{project_id}/gathers/apify_facebook_posts", json=data)
    assert response.status_code == 422


@pytest.mark.freeze_time(CREATED_TIME)
def test_invalid_date_posts_created_before(reseed_tables, client_admin: TestClient) -> None:
    """Test create invalid apify facebook gather."""
    data = {
        "name": "First apify gather",
        "limit_posts_per_account": 1000,
        "posts_created_after": "2022-3-2",
        "posts_created_before": "20220-5-8",
        "account_url_list": ["https://buildup.org/"],
    }
    project_id = 1
    response = client_admin.post(f"/projects/{project_id}/gathers/apify_facebook_posts", json=data)
    assert response.status_code == 422


@pytest.mark.freeze_time(CREATED_TIME)
def test_invalid_date_range(reseed_tables, client_admin: TestClient) -> None:
    """Test create invalid apify facebook gather."""
    data = {
        "name": "First apify gather",
        "limit_posts_per_account": 1000,
        # posts_created_after is after posts_created_before
        "posts_created_after": "2022-3-5",
        "posts_created_before": "2022-3-4",
        "account_url_list": ["https://buildup.org/"],
    }
    project_id = 1
    response = client_admin.post(f"/projects/{project_id}/gathers/apify_facebook_posts", json=data)
    assert response.status_code == 422


@pytest.mark.freeze_time(CREATED_TIME)
def test_invalid_date_range_days(reseed_tables, client_admin: TestClient) -> None:
    """Test create invalid apify facebook gather."""
    data = {
        "name": "First apify gather",
        "limit_posts_per_account": 1000,
        # date range is more then 365 days
        "posts_created_after": "2022-3-5",
        "posts_created_before": "2023-3-6",
        "account_url_list": ["https://buildup.org/"],
    }
    project_id = 1
    response = client_admin.post(f"/projects/{project_id}/gathers/apify_facebook_posts", json=data)
    assert response.status_code == 422


@pytest.mark.freeze_time(CREATED_TIME)
def test_invalid_list(reseed_tables, client_admin: TestClient) -> None:
    """Test create invalid apify facebook gather."""
    data = {
        "name": "First apify gather",
        "limit_posts_per_account": 1000,
        "posts_created_after": "2022-3-5",
        "posts_created_before": "2022-3-6",
        # List length is too long
        "account_url_list": ["https://buildup.org/"] * 201,
    }
    project_id = 1
    response = client_admin.post(f"/projects/{project_id}/gathers/apify_facebook_posts", json=data)
    assert response.status_code == 422
    json = response.json()
    assert "200" in json["detail"][0]["msg"]


def test_serialize_facebook_post_gather_response_with_all_fields():
    """Test that ApifyFacebookPostsGatherResponse serializes correctly."""
    instance = gathers.apify_facebook_posts.schemas.ApifyFacebookPostsGatherResponse(
        name="Example",
        limit_posts_per_account=10,
        account_url_list=[
            "https://www.facebook.com/humansofnewyork/",
            "https://www.facebook.com/example_account/",
        ],
        posts_created_after="2024-04-03T01:00:00+01:00",
        posts_created_before="2024-04-04",
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=123,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_facebook_posts,
    )

    output_dict = instance.serialize_to_apify_input()

    expected_output_dict = {
        "resultsLimit": 10,
        "startUrls": [
            {"url": "https://www.facebook.com/humansofnewyork/"},
            {"url": "https://www.facebook.com/example_account/"},
        ],
        # Date time is converted to UTC
        "onlyPostsNewerThan": "2024-04-03T00:00:00Z",
        # Considered to be mid night UTC of the given date
        "onlyPostsOlderThan": "2024-04-04T00:00:00Z",
    }

    assert expected_output_dict == output_dict


def test_serialize_facebook_post_gather_response_with_required_fields_only():
    """Test that serialize to Apify correctly omits fields when they are not provided."""
    instance = gathers.apify_facebook_posts.schemas.ApifyFacebookPostsGatherResponse(
        name="Example",
        limit_posts_per_account=10,
        account_url_list=[
            "https://www.facebook.com/humansofnewyork/",
            "https://www.facebook.com/example_account/",
        ],
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=123,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_facebook_posts,
    )

    output_dict = instance.serialize_to_apify_input()

    expected_keys = ["resultsLimit", "startUrls"]
    assert all(key in output_dict for key in expected_keys)
    assert "onlyPostsOlderThan" not in output_dict
    assert "onlyPostsNewerThan" not in output_dict

    expected_output_dict = {
        "resultsLimit": 10,
        "startUrls": [
            {"url": "https://www.facebook.com/humansofnewyork/"},
            {"url": "https://www.facebook.com/example_account/"},
        ],
    }

    assert expected_output_dict == output_dict
