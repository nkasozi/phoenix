"""Child types."""

import dataclasses
from typing import Type, Union

from phiphi.api.projects.gathers import manual_upload
from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.gathers.apify_facebook_comments import (
    schemas as facebook_comment_schema,
)
from phiphi.api.projects.gathers.apify_facebook_posts import (
    schemas as facebook_post_schema,
)
from phiphi.api.projects.gathers.apify_facebook_search_posts import (
    schemas as facebook_search_posts_schema,
)
from phiphi.api.projects.gathers.apify_tiktok_accounts_posts import (
    schemas as tiktok_accounts_posts_schema,
)
from phiphi.api.projects.gathers.apify_tiktok_comments import (
    schemas as tiktok_comments_schema,
)
from phiphi.api.projects.gathers.apify_tiktok_hashtags_posts import (
    schemas as tiktok_hashtags_posts_schema,
)
from phiphi.api.projects.gathers.apify_tiktok_searches_posts import (
    schemas as tiktok_searches_posts_schema,
)
from phiphi.api.projects.gathers.apify_x_advanced_searches_posts_comments import (
    schemas as apify_x_advanced_searches_posts_comments_schema,
)
from phiphi.api.projects.gathers.apify_x_simple_searches_posts_comments import (
    schemas as apify_x_simple_searches_posts_comments_schema,
)
from phiphi.api.projects.gathers.danek_facebook_searches_posts import (
    schemas as danek_facebook_searches_posts_schema,
)
from phiphi.api.projects.gathers.danek_instagram_comments import (
    schemas as danek_instagram_comments_schema,
)
from phiphi.api.projects.gathers.danek_instagram_posts import (
    schemas as danek_instagram_posts_schema,
)

##############################
# Child Types
#
# IMPORTANT:
# Add AllChildTypesUnion and CHILD_TYPES_MAP.
##############################
AllChildTypesUnion = Union[
    danek_instagram_comments_schema.DanekInstagramCommentsGatherResponse,
    danek_instagram_posts_schema.DanekInstagramPostsGatherResponse,
    danek_facebook_searches_posts_schema.DanekFacebookSearchesPostsGatherResponse,
    facebook_comment_schema.ApifyFacebookCommentsGatherResponse,
    facebook_post_schema.ApifyFacebookPostsGatherResponse,
    facebook_search_posts_schema.ApifyFacebookSearchPostsGatherResponse,
    tiktok_hashtags_posts_schema.ApifyTikTokHashtagsPostsGatherResponse,
    tiktok_accounts_posts_schema.ApifyTikTokAccountsPostsGatherResponse,
    tiktok_searches_posts_schema.ApifyTikTokSearchesPostsGatherResponse,
    tiktok_comments_schema.ApifyTikTokCommentsGatherResponse,
    apify_x_advanced_searches_posts_comments_schema.ApifyXAdvancedSearchesPostsCommentsGatherResponse,
    apify_x_simple_searches_posts_comments_schema.ApifyXSimpleSearchesPostsCommentsGatherResponse,
    manual_upload.schemas.ManualUploadGatherResponse,
]

CHILD_TYPES_MAP: dict[gather_schemas.ChildTypeName, Type[AllChildTypesUnion]] = {
    gather_schemas.ChildTypeName.apify_facebook_comments: (
        facebook_comment_schema.ApifyFacebookCommentsGatherResponse
    ),
    gather_schemas.ChildTypeName.apify_facebook_posts: (
        facebook_post_schema.ApifyFacebookPostsGatherResponse
    ),
    gather_schemas.ChildTypeName.apify_facebook_search_posts: (
        facebook_search_posts_schema.ApifyFacebookSearchPostsGatherResponse
    ),
    gather_schemas.ChildTypeName.apify_tiktok_hashtags_posts: (
        tiktok_hashtags_posts_schema.ApifyTikTokHashtagsPostsGatherResponse
    ),
    gather_schemas.ChildTypeName.apify_tiktok_accounts_posts: (
        tiktok_accounts_posts_schema.ApifyTikTokAccountsPostsGatherResponse
    ),
    gather_schemas.ChildTypeName.apify_tiktok_searches_posts: (
        tiktok_searches_posts_schema.ApifyTikTokSearchesPostsGatherResponse
    ),
    gather_schemas.ChildTypeName.apify_tiktok_comments: (
        tiktok_comments_schema.ApifyTikTokCommentsGatherResponse
    ),
    gather_schemas.ChildTypeName.apify_x_advanced_searches_posts_comments: (
        apify_x_advanced_searches_posts_comments_schema.ApifyXAdvancedSearchesPostsCommentsGatherResponse
    ),
    gather_schemas.ChildTypeName.apify_x_simple_searches_posts_comments: (
        apify_x_simple_searches_posts_comments_schema.ApifyXSimpleSearchesPostsCommentsGatherResponse
    ),
    gather_schemas.ChildTypeName.danek_facebook_searches_posts: (
        danek_facebook_searches_posts_schema.DanekFacebookSearchesPostsGatherResponse
    ),
    gather_schemas.ChildTypeName.danek_instagram_comments: (
        danek_instagram_comments_schema.DanekInstagramCommentsGatherResponse
    ),
    gather_schemas.ChildTypeName.danek_instagram_posts: (
        danek_instagram_posts_schema.DanekInstagramPostsGatherResponse
    ),
    gather_schemas.ChildTypeName.manual_upload: (manual_upload.schemas.ManualUploadGatherResponse),
}


