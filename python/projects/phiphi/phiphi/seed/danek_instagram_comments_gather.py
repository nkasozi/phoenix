"""Seed for Danek Instagram Comments Gathers."""

from sqlalchemy.orm import Session

from phiphi.api.projects import gathers

TEST_DANEK_INSTAGRAM_COMMENTS_GATHER_CREATE = (
    gathers.danek_instagram_comments.schemas.DanekInstagramCommentsGatherCreate(
        name="Phoenix Danek Instagram Comments Gather",
        post_id_list=["1", "2", "3"],
        limit_comments_per_post=50,
    )
)

TEST_DANEK_INSTAGRAM_COMMENTS_GATHER: list[
    gathers.danek_instagram_comments.schemas.DanekInstagramCommentsGatherResponse
] = []


def seed_test_danek_instagram_comments_gathers(session: Session) -> None:
    """Seed the gathers."""
    TEST_DANEK_INSTAGRAM_COMMENTS_GATHER.clear()
    danek_instagram_comments_gathers = [
        TEST_DANEK_INSTAGRAM_COMMENTS_GATHER_CREATE,
    ]

    for danek_instagram_comments_gather in danek_instagram_comments_gathers:
        gather_response = gathers.child_crud.create_child_gather(
            session=session,
            project_id=2,
            request_schema=danek_instagram_comments_gather,
            child_model=gathers.danek_instagram_comments.models.DanekInstagramCommentsGather,
            response_schema=gathers.danek_instagram_comments.schemas.DanekInstagramCommentsGatherResponse,
            child_type=gathers.schemas.ChildTypeName.danek_instagram_comments,
        )
        TEST_DANEK_INSTAGRAM_COMMENTS_GATHER.append(gather_response)
