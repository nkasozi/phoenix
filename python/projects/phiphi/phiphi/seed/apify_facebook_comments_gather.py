"""Seed the apify facebook COMMENT gathers."""

from sqlalchemy.orm import Session

from phiphi.api.projects.gathers import child_crud as gather_child_crud
from phiphi.api.projects.gathers import schemas as gathers_schemas
from phiphi.api.projects.gathers.apify_facebook_comments import models, schemas

TEST_APIFY_FACEBOOK_COMMENTS_GATHER_CREATE = schemas.ApifyFacebookCommentsGatherCreate(
    name="Phoenix Apify Facebook COMMENT Gather",
    post_url_list=["https://phoenix.com", "https://buildup.org"],
    limit_comments_per_post=1000,
    sort_comments_by=schemas.FacebookCommentSortOption.facebook_default,
    include_comment_replies=False,
)

TEST_APIFY_FACEBOOK_COMMENTS_GATHER_CREATE_2 = schemas.ApifyFacebookCommentsGatherCreate(
    name="Phoenix Apify Facebook COMMENT Gather 2",
    post_url_list=["https://phoenix.com", "https://buildup.org"],
    limit_comments_per_post=1000,
    sort_comments_by=schemas.FacebookCommentSortOption.most_relevant,
    include_comment_replies=True,
)

TEST_APIFY_FACEBOOK_COMMENTS_GATHER_CREATE_3 = schemas.ApifyFacebookCommentsGatherCreate(
    name="Phoenix Apify Facebook COMMENT Gather 3 - used for estimate gather above credits",
    post_url_list=["https://phoenix.com", "https://buildup.org"],
    limit_comments_per_post=3000,
    sort_comments_by=schemas.FacebookCommentSortOption.newest_first,
    include_comment_replies=False,
)

TEST_APIFY_FACEBOOK_COMMENTS_GATHER_CREATE_4 = schemas.ApifyFacebookCommentsGatherCreate(
    name="Phoenix Apify Facebook COMMENT Gather 4",
    post_url_list=["https://phoenix.com"],
    limit_comments_per_post=10,
    sort_comments_by=schemas.FacebookCommentSortOption.newest_first,
    include_comment_replies=False,
)

TEST_APIFY_FACEBOOK_COMMENTS_GATHER_CREATE_5 = schemas.ApifyFacebookCommentsGatherCreate(
    name="Phoenix Apify Facebook COMMENT Gather 5",
    post_url_list=["https://phoenix.com"],
    limit_comments_per_post=10,
    sort_comments_by=schemas.FacebookCommentSortOption.newest_first,
    include_comment_replies=False,
)


TEST_APIFY_FACEBOOK_COMMENTS_GATHER_CREATE_6 = schemas.ApifyFacebookCommentsGatherCreate(
    name="Phoenix Apify Facebook COMMENT Gather 6",
    post_url_list=["https://phoenix.com"],
    limit_comments_per_post=10,
    sort_comments_by=schemas.FacebookCommentSortOption.newest_first,
    include_comment_replies=False,
)

SEEDED_FACEBOOK_COMMENTS_GATHERS: list[schemas.ApifyFacebookCommentsGatherResponse] = []


def seed_test_apify_facebook_comments_gathers(session: Session) -> None:
    """Seed the gathers."""
    SEEDED_FACEBOOK_COMMENTS_GATHERS.clear()
    apify_facebook_gathers = [
        TEST_APIFY_FACEBOOK_COMMENTS_GATHER_CREATE,
        TEST_APIFY_FACEBOOK_COMMENTS_GATHER_CREATE_2,
    ]

    for apify_facebook_gather in apify_facebook_gathers:
        SEEDED_FACEBOOK_COMMENTS_GATHERS.append(
            gather_child_crud.create_child_gather(
                session=session,
                project_id=2,
                request_schema=apify_facebook_gather,
                child_model=models.ApifyFacebookCommentsGather,
                response_schema=schemas.ApifyFacebookCommentsGatherResponse,
                child_type=gathers_schemas.ChildTypeName.apify_facebook_comments,
            )
        )

    apify_facebook_gathers = [
        TEST_APIFY_FACEBOOK_COMMENTS_GATHER_CREATE_3,
        TEST_APIFY_FACEBOOK_COMMENTS_GATHER_CREATE_4,
        TEST_APIFY_FACEBOOK_COMMENTS_GATHER_CREATE_5,
        TEST_APIFY_FACEBOOK_COMMENTS_GATHER_CREATE_6,
    ]
    for apify_facebook_gather in apify_facebook_gathers:
        SEEDED_FACEBOOK_COMMENTS_GATHERS.append(
            gather_child_crud.create_child_gather(
                session=session,
                project_id=1,
                request_schema=apify_facebook_gather,
                child_model=models.ApifyFacebookCommentsGather,
                response_schema=schemas.ApifyFacebookCommentsGatherResponse,
                child_type=gathers_schemas.ChildTypeName.apify_facebook_comments,
            )
        )
