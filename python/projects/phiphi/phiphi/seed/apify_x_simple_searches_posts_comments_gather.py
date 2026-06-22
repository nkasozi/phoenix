"""Seed the Apify X Simple Searches (posts+comments) gathers.

This mirrors the style of the Advanced Searches seed and keeps things small and maintainable.
"""

from sqlalchemy.orm import Session

from phiphi.api.projects.gathers import child_crud as gather_child_crud
from phiphi.api.projects.gathers import schemas as gathers_schemas
from phiphi.api.projects.gathers.apify_x_simple_searches_posts_comments import models, schemas

# Minimal but representative seed payloads. Keep these simple to ease maintenance.
TEST_APIFY_X_SIMPLE_SEARCHES_POSTS_COMMENTS_GATHER_CREATE = (
    schemas.ApifyXSimpleSearchesPostsCommentsGatherCreate(
        name="Phoenix Apify X Simple Searches (Posts+Comments)",
        handle_list=["NASA", "SpaceX"],
        keywords_list=["mars mission", "rocket launch"],
        limit_results_per_search=500,
        posts_created_after="2024-01-01",
        posts_created_before="2024-06-30T23:59:59Z",
        sort="Latest",
        location_near="Florida",
    )
)

TEST_APIFY_X_SIMPLE_SEARCHES_POSTS_COMMENTS_GATHER_CREATE_2 = (
    schemas.ApifyXSimpleSearchesPostsCommentsGatherCreate(
        name="Phoenix Apify X Simple Searches (Posts+Comments) Project 2",
        handle_list=["OpenAI", "AnthropicAI"],
        keywords_list=["AI safety", "machine learning"],
        limit_results_per_search=250,
        posts_created_after=None,
        posts_created_before=None,
        sort="Top",
        location_near=None,
    )
)

# Keep one seed with small per-query cap to exercise resource estimation boundaries.
TEST_APIFY_X_SIMPLE_SEARCHES_POSTS_COMMENTS_GATHER_CREATE_3 = (
    schemas.ApifyXSimpleSearchesPostsCommentsGatherCreate(
        name="Phoenix Apify X Simple Searches (Posts+Comments) Project 3",
        handle_list=["ESA"],
        keywords_list=["satellite"],
        limit_results_per_search=60,
        posts_created_after="2023-12-01",
        posts_created_before="2024-01-15",
        sort=None,  # Will default to 'Latest' in serialization
        location_near="Europe",
    )
)

TEST_APIFY_X_SIMPLE_SEARCHES_POSTS_COMMENTS_GATHERS: list[
    schemas.ApifyXSimpleSearchesPostsCommentsGatherResponse
] = []


def seed_test_apify_x_simple_searches_posts_comments_gathers(session: Session) -> None:
    """Seed a few Apify X simple search gathers for tests and local dev.

    Args:
        session: SQLAlchemy session used for persistence.
    """
    TEST_APIFY_X_SIMPLE_SEARCHES_POSTS_COMMENTS_GATHERS.clear()

    # Group 1: single project with one gather
    to_create = [TEST_APIFY_X_SIMPLE_SEARCHES_POSTS_COMMENTS_GATHER_CREATE]
    for payload in to_create:
        gather = gather_child_crud.create_child_gather(
            session=session,
            project_id=2,
            request_schema=payload,
            child_model=models.ApifyXSimpleSearchesPostsCommentsGather,
            response_schema=schemas.ApifyXSimpleSearchesPostsCommentsGatherResponse,
            child_type=gathers_schemas.ChildTypeName.apify_x_simple_searches_posts_comments,
        )
        TEST_APIFY_X_SIMPLE_SEARCHES_POSTS_COMMENTS_GATHERS.append(gather)

    # Group 2: spread across a couple of projects to mirror varied states.
    TEST_APIFY_X_SIMPLE_SEARCHES_POSTS_COMMENTS_GATHERS.append(
        gather_child_crud.create_child_gather(
            session=session,
            project_id=3,
            request_schema=TEST_APIFY_X_SIMPLE_SEARCHES_POSTS_COMMENTS_GATHER_CREATE_2,
            child_model=models.ApifyXSimpleSearchesPostsCommentsGather,
            response_schema=schemas.ApifyXSimpleSearchesPostsCommentsGatherResponse,
            child_type=gathers_schemas.ChildTypeName.apify_x_simple_searches_posts_comments,
        )
    )

    TEST_APIFY_X_SIMPLE_SEARCHES_POSTS_COMMENTS_GATHERS.append(
        gather_child_crud.create_child_gather(
            session=session,
            project_id=5,
            request_schema=TEST_APIFY_X_SIMPLE_SEARCHES_POSTS_COMMENTS_GATHER_CREATE_3,
            child_model=models.ApifyXSimpleSearchesPostsCommentsGather,
            response_schema=schemas.ApifyXSimpleSearchesPostsCommentsGatherResponse,
            child_type=gathers_schemas.ChildTypeName.apify_x_simple_searches_posts_comments,
        )
    )
