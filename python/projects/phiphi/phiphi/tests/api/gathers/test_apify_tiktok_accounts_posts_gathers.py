"""Tes Apify TikTok Accounts Posts Gathers."""

import datetime

import pytest
from fastapi.testclient import TestClient

from phiphi.api.projects.gathers import constants
from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.gathers.apify_tiktok_accounts_posts import schemas
from phiphi.seed import apify_tiktok_accounts_posts_gather

CREATED_TIME = "2024-04-01T12:00:01"


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_tiktok_accounts_posts": 50000.00}}
)
@pytest.mark.parametrize(
    "post_data",
    [
        {
            "name": "First apify gather",
            "limit_posts_per_account": 1000,
            "account_username_list": ["example", "test"],
            "posts_created_after": "2024-04-01",
        },
        {
            "name": "First apify gather",
            "limit_posts_per_account": 1000,
            "account_username_list": ["example", "test"],
            "posts_created_since_num_days": 7,
        },
    ],
)
@pytest.mark.freeze_time(CREATED_TIME)
def test_create_apify_tiktok_accounts_posts_gather(
    reseed_tables, client_admin: TestClient, post_data, patch_settings
) -> None:
    """Test create apify TikTok accounts posts gather."""
    project_id = 1
    response = client_admin.post(
        f"/projects/{project_id}/gathers/apify_tiktok_accounts_posts", json=post_data
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


@pytest.mark.freeze_time(CREATED_TIME)
def test_create_apify_tiktok_accounts_posts_gather_invalid(
    reseed_tables, client_admin: TestClient
) -> None:
    """Test creating apify TikTok accounts posts gather with correct since and after days."""
    data = {
        "name": "First apify gather",
        "limit_posts_per_account": 1000,
        "account_username_list": ["example"],
        "posts_created_after": "2024-04-01",
        "posts_created_since_num_days": 7,
    }
    project_id = 1
    response = client_admin.post(
        f"/projects/{project_id}/gathers/apify_tiktok_accounts_posts", json=data
    )
    assert response.status_code == 422
    response_data = response.json()
    assert response_data["detail"][0]["msg"] == (
        "Value error, posts_created_since_num_days "
        "can only be set if posts_created_after is not set (None)"
    )


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_tiktok_accounts_posts": 50000.00}}
)
def test_patch_apify_tiktok_accounts_posts(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test patch apify TikTok accounts posts gather."""
    data = {
        "name": "Updated apify gather",
        "account_username_list": ["example", "test"],
        "limit_posts_per_account": 1,
        # Check can set to None
        "posts_created_after": None,
    }
    test_gather = apify_tiktok_accounts_posts_gather.TEST_APIFY_TIKTOK_ACCOUNTS_POSTS_GATHERS[0]
    project_id = test_gather.project_id
    gather_id = test_gather.id
    dict_test_gather = test_gather.dict()
    for key, value in data.items():
        assert dict_test_gather[key] != value
    response = client_admin.patch(
        f"/projects/{project_id}/gathers/apify_tiktok_accounts_posts/{gather_id}", json=data
    )
    assert response.status_code == 200
    gather = response.json()

    assert gather["name"] == data["name"]
    assert gather["account_username_list"] == data["account_username_list"]
    assert gather["limit_posts_per_account"] == data["limit_posts_per_account"]
    assert gather["posts_created_after"] == data["posts_created_after"]
    assert gather["job_run_resource_estimate"] == {
        "max_total_cost": 1,
        "max_gather_result_count": 2,
    }


def test_serialize_tiktok_accounts_posts_gather_response_with_all_fields_1():
    """Test that ApifyTikTokAccountsPostsGatherResponse serializes correctly."""
    instance = schemas.ApifyTikTokAccountsPostsGatherResponse(
        name="Example",
        limit_posts_per_account=10,
        account_username_list=["example", "test"],
        posts_created_after="2024-04-04",
        posts_created_since_num_days=None,
        proxy_country_to_gather_from="US",
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=123,
        latest_job_run=None,
        child_type=gather_schemas.ChildTypeName.apify_tiktok_hashtags_posts,
    )

    output_dict = instance.serialize_to_apify_input()

    expected_output_dict = {
        "resultsPerPage": 10,
        "profiles": ["example", "test"],
        "oldestPostDate": "2024-04-04",
        "proxyCountryCode": "US",
        "searchSection": constants.TIKTOK_POST_SEARCH_SECTION,
    }

    assert expected_output_dict == output_dict


def test_serialize_tiktok_accounts_posts_gather_response_with_all_fields_2():
    """Test that ApifyTikTokAccountsPostsGatherResponse serializes correctly."""
    instance = schemas.ApifyTikTokAccountsPostsGatherResponse(
        name="Example",
        limit_posts_per_account=10,
        account_username_list=["example", "test"],
        posts_created_since_num_days=7,
        proxy_country_to_gather_from="US",
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=123,
        latest_job_run=None,
        child_type=gather_schemas.ChildTypeName.apify_tiktok_hashtags_posts,
    )

    output_dict = instance.serialize_to_apify_input()

    expected_output_dict = {
        "resultsPerPage": 10,
        "profiles": ["example", "test"],
        "scrapeLastNDays": 7,
        "proxyCountryCode": "US",
        "searchSection": constants.TIKTOK_POST_SEARCH_SECTION,
    }

    assert expected_output_dict == output_dict


def test_serialize_tiktok_accounts_posts_gather_response_with_required_fields_only():
    """Test that serialize to Apify correctly omits fields when they are not provided."""
    instance = schemas.ApifyTikTokAccountsPostsGatherResponse(
        name="Example",
        limit_posts_per_account=10,
        account_username_list=["example", "test"],
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=123,
        latest_job_run=None,
        child_type=gather_schemas.ChildTypeName.apify_tiktok_hashtags_posts,
    )

    output_dict = instance.serialize_to_apify_input()

    expected_keys = ["resultsPerPage", "profiles", "searchSection"]
    assert all(key in output_dict for key in expected_keys)
    assert "oldestPostDate" not in output_dict
    assert "scrapeLastNDays" not in output_dict
    assert "proxyCountryCode" not in output_dict

    expected_output_dict = {
        "resultsPerPage": 10,
        "profiles": ["example", "test"],
        "searchSection": constants.TIKTOK_POST_SEARCH_SECTION,
    }

    assert expected_output_dict == output_dict
