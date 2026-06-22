"""Schemas for Apify TikTok hashtags posts gathers.

This schemas is a subset of the available inputs for the Apify TikTok Scraper.

For reference see the Apify actor docs:
https://apify.com/clockworks/tiktok-scraper/input-schema

Note on `posts_created_after` and `posts_created_since_num_days` that these fields don't work for
searches. See issue:
https://apify.com/clockworks/tiktok-scraper/issues/trying-to-set-a-time-RYR6bQdcvzc52hwnO

It is thought (but not 100% sure) that the `apify_tiktok_hashtags_posts_gather` has the same
functionality as the `apify_searches_posts_gather` but it normalises all the inputs in
`hashtag_list` to have a `#` at the begging.
"""

from typing import Any, Optional

import pydantic

from phiphi.api.projects.gathers import constants, utils
from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.job_runs import schemas as job_runs_schemas


class ApifyTikTokHashtagsPostsGatherBase(gather_schemas.GatherBase):
    """Input schema for the Apify TikTok Scraper for hashtags."""

    limit_posts_per_hashtag: int = pydantic.Field(
        serialization_alias="resultsPerPage", description="Limit results per hashtag"
    )
    # It is important that the name of the property is different from the alias other wise it will
    # not be returned from serialize_to_apify_input
    hashtag_list: list[str] = pydantic.Field(
        serialization_alias="hashtags",
        description=(
            "List of hashtags to scrape TikTok videos for. "
            " It is recommended to use without # prefix but "
            "there seems to be no difference when using with."
        ),
    )
    proxy_country_to_gather_from: Optional[str] = pydantic.Field(
        default=None,
        serialization_alias="proxyCountryCode",
        description=(
            "Country to use for the proxy to gather from. "
            "If this is set a RESIDENTIAL group will be used and will increase the price."
        ),
    )


class ApifyTikTokHashtagsPostsGatherResponse(
    gather_schemas.GatherChildResponseBase, ApifyTikTokHashtagsPostsGatherBase
):
    """Apify TikTok hashtags posts gather schema."""

    def serialize_to_apify_input(self) -> dict[str, Any]:
        """Serialize the instance to a dictionary suitable for Apify API."""
        apify_dict = super().serialize_to_apify_input()
        # We are adding searchSection to the dictionary as it is a constant for gathering posts.
        apify_dict["searchSection"] = constants.TIKTOK_POST_SEARCH_SECTION
        return apify_dict

    # Both the property and computed_field decorators are used other wise mypy thinks that the
    # property is a function
    # Mypy doesn't allow both property and computed_field decorators, hence the ignore
    @pydantic.computed_field  # type: ignore[prop-decorator]
    @property
    def job_run_resource_estimate(self) -> job_runs_schemas.JobRunResourceEstimate:
        """Calculate the resource estimate for the job run."""
        max_gather_result_count: int = len(self.hashtag_list) * self.limit_posts_per_hashtag
        return utils.calculate_job_run_resource_estimate_from_result_count(
            max_gather_result_count,
            utils.get_mean_cost_per_100k_results(
                gather_schemas.ChildTypeName.apify_tiktok_hashtags_posts
            ),
        )


class ApifyTikTokHashtagsPostsGatherCreate(
    gather_schemas.GatherCreate, ApifyTikTokHashtagsPostsGatherBase
):
    """Apify Gather create schema.

    Properties to receive via API on creation.
    """


class ApifyTikTokHashtagsPostsGatherUpdate(gather_schemas.GatherUpdate):
    """Apify Gather update schema."""

    limit_posts_per_hashtag: Optional[int] = pydantic.Field(
        serialization_alias="resultsPerPage", description="Limit results per hashtag"
    )
    # It is important that the name of the property is different from the alias other wise it will
    # not be returned from serialize_to_apify_input
    hashtag_list: Optional[list[str]] = pydantic.Field(
        serialization_alias="hashtags",
        description=(
            "List of hashtags to scrape TikTok videos for. "
            " It is recommended to use without # prefix but "
            "there seems to be no difference when using with."
        ),
    )
    proxy_country_to_gather_from: Optional[str] = pydantic.Field(
        default=None,
        serialization_alias="proxyCountryCode",
        description=(
            "Country to use for the proxy to gather from. "
            "If this is set a RESIDENTIAL group will be used and will increase the price."
        ),
    )
