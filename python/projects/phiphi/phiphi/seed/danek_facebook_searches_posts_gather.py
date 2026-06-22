"""Seed for Danek Facebook Searches Posts Gathers."""

from sqlalchemy.orm import Session

from phiphi.api.projects import gathers

TEST_DANEK_FACEBOOK_SEARCHES_POSTS_GATHER_CREATE = (
    gathers.danek_facebook_searches_posts.schemas.DanekFacebookSearchesPostsGatherCreate(
        name="Phoenix Danek Facebook Searches Posts Gather",
        search_list=[
            "phoenix",
            "howtobuildup",
        ],
        stop_scraping_per_search_after_count=10,
        proxy_country_to_gather_from=gathers.danek_facebook_searches_posts.schemas.ProxyCodes.US,
        posts_created_after="2022-01-01T00:00:00Z",
        posts_created_before="2022-01-31T00:00:00Z",
        recent_posts=True,
    )
)

TEST_DANEK_FACEBOOK_SEARCHES_POSTS_GATHER: list[
    gathers.danek_facebook_searches_posts.schemas.DanekFacebookSearchesPostsGatherResponse
] = []


def seed_test_danek_facebook_searches_posts_gathers(session: Session) -> None:
    """Seed the gathers."""
    TEST_DANEK_FACEBOOK_SEARCHES_POSTS_GATHER.clear()
    danek_facebook_gathers = [
        TEST_DANEK_FACEBOOK_SEARCHES_POSTS_GATHER_CREATE,
    ]

    for danek_facebook_gather in danek_facebook_gathers:
        gather_response = gathers.child_crud.create_child_gather(
            session=session,
            project_id=2,
            request_schema=danek_facebook_gather,
            child_model=gathers.danek_facebook_searches_posts.models.DanekFacebookSearchesPostsGather,
            response_schema=gathers.danek_facebook_searches_posts.schemas.DanekFacebookSearchesPostsGatherResponse,
            child_type=gathers.schemas.ChildTypeName.danek_facebook_searches_posts,
        )
        TEST_DANEK_FACEBOOK_SEARCHES_POSTS_GATHER.append(gather_response)
