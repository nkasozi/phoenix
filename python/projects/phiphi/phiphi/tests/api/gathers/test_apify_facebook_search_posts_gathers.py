"""Test Apify Facebook Search Posts Gathers."""

import datetime

import pydantic
import pytest
from fastapi.testclient import TestClient
from pydantic_extra_types.country import CountryAlpha2

from phiphi.api.projects import gathers
from phiphi.seed import apify_facebook_search_posts_gather

CREATED_TIME = "2024-04-01T12:00:01"
UPDATE_TIME = "2024-04-01T12:00:02"


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_facebook_search_posts": 50000.00}}
)
@pytest.mark.freeze_time(CREATED_TIME)
def test_create_apify_facebook_search_posts_gather(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test create apify facebook search posts gather."""
    post_data = {
        "name": "First apify gather",
        "search_query": "example",
        "limit_posts": 1000,
        "limit_retries": 5,
    }
    project_id = 1
    response = client_admin.post(
        f"/projects/{project_id}/gathers/apify_facebook_search_posts", json=post_data
    )
    assert response.status_code == 200
    gather = response.json()

    for key, value in post_data.items():
        assert gather[key] == value

    # These are automatically set

    assert gather["created_at"] == CREATED_TIME
    assert gather["job_run_resource_estimate"] == {
        "max_total_cost": 500,
        "max_gather_result_count": 1000,
    }


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {"MEAN_COST_PER_100K_RESULTS_DICT": {"apify_facebook_search_posts": 50000.00}}
)
def test_patch_apify_facebook_search_posts(
    reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test patch apify facebook search posts gather."""
    data = {
        "name": "Updated apify gather",
        "search_query": "example",
        "limit_posts": 1,
        "limit_retries": 5,
    }
    # Check that it is not the same as the seed values
    # just in case there are changes in the seed
    test_gather = apify_facebook_search_posts_gather.TEST_APIFY_FACEBOOK_SEARCH_POSTS_GATHERS[0]
    project_id = test_gather.project_id
    gather_id = test_gather.id
    dict_test_gather = test_gather.dict()
    for key, value in data.items():
        assert dict_test_gather[key] != value
    response = client_admin.patch(
        f"/projects/{project_id}/gathers/apify_facebook_search_posts/{gather_id}", json=data
    )
    json_response = response.json()
    assert response.status_code == 200
    for key, value in data.items():
        assert json_response[key] == value

    assert json_response["child_type"] == "apify_facebook_search_posts"
    assert json_response["job_run_resource_estimate"] == {
        "max_total_cost": 0.5,
        "max_gather_result_count": 1,
    }


def test_validation_apify_proxy_config():
    """Test that ApifyProxyConfig throws an error if use_apify_proxy is False."""
    with pytest.raises(pydantic.ValidationError):
        gathers.apify_facebook_search_posts.schemas.ApifyProxyConfig(
            use_apify_proxy=False, apify_proxy_groups=["GROUP1", "GROUP2"]
        )


def test_validation_apify_proxy_config_country():
    """Test that ApifyProxyConfig throws validation error with in correct country code."""
    with pytest.raises(pydantic.ValidationError):
        gathers.apify_facebook_search_posts.schemas.ApifyProxyConfig(
            use_apify_proxy=True,
            apify_proxy_groups=["GROUP1", "GROUP2"],
            apify_proxy_country="NOT_A_COUNTRY",  # type: ignore[arg-type]
        )


def test_serialize_facebook_search_post_gather_response_with_all_fields():
    """Test that ApifyFacebookSearchPostsGatherResponse serializes correctly."""
    instance = gathers.apify_facebook_search_posts.schemas.ApifyFacebookSearchPostsGatherResponse(
        name="Example",
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=123,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_facebook_search_posts,
        search_query="hello",
        limit_posts=10,
        limit_retries=5,
        recent_posts=False,
        proxy=gathers.apify_facebook_search_posts.schemas.ApifyProxyConfig(
            use_apify_proxy=True,
            apify_proxy_groups=["GROUP1", "GROUP2"],
            apify_proxy_country=CountryAlpha2("US"),
        ),
    )

    output_dict = instance.serialize_to_apify_input()

    expected_output_dict = {
        "query": "hello",
        "max_posts": 10,
        "max_retries": 5,
        "recent_posts": False,
        "proxy": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["GROUP1", "GROUP2"],
            "apifyProxyCountry": "US",
        },
        # This attribute is added with the serialisation
        "search_type": gathers.constants.FACEBOOK_POST_SEARCH_TYPE,
    }

    assert expected_output_dict == output_dict


def test_serialize_facebook_search_post_gather_response_with_required_fields_only():
    """Test that serialize to Apify correctly omits fields when they are not provided."""
    instance = gathers.apify_facebook_search_posts.schemas.ApifyFacebookSearchPostsGatherResponse(
        name="Example",
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=123,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_facebook_search_posts,
        search_query="hello",
        limit_posts=10,
        limit_retries=5,
    )

    output_dict = instance.serialize_to_apify_input()

    expected_output_dict = {
        "query": "hello",
        "max_posts": 10,
        "max_retries": 5,
        "search_type": gathers.constants.FACEBOOK_POST_SEARCH_TYPE,
    }

    assert expected_output_dict == output_dict
