"""Seed the apify facebook post gathers."""

from sqlalchemy.orm import Session

from phiphi.api.projects.gathers import child_crud as gather_child_crud
from phiphi.api.projects.gathers import schemas as gathers_schemas
from phiphi.api.projects.gathers.apify_facebook_posts import models, schemas

TEST_APIFY_FACEBOOK_POSTS_GATHER_CREATE = schemas.ApifyFacebookPostsGatherCreate(
    name="Phoenix Apify Facebook Post Gather",
    account_url_list=["https://phoenix.com", "https://buildup.org"],
    limit_posts_per_account=1000,
    posts_created_after="2024-04-25",
    posts_created_before="2024-05-02",
)

TEST_APIFY_FACEBOOK_POSTS_GATHER_CREATE_2 = schemas.ApifyFacebookPostsGatherCreate(
    name="Phoenix Apify Facebook Post Gather 2",
    account_url_list=["https://phoenix.com", "https://buildup.org"],
    limit_posts_per_account=1000,
    posts_created_after="2024-03-12",
    posts_created_before="2024-05-01",
)

TEST_APIFY_FACEBOOK_POSTS_GATHER_CREATE_3 = schemas.ApifyFacebookPostsGatherCreate(
    name="Phoenix Apify Facebook Post Gather 3",
    account_url_list=["https://phoenix.com"],
    limit_posts_per_account=1000,
    posts_created_after="2024-02-25",
    posts_created_before="2024-05-03",
)


def seed_test_apify_facebook_posts_gathers(session: Session) -> None:
    """Seed the gathers."""
    apify_facebook_gathers = [
        TEST_APIFY_FACEBOOK_POSTS_GATHER_CREATE,
        TEST_APIFY_FACEBOOK_POSTS_GATHER_CREATE_2,
    ]

    for apify_facebook_gather in apify_facebook_gathers:
        gather_child_crud.create_child_gather(
            session=session,
            project_id=1,
            request_schema=apify_facebook_gather,
            child_model=models.ApifyFacebookPostsGather,
            response_schema=schemas.ApifyFacebookPostsGatherResponse,
            child_type=gathers_schemas.ChildTypeName.apify_facebook_posts,
        )

    gather_child_crud.create_child_gather(
        session=session,
        project_id=2,
        request_schema=TEST_APIFY_FACEBOOK_POSTS_GATHER_CREATE_3,
        child_model=models.ApifyFacebookPostsGather,
        response_schema=schemas.ApifyFacebookPostsGatherResponse,
        child_type=gathers_schemas.ChildTypeName.apify_facebook_posts,
    )