@dataclasses.dataclass
class GatherProjectDBDefaults:
    """Gather project db defaults for a child gather."""

    platform: gather_schemas.Platform
    data_type: gather_schemas.DataType


CHILD_TYPES_MAP_PROJECT_DB_DEFAULTS: dict[
    gather_schemas.ChildTypeName, GatherProjectDBDefaults
] = {
    gather_schemas.ChildTypeName.apify_facebook_comments: GatherProjectDBDefaults(
        platform=gather_schemas.Platform.facebook,
        data_type=gather_schemas.DataType.comments,
    ),
    gather_schemas.ChildTypeName.apify_facebook_posts: GatherProjectDBDefaults(
        platform=gather_schemas.Platform.facebook,
        data_type=gather_schemas.DataType.posts,
    ),
    gather_schemas.ChildTypeName.apify_facebook_search_posts: GatherProjectDBDefaults(
        platform=gather_schemas.Platform.facebook,
        data_type=gather_schemas.DataType.posts,
    ),
    gather_schemas.ChildTypeName.apify_tiktok_hashtags_posts: GatherProjectDBDefaults(
        platform=gather_schemas.Platform.tiktok,
        data_type=gather_schemas.DataType.posts,
    ),
    gather_schemas.ChildTypeName.apify_tiktok_accounts_posts: GatherProjectDBDefaults(
        platform=gather_schemas.Platform.tiktok,
        data_type=gather_schemas.DataType.posts,
    ),
    gather_schemas.ChildTypeName.apify_tiktok_searches_posts: GatherProjectDBDefaults(
        platform=gather_schemas.Platform.tiktok,
        data_type=gather_schemas.DataType.posts,
    ),
    gather_schemas.ChildTypeName.apify_tiktok_comments: GatherProjectDBDefaults(
        platform=gather_schemas.Platform.tiktok,
        data_type=gather_schemas.DataType.comments,
    ),
    gather_schemas.ChildTypeName.danek_facebook_searches_posts: GatherProjectDBDefaults(
        platform=gather_schemas.Platform.facebook,
        data_type=gather_schemas.DataType.posts,
    ),
    gather_schemas.ChildTypeName.danek_instagram_posts: GatherProjectDBDefaults(
        platform=gather_schemas.Platform.instagram,
        data_type=gather_schemas.DataType.posts,
    ),
    gather_schemas.ChildTypeName.danek_instagram_comments: GatherProjectDBDefaults(
        platform=gather_schemas.Platform.instagram,
        data_type=gather_schemas.DataType.comments,
    ),
}


def get_response_type(
    child_type_name: gather_schemas.ChildTypeName,
) -> Type[AllChildTypesUnion]:
    """Get response type.

    Args:
        child_type_name (gather_schemas.ChildTypeName): Gather child type

    Returns:
        response_schema_type: Response schema type for the child type.
    """
    if child_type_name not in CHILD_TYPES_MAP:
        raise ValueError(
            f"Gather child_type: {child_type_name} has not been added to CHILD_TYPES_MAP."
            " This should be done."
        )
    return CHILD_TYPES_MAP[child_type_name]


def get_gather_project_db_defaults(
    child_type_name: gather_schemas.ChildTypeName,
) -> GatherProjectDBDefaults:
    """Get gather project db defaults for a child gather.

    Args:
        child_type_name (gather_schemas.ChildTypeName): Gather child type

    Returns:
        GatherProjectDBDefaults: Create defaults for the child type.
    """
    if child_type_name not in CHILD_TYPES_MAP_PROJECT_DB_DEFAULTS:
        raise ValueError(
            f"Gather child_type: {child_type_name} has not been added to "
            "CHILD_TYPES_MAP_PROJECT_DB_DEFAULTS. "
            "This should be done."
        )
    return CHILD_TYPES_MAP_PROJECT_DB_DEFAULTS[child_type_name]
