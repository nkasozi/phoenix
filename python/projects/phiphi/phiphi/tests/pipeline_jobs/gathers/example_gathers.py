"""Example gathers (reponses/rows/specs)."""

import datetime

from phiphi.api.projects import gathers


def facebook_posts_gather_example() -> (
    gathers.apify_facebook_posts.schemas.ApifyFacebookPostsGatherResponse
):
    """Example for ApifyFacebookPostsGatherResponse schema."""
    return gathers.apify_facebook_posts.schemas.ApifyFacebookPostsGatherResponse(
        name="Example",
        limit_posts_per_account=4,
        account_url_list=[
            "https://www.facebook.com/howtobuildup/",
            "https://www.facebook.com/unitednations/",
        ],
        posts_created_after="2024-01-03",
        posts_created_before="2024-04-04",
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=1,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_facebook_posts,
    )


def facebook_search_posts_gather_example() -> (
    gathers.apify_facebook_search_posts.schemas.ApifyFacebookSearchPostsGatherResponse
):
    """Example for ApifyFacebookSearchPostsGatherResponse schema."""
    return gathers.apify_facebook_search_posts.schemas.ApifyFacebookSearchPostsGatherResponse(
        name="Example",
        search_query="hello world",
        limit_posts=3,
        limit_retries=2,
        id=7,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=1,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_facebook_search_posts,
    )


def facebook_comments_gather_example() -> (
    gathers.apify_facebook_comments.schemas.ApifyFacebookCommentsGatherResponse
):
    """Example for ApifyFacebookCommentsGatherResponse schema."""
    return gathers.apify_facebook_comments.schemas.ApifyFacebookCommentsGatherResponse(
        name="Example",
        limit_comments_per_post=4,
        post_url_list=[
            "https://www.facebook.com/unitednations/posts/pfbid045as8QKV2uLVYe2NumDPs7a68Hr4P5cjmoyMRo2e4dj4p3rp2gWNNj948Uu7BVcxl",
            "https://www.facebook.com/unitednations/posts/pfbid0LmBjLodaYjFhvntY3rX4xB2cyrcUeXHuasXJNFgimkNX7NE76CjSEYCwwveF9v5ml",
        ],
        sort_comments_by=gathers.apify_facebook_comments.schemas.FacebookCommentSortOption.facebook_default,
        include_comment_replies=False,
        id=2,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=1,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_facebook_comments,
    )


def tiktok_accounts_posts_gather_example() -> (
    gathers.apify_tiktok_accounts_posts.schemas.ApifyTikTokAccountsPostsGatherResponse
):
    """Example for ApifyTiktokAccountsPostsGatherResponse schema."""
    return gathers.apify_tiktok_accounts_posts.schemas.ApifyTikTokAccountsPostsGatherResponse(
        name="Example",
        account_username_list=["@unitednations", "@bbcnews"],
        limit_posts_per_account=3,
        id=3,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=1,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_tiktok_accounts_posts,
    )


def tiktok_hashtags_posts_gather_example() -> (
    gathers.apify_tiktok_hashtags_posts.schemas.ApifyTikTokHashtagsPostsGatherResponse
):
    """Example for ApifyTiktokHashtagsGatherPostsResponse schema."""
    return gathers.apify_tiktok_hashtags_posts.schemas.ApifyTikTokHashtagsPostsGatherResponse(
        name="Example",
        hashtag_list=["unitednations", "bbcnews"],
        limit_posts_per_hashtag=3,
        id=4,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=1,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_tiktok_hashtags_posts,
    )


def tiktok_searches_posts_gather_example() -> (
    gathers.apify_tiktok_searches_posts.schemas.ApifyTikTokSearchesPostsGatherResponse
):
    """Example for ApifyTiktokSearchesGatherPostsResponse schema."""
    return gathers.apify_tiktok_searches_posts.schemas.ApifyTikTokSearchesPostsGatherResponse(
        name="Example",
        search_list=["hello world", "peace"],
        limit_posts_per_search=3,
        id=6,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=1,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_tiktok_searches_posts,
    )


def tiktok_comments_gather_example() -> (
    gathers.apify_tiktok_comments.schemas.ApifyTikTokCommentsGatherResponse
):
    """Example for ApifyTiktokCommentsGatherResponse schema."""
    return gathers.apify_tiktok_comments.schemas.ApifyTikTokCommentsGatherResponse(
        name="Example",
        post_url_list=[
            # These are real URLs but from public organisations
            "https://www.tiktok.com/@unitednations/video/7412700631284141355",
            "https://www.tiktok.com/@bbc/video/7413716097670630689",
        ],
        limit_total_comments=3,
        include_comment_replies=True,
        id=5,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=1,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_tiktok_comments,
    )


