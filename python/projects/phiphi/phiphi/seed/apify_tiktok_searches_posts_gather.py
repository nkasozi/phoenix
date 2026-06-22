"""Seed the apify tiktok searches post gathers."""

from sqlalchemy.orm import Session

from phiphi.api.projects.gathers import child_crud as gather_child_crud
from phiphi.api.projects.gathers import schemas as gathers_schemas
from phiphi.api.projects.gathers.apify_tiktok_searches_posts import models, schemas

TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHER_CREATE = schemas.ApifyTikTokSearchesPostsGatherCreate(
    name="Phoenix Apify TikTok Searches Posts Gather",
    search_list=["search1", "search2"],
    limit_posts_per_search=1000,
    proxy_country_to_gather_from="US",
)

TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHER_CREATE_2 = schemas.ApifyTikTokSearchesPostsGatherCreate(
    name="Phoenix Apify TikTok Searches Posts Gather project 3",
    search_list=["search1", "search2"],
    limit_posts_per_search=1000,
    proxy_country_to_gather_from="US",
)

TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHER_CREATE_3 = schemas.ApifyTikTokSearchesPostsGatherCreate(
    name="Completed Apify TikTok Searches Posts Gather project 6",
    search_list=["search1", "search2"],
    limit_posts_per_search=1000,
    proxy_country_to_gather_from="US",
)

TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHER_CREATE_4 = schemas.ApifyTikTokSearchesPostsGatherCreate(
    name="Running Apify TikTok Searches Posts Gather project 6",
    search_list=["search1", "search2"],
    limit_posts_per_search=1000,
    proxy_country_to_gather_from="US",
)

TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHER_CREATE_5 = schemas.ApifyTikTokSearchesPostsGatherCreate(
    name="To Run Apify TikTok Searches Posts Gather project 6",
    # Important that we can make the job_run_resource_estimate > 60
    # That way we can test more cases of the cost_guard for the gather job run
    search_list=["search1"],
    limit_posts_per_search=53,
    proxy_country_to_gather_from="US",
)

TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHERS: list[schemas.ApifyTikTokSearchesPostsGatherResponse] = []


def seed_test_apify_tiktok_searches_posts_gathers(session: Session) -> None:
    """Seed the gathers."""
    TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHERS.clear()
    apify_tiktok_gathers = [
        TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHER_CREATE,
    ]

    for apify_tiktok_gather in apify_tiktok_gathers:
        tiktok_gather = gather_child_crud.create_child_gather(
            session=session,
            project_id=2,
            request_schema=apify_tiktok_gather,
            child_model=models.ApifyTikTokSearchesPostsGather,
            response_schema=schemas.ApifyTikTokSearchesPostsGatherResponse,
            child_type=gathers_schemas.ChildTypeName.apify_tiktok_searches_posts,
        )
        TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHERS.append(tiktok_gather)

    TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHERS.append(
        gather_child_crud.create_child_gather(
            session=session,
            project_id=3,
            request_schema=TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHER_CREATE_2,
            child_model=models.ApifyTikTokSearchesPostsGather,
            response_schema=schemas.ApifyTikTokSearchesPostsGatherResponse,
            child_type=gathers_schemas.ChildTypeName.apify_tiktok_searches_posts,
        )
    )
    TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHERS.append(
        gather_child_crud.create_child_gather(
            session=session,
            project_id=5,
            request_schema=TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHER_CREATE_2,
            child_model=models.ApifyTikTokSearchesPostsGather,
            response_schema=schemas.ApifyTikTokSearchesPostsGatherResponse,
            child_type=gathers_schemas.ChildTypeName.apify_tiktok_searches_posts,
        )
    )

    apify_tiktok_gathers = [
        TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHER_CREATE_3,
        TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHER_CREATE_4,
        TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHER_CREATE_5,
    ]

    for apify_tiktok_gather in apify_tiktok_gathers:
        tiktok_gather = gather_child_crud.create_child_gather(
            session=session,
            project_id=6,
            request_schema=apify_tiktok_gather,
            child_model=models.ApifyTikTokSearchesPostsGather,
            response_schema=schemas.ApifyTikTokSearchesPostsGatherResponse,
            child_type=gathers_schemas.ChildTypeName.apify_tiktok_searches_posts,
        )
        TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHERS.append(tiktok_gather)
