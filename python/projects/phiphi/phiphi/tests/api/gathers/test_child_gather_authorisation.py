"""Test child gather authorisation.

This tests just a subset of the child gathers with the idea that if it works for these it will work
for the rest. In that the child route code is generalised across all child gathers.

Admin access is tested in the test for each gather type.
"""

from fastapi.testclient import TestClient


def test_create_apify_facebook_comments_gather_no_access(
    reseed_tables, client: TestClient
) -> None:
    """Test create apify facebook comment gather no access."""
    data = {
        "name": "First apify gather",
        "limit_comments_per_post": 1000,
        "sort_comments_by": "facebook_default",
        "post_url_list": ["https://buildup.org/", "https://buildup.org/2/"],
        "include_comment_replies": True,
    }
    project_id = 1
    response = client.post(f"/projects/{project_id}/gathers/apify_facebook_comments", json=data)
    assert response.status_code == 401


def test_create_apify_facebook_comments_gather_user_access(
    reseed_tables, client_user_1: TestClient
) -> None:
    """Test create apify facebook comment gather user access."""
    data = {
        "name": "First apify gather",
        "limit_comments_per_post": 1000,
        "sort_comments_by": "facebook_default",
        "post_url_list": ["https://buildup.org/", "https://buildup.org/2/"],
        "include_comment_replies": True,
    }
    project_id = 1
    response = client_user_1.post(
        f"/projects/{project_id}/gathers/apify_facebook_comments", json=data
    )
    assert response.status_code == 200


def test_patch_apify_facebook_posts_no_access(reseed_tables, client: TestClient) -> None:
    """Test patch apify facebook comment gather no access."""
    data = {
        "name": "Updated apify gather",
        "limit_posts_per_account": 1,
        "account_url_list": ["https://buildup.org/2/"],
        "posts_created_after": "2021-4-8T12:00:00+01:00",
        "posts_created_before": "2022-3-5",
    }
    project_id = 1
    response = client.patch(f"/projects/{project_id}/gathers/apify_facebook_posts/1/", json=data)
    assert response.status_code == 401


def test_patch_apify_facebook_posts_user_access(reseed_tables, client_user_1: TestClient) -> None:
    """Test patch apify facebook posts gather user access."""
    data = {
        "name": "Updated apify gather",
        "limit_posts_per_account": 1,
        "account_url_list": ["https://buildup.org/2/"],
        "posts_created_after": "2021-4-8T12:00:00+01:00",
        "posts_created_before": "2022-3-5",
    }
    project_id = 1
    response = client_user_1.patch(
        f"/projects/{project_id}/gathers/apify_facebook_posts/1/", json=data
    )
    assert response.status_code == 200