def x_advanced_searches_posts_comments_gather_example() -> (
    gathers.apify_x_advanced_searches_posts_comments.schemas.ApifyXAdvancedSearchesPostsCommentsGatherResponse
):
    """Example for ApifyXAdvancedSearchesPostsCommentsGatherResponse schema."""
    return gathers.apify_x_advanced_searches_posts_comments.schemas.ApifyXAdvancedSearchesPostsCommentsGatherResponse(  # noqa: E501
        name="Example",
        search_list=[
            "from:nasa",
            "global warming",
        ],
        limit_results_per_search=5,
        posts_created_after="2025-01-01T00:00:00Z",
        posts_created_before="2025-02-01T00:00:00Z",
        sort="Latest",
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=1,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_x_advanced_searches_posts_comments,
    )


def x_simple_searches_posts_comments_gather_example() -> (
    gathers.apify_x_simple_searches_posts_comments.schemas.ApifyXSimpleSearchesPostsCommentsGatherResponse
):
    """Example for ApifyXSimpleSearchesPostsCommentsGatherResponse schema."""
    return gathers.apify_x_simple_searches_posts_comments.schemas.ApifyXSimpleSearchesPostsCommentsGatherResponse(  # noqa: E501
        name="Example",
        handle_list=["nasa", "spacex"],
        keywords_list=["mars exploration", "exploration"],
        limit_results_per_search=20,
        posts_created_after="2024-01-01T00:00:00Z",
        posts_created_before="2025-02-01T00:00:00Z",
        # Location often means there is no results
        location_near=None,
        sort="Latest",
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=1,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_x_simple_searches_posts_comments,
    )


def danek_facebook_searches_posts_gather_example() -> (
    gathers.danek_facebook_searches_posts.schemas.DanekFacebookSearchesPostsGatherResponse
):
    """Example for DanekFacebookSearchesPostsGatherResponse schema."""
    return gathers.danek_facebook_searches_posts.schemas.DanekFacebookSearchesPostsGatherResponse(
        name="Example",
        id=8,
        project_id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.danek_facebook_searches_posts,
        search_list=[
            "tech innovation",
            "tech news",
        ],
        stop_scraping_per_search_after_count=20,
        posts_created_after="2024-01-01T00:00:00Z",
        posts_created_before="2024-01-02T23:00:00Z",
        recent_posts=False,
    )


def danek_instagram_posts_gather_example() -> (
    gathers.danek_instagram_posts.schemas.DanekInstagramPostsGatherResponse
):
    """Example for DanekFacebookSearchesPostsGatherResponse schema."""
    return gathers.danek_instagram_posts.schemas.DanekInstagramPostsGatherResponse(
        name="Example",
        id=9,
        project_id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.danek_instagram_posts,
        account_username_list=[
            "howtobuildup",
            "unitednations",
        ],
        limit_posts_per_account=20,
        posts_created_after="2025-01-01T00:00:00Z",
        scrape_comments_count_per_post=0,
        limit_child_comments_per_comment=0,
    )


def danek_instagram_posts_with_comments_gather_example() -> (
    gathers.danek_instagram_posts.schemas.DanekInstagramPostsGatherResponse
):
    """Example for DanekFacebookSearchesPostsGatherResponse schema."""
    return gathers.danek_instagram_posts.schemas.DanekInstagramPostsGatherResponse(
        name="Example",
        id=9,
        project_id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.danek_instagram_posts,
        account_username_list=[
            "howtobuildup",
            "unitednations",
        ],
        limit_posts_per_account=20,
        posts_created_after="2025-01-01T00:00:00Z",
        scrape_comments_count_per_post=20,
        limit_child_comments_per_comment=0,
    )


def danek_instagram_comments_gather_example() -> (
    gathers.danek_instagram_comments.schemas.DanekInstagramCommentsGatherResponse
):
    """Example for DanekInstagramCommentsGatherResponse schema.

    Contains real post_ids in the post_id_list so that the integration tests are usable.
    """
    return gathers.danek_instagram_comments.schemas.DanekInstagramCommentsGatherResponse(
        name="Example",
        id=10,
        project_id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.danek_instagram_comments,
        post_id_list=[
            "3826211346950544459",
            "3151106959012096412",
        ],
        limit_comments_per_post=20,
    )


def danek_instagram_comments_child_comments_gather_example() -> (
    gathers.danek_instagram_comments.schemas.DanekInstagramCommentsGatherResponse
):
    """Example for DanekInstagramCommentsGatherResponse schema with child comments.

    Contains real post_ids in the post_id_list so that the integration tests are usable.
    """
    return gathers.danek_instagram_comments.schemas.DanekInstagramCommentsGatherResponse(
        name="Example",
        id=11,
        project_id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.danek_instagram_comments,
        post_id_list=[
            "3826211346950544459",
            "3151106959012096412",
        ],
        limit_comments_per_post=20,
        limit_child_comments_per_comment=10,
    )
