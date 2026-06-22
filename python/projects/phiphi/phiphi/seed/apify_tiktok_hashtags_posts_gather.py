"""Seed the apify tiktok hashtags post gathers."""

from sqlalchemy.orm import Session

from phiphi.api.projects.gathers import child_crud as gather_child_crud
from phiphi.api.projects.gathers import schemas as gathers_schemas
from phiphi.api.projects.gathers.apify_tiktok_hashtags_posts import models, schemas

TEST_APIFY_TIKTOK_HASHTAGS_POSTS_GATHER_CREATE = schemas.ApifyTikTokHashtagsPostsGatherCreate(
    name="Phoenix Apify TikTok Hashtags Posts Gather",
    hashtag_list=["hashtag1", "hashtag2"],
    limit_posts_per_hashtag=1000,
    proxy_country_to_gather_from="US",
)

TEST_APIFY_TIKTOK_HASHTAGS_POSTS_GATHERS = []


def seed_test_apify_tiktok_hashtags_posts_gathers(session: Session) -> None:
    """Seed the gathers."""
    apify_tiktok_gathers = [
        TEST_APIFY_TIKTOK_HASHTAGS_POSTS_GATHER_CREATE,
    ]

    for apify_tiktok_gather in apify_tiktok_gathers:
        tiktok_gather = gather_child_crud.create_child_gather(
            session=session,
            project_id=2,
            request_schema=apify_tiktok_gather,
            child_model=models.ApifyTikTokHashtagsPostsGather,
            response_schema=schemas.ApifyTikTokHashtagsPostsGatherResponse,
            child_type=gathers_schemas.ChildTypeName.apify_tiktok_hashtags_posts,
        )
        TEST_APIFY_TIKTOK_HASHTAGS_POSTS_GATHERS.append(tiktok_gather)
