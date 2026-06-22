"""Seed the apify facebook search posts gathers."""

from sqlalchemy.orm import Session

from phiphi.api.projects.gathers import child_crud as gather_child_crud
from phiphi.api.projects.gathers import schemas as gathers_schemas
from phiphi.api.projects.gathers.apify_facebook_search_posts import models, schemas

TEST_APIFY_FACEBOOK_SEARCH_POSTS_GATHER_CREATE = schemas.ApifyFacebookSearchPostsGatherCreate(
    name="Phoenix Apify Facebook Search Posts Gather",
    search_query="phoenix",
    limit_posts=1000,
    limit_retries=3,
    recent_posts=True,
    proxy=schemas.ApifyProxyConfig(
        use_apify_proxy=True,
        apify_proxy_groups=["RESIDENTIAL"],
    ),
)

TEST_APIFY_FACEBOOK_SEARCH_POSTS_GATHERS = []


def seed_test_apify_facebook_search_posts_gathers(session: Session) -> None:
    """Seed the gathers."""
    apify_facebook_gathers = [
        TEST_APIFY_FACEBOOK_SEARCH_POSTS_GATHER_CREATE,
    ]

    for apify_facebook_gather in apify_facebook_gathers:
        gather_response = gather_child_crud.create_child_gather(
            session=session,
            project_id=2,
            request_schema=apify_facebook_gather,
            child_model=models.ApifyFacebookSearchPostsGather,
            response_schema=schemas.ApifyFacebookSearchPostsGatherResponse,
            child_type=gathers_schemas.ChildTypeName.apify_facebook_search_posts,
        )
        TEST_APIFY_FACEBOOK_SEARCH_POSTS_GATHERS.append(gather_response)
