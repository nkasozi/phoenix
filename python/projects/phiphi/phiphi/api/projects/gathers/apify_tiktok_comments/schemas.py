"""Schemas for Apify TikTok comments.

After testing we decided to use `apidojo` instead of `clockworks` for scraping TikTok comments.
This is mainly due to the price difference.

For reference see the Apify actor docs:
https://apify.com/apidojo/tiktok-comments-scraper/input-schema
"""

from typing import Optional

import pydantic

from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.gathers import utils
from phiphi.api.projects.job_runs import schemas as job_runs_schemas
from phiphi.pydantic_types import UrlStr


class ApifyTikTokCommentsGatherBase(gather_schemas.GatherBase):
    """Input schema for the Apify TikTok Scraper for comments."""

    post_url_list: list[UrlStr] = pydantic.Field(
        serialization_alias="startUrls",
        description="List of TikTok post (video) URLs to scrape comments from",
    )
    limit_total_comments: int = pydantic.Field(
        serialization_alias="maxItems",
        description="Limit total number of comments (including replies)",
    )
    include_comment_replies: bool = pydantic.Field(
        default=False,
        serialization_alias="includeReplies",
        description="If True, includes replies to comments. Default is False.",
    )


class ApifyTikTokCommentsGatherResponse(
    gather_schemas.GatherChildResponseBase, ApifyTikTokCommentsGatherBase
):
    """Apify TikTok searches posts gather schema."""

    # Both the property and computed_field decorators are used other wise mypy thinks that the
    # property is a function
    # Mypy doesn't allow both property and computed_field decorators, hence the ignore
    @pydantic.computed_field  # type: ignore[prop-decorator]
    @property
    def job_run_resource_estimate(self) -> job_runs_schemas.JobRunResourceEstimate:
        """Calculate the resource estimate for the job run."""
        max_gather_result_count: int = self.limit_total_comments
        return utils.calculate_job_run_resource_estimate_from_result_count(
            max_gather_result_count,
            utils.get_mean_cost_per_100k_results(
                gather_schemas.ChildTypeName.apify_tiktok_comments
            ),
        )


class ApifyTikTokCommentsGatherCreate(ApifyTikTokCommentsGatherBase, gather_schemas.GatherCreate):
    """Apify TikTok Comments Gather create schema.

    Properties to receive via API on creation.
    """


class ApifyTikTokCommentsGatherUpdate(gather_schemas.GatherUpdate):
    """Apify TikTok Comments Gather update schema.

    Only properties that are set will be updated.
    """

    limit_total_comments: Optional[int] = pydantic.Field(
        default=None,
        description="Limit total number of comments (including replies)",
    )
    post_url_list: Optional[list[UrlStr]] = pydantic.Field(
        default=None,
        description="List of TikTok post (video) URLs to scrape comments from",
    )
    include_comment_replies: Optional[bool] = pydantic.Field(
        default=None,
        description="If True, includes replies to comments.",
    )
