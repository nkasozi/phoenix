"""Utils for gathers."""

import json
import pathlib

from phiphi.api.projects.gathers import schemas as gather_schemas


def load_sample_raw_data(
    child_type_name: gather_schemas.ChildTypeName,
) -> list[dict]:
    """Return a sample raw data JSON blob for a given gather child type."""
    # Mapping of child type names to their relative paths
    path_mapping = {
        gather_schemas.ChildTypeName.apify_facebook_posts: (
            "apify/sample_data/facebook_posts.json"
        ),
        gather_schemas.ChildTypeName.apify_facebook_comments: (
            "apify/sample_data/facebook_comments.json"
        ),
        gather_schemas.ChildTypeName.apify_facebook_search_posts: (
            "apify/sample_data/facebook_search_posts.json"
        ),
        gather_schemas.ChildTypeName.apify_tiktok_accounts_posts: (
            "apify/sample_data/tiktok_accounts_posts.json"
        ),
        gather_schemas.ChildTypeName.apify_tiktok_hashtags_posts: (
            "apify/sample_data/tiktok_hashtags_posts.json"
        ),
        gather_schemas.ChildTypeName.apify_tiktok_searches_posts: (
            "apify/sample_data/tiktok_searches_posts.json"
        ),
        gather_schemas.ChildTypeName.apify_tiktok_comments: (
            "apify/sample_data/tiktok_comments.json"
        ),
        gather_schemas.ChildTypeName.apify_x_advanced_searches_posts_comments: (
            "apify/sample_data/x_advanced_searches_posts_comments.json"
        ),
        # Using the same sample data as advanced searches for simplicity
        gather_schemas.ChildTypeName.apify_x_simple_searches_posts_comments: (
            "apify/sample_data/x_advanced_searches_posts_comments.json"
        ),
        gather_schemas.ChildTypeName.danek_facebook_searches_posts: (
            "danek/sample_data/facebook_searches_posts.json"
        ),
        gather_schemas.ChildTypeName.danek_instagram_posts: (
            "danek/sample_data/sanitized_instagram_posts.json"
        ),
        gather_schemas.ChildTypeName.danek_instagram_comments: (
            "danek/sample_data/sanitized_instagram_comments.json"
        ),
    }

    relative_path = path_mapping.get(child_type_name)
    if relative_path is None:
        raise NotImplementedError(f"{child_type_name=} not supported.")

    base_path = pathlib.Path(__file__).parent
    full_path = base_path.joinpath(relative_path).resolve()
    with open(full_path, "r") as f:
        data: list[dict] = json.load(f)
    return data
