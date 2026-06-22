"""Seed the Apify X Advanced Searches (posts+comments) gathers.

This mirrors the style of the TikTok seed and keeps things small and maintainable.
"""

from sqlalchemy.orm import Session

from phiphi.api.projects.gathers import child_crud as gather_child_crud
from phiphi.api.projects.gathers import schemas as gathers_schemas
from phiphi.api.projects.gathers.apify_x_advanced_searches_posts_comments import models, schemas

# Minimal but representative seed payloads. Keep these simple to ease maintenance.
TEST_APIFY_X_ADV_SEARCHES_POSTS_COMMENTS_GATHER_CREATE = (
    schemas.ApifyXAdvancedSearchesPostsCommentsGatherCreate(
        name="Phoenix Apify X Advanced Searches (Posts+Comments)",
        search_list=[
            "from:NASA mars mission",
            "to:buildup (satellite OR payload)",
        ],
        limit_results_per_search=500,
        posts_created_after="2024-01-01",
        posts_created_before="2024-06-30T23:59:59Z",
        sort="Latest",
    )
)

TEST_APIFY_X_ADV_SEARCHES_POSTS_COMMENTS_GATHER_CREATE_2 = (
    schemas.ApifyXAdvancedSearchesPostsCommentsGatherCreate(
        name="Phoenix Apify X Advanced Searches (Posts+Comments) Project 2",
        search_list=[
            '(AI OR "machine learning") langchain -is:retweet',
            "from:OpenAI (release OR announcement)",
        ],
        limit_results_per_search=250,
        posts_created_after=None,
        posts_created_before=None,
        sort="Top",
    )
)

# Keep one seed with small per-query cap to exercise resource estimation boundaries.
TEST_APIFY_X_ADV_SEARCHES_POSTS_COMMENTS_GATHER_CREATE_3 = (
    schemas.ApifyXAdvancedSearchesPostsCommentsGatherCreate(
        name="Phoenix Apify X Advanced Searches (Posts+Comments) Project 3",
        search_list=["from:ESA to:NASA collaboration"],
        limit_results_per_search=60,
        posts_created_after="2023-12-01",
        posts_created_before="2024-01-15",
        sort=None,  # Will default to 'Latest' in serialization
    )
)

TEST_APIFY_X_ADV_SEARCHES_POSTS_COMMENTS_GATHERS: list[
    schemas.ApifyXAdvancedSearchesPostsCommentsGatherResponse
] = []


def seed_test_apify_x_advanced_searches_posts_comments_gathers(session: Session) -> None:
    """Seed a few Apify X advanced search gathers for tests and local dev.

    Args:
        session: SQLAlchemy session used for persistence.
    """
    TEST_APIFY_X_ADV_SEARCHES_POSTS_COMMENTS_GATHERS.clear()

    # Group 1: single project with one gather
    to_create = [TEST_APIFY_X_ADV_SEARCHES_POSTS_COMMENTS_GATHER_CREATE]
    for payload in to_create:
        gather = gather_child_crud.create_child_gather(
            session=session,
            project_id=2,
            request_schema=payload,
            child_model=models.ApifyXAdvancedSearchesPostsCommentsGather,
            response_schema=schemas.ApifyXAdvancedSearchesPostsCommentsGatherResponse,
            child_type=gathers_schemas.ChildTypeName.apify_x_advanced_searches_posts_comments,
        )
        TEST_APIFY_X_ADV_SEARCHES_POSTS_COMMENTS_GATHERS.append(gather)

    # Group 2: spread across a couple of projects to mirror varied states.
    TEST_APIFY_X_ADV_SEARCHES_POSTS_COMMENTS_GATHERS.append(
        gather_child_crud.create_child_gather(
            session=session,
            project_id=3,
            request_schema=TEST_APIFY_X_ADV_SEARCHES_POSTS_COMMENTS_GATHER_CREATE_2,
            child_model=models.ApifyXAdvancedSearchesPostsCommentsGather,
            response_schema=schemas.ApifyXAdvancedSearchesPostsCommentsGatherResponse,
            child_type=gathers_schemas.ChildTypeName.apify_x_advanced_searches_posts_comments,
        )
    )

    TEST_APIFY_X_ADV_SEARCHES_POSTS_COMMENTS_GATHERS.append(
        gather_child_crud.create_child_gather(
            session=session,
            project_id=5,
            request_schema=TEST_APIFY_X_ADV_SEARCHES_POSTS_COMMENTS_GATHER_CREATE_3,
            child_model=models.ApifyXAdvancedSearchesPostsCommentsGather,
            response_schema=schemas.ApifyXAdvancedSearchesPostsCommentsGatherResponse,
            child_type=gathers_schemas.ChildTypeName.apify_x_advanced_searches_posts_comments,
        )
    )
