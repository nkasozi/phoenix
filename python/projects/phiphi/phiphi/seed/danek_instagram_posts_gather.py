"""Seed for Danek Facebook Searches Posts Gathers."""

from sqlalchemy.orm import Session

from phiphi.api.projects import gathers

TEST_DANEK_INSTAGRAM_POSTS_GATHER_CREATE = (
    gathers.danek_instagram_posts.schemas.DanekInstagramPostsGatherCreate(
        name="Phoenix Danek Instagram Posts Gather",
        account_username_list=[
            "phoenix",
            "howtobuildup",
        ],
        limit_posts_per_account=10,
        posts_created_after="2022-01-01T00:00:00Z",
    )
)

TEST_DANEK_INSTAGRAM_POSTS_GATHER: list[
    gathers.danek_instagram_posts.schemas.DanekInstagramPostsGatherResponse
] = []


def seed_test_danek_instagram_posts_gathers(session: Session) -> None:
    """Seed the gathers."""
    TEST_DANEK_INSTAGRAM_POSTS_GATHER.clear()
    danek_facebook_gathers = [
        TEST_DANEK_INSTAGRAM_POSTS_GATHER_CREATE,
    ]

    for danek_facebook_gather in danek_facebook_gathers:
        gather_response = gathers.child_crud.create_child_gather(
            session=session,
            project_id=2,
            request_schema=danek_facebook_gather,
            child_model=gathers.danek_instagram_posts.models.DanekInstagramPostsGather,
            response_schema=gathers.danek_instagram_posts.schemas.DanekInstagramPostsGatherResponse,
            child_type=gathers.schemas.ChildTypeName.danek_instagram_posts,
        )
        TEST_DANEK_INSTAGRAM_POSTS_GATHER.append(gather_response)
