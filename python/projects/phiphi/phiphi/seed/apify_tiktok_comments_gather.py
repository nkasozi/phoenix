"""Seed the apify tiktok COMMENT gathers."""

from sqlalchemy.orm import Session

from phiphi.api.projects.gathers import child_crud as gather_child_crud
from phiphi.api.projects.gathers import schemas as gathers_schemas
from phiphi.api.projects.gathers.apify_tiktok_comments import models, schemas

TEST_APIFY_TIKTOK_COMMENTS_GATHER_CREATE = schemas.ApifyTikTokCommentsGatherCreate(
    name="Phoenix Apify TikTok COMMENT Gather",
    post_url_list=[
        "https://www.tiktok.com/@phoenix/video/1234567890123456789",
        "https://www.tiktok.com/@howtobuildup/video/0987654321098765432",
    ],
    limit_total_comments=1000,
    include_comment_replies=False,
)

TEST_APIFY_TIKTOK_COMMENTS_GATHERS = []


def seed_test_apify_tiktok_comments_gathers(session: Session) -> None:
    """Seed the gathers."""
    apify_tiktok_gathers = [
        TEST_APIFY_TIKTOK_COMMENTS_GATHER_CREATE,
    ]

    for apify_tiktok_gather in apify_tiktok_gathers:
        gather_response = gather_child_crud.create_child_gather(
            session=session,
            project_id=2,
            request_schema=apify_tiktok_gather,
            child_model=models.ApifyTikTokCommentsGather,
            response_schema=schemas.ApifyTikTokCommentsGatherResponse,
            child_type=gathers_schemas.ChildTypeName.apify_tiktok_comments,
        )
        TEST_APIFY_TIKTOK_COMMENTS_GATHERS.append(gather_response)
