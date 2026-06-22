"""Schemas for Apify TikTok searches posts gathers.

This schemas is a subset of the available inputs for the Apify TikTok Scraper.

For reference see the Apify actor docs:
https://apify.com/clockworks/tiktok-scraper/input-schema

Note on `posts_created_after` and `posts_created_since_num_days` that these fields don't work for
searches. See issue:
https://apify.com/clockworks/tiktok-scraper/issues/trying-to-set-a-time-RYR6bQdcvzc52hwnO
"""

from typing import Any, Optional

import pydantic

from phiphi.api.projects.gathers import constants, utils
from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.job_runs import schemas as job_runs_schemas


class ApifyTikTokSearchesPostsGatherBase(gather_schemas.GatherBase):
    """Input schema for the Apify TikTok Scraper for searches."""

    limit_posts_per_search: int = pydantic.Field(
        serialization_alias="resultsPerPage", description="Limit results per search"
    )
    # It is important that the name of the property is different from the alias other wise it will
    # not be returned from serialize_to_apify_input
    search_list: list[str] = pydantic.Field(
        serialization_alias="searchQueries",
        description=("List of searches to scrape TikTok videos for."),
    )
    proxy_country_to_gather_from: Optional[str] = pydantic.Field(
        default=None,
        serialization_alias="proxyCountryCode",
        description=(
            "Country to use for the proxy to gather from. "
            "If this is set a RESIDENTIAL group will be used and will increase the price."
        ),
    )


class ApifyTikTokSearchesPostsGatherResponse(
    gather_schemas.GatherChildResponseBase, ApifyTikTokSearchesPostsGatherBase
):
    """Apify TikTok searches posts gather schema."""

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
        max_gather_result_count: int = len(self.search_list) * self.limit_posts_per_search
        return utils.calculate_job_run_resource_estimate_from_result_count(
            max_gather_result_count,
            utils.get_mean_cost_per_100k_results(
                gather_schemas.ChildTypeName.apify_tiktok_searches_posts
            ),
        )


class ApifyTikTokSearchesPostsGatherCreate(
    gather_schemas.GatherCreate, ApifyTikTokSearchesPostsGatherBase
):
    """Apify Gather create schema.

    Properties to receive via API on creation.
    """


class ApifyTikTokSearchesPostsGatherUpdate(gather_schemas.GatherUpdate):
    """Apify Gather update schema."""

    limit_posts_per_search: Optional[int] = pydantic.Field(
        serialization_alias="resultsPerPage", description="Limit results per search", default=None
    )
    # It is important that the name of the property is different from the alias other wise it will
    # not be returned from serialize_to_apify_input
    search_list: Optional[list[str]] = pydantic.Field(
        serialization_alias="searches",
        description=(
            "List of searches to scrape TikTok videos for. "
            " It is recommended to use without # prefix but "
            "there seems to be no difference when using with."
        ),
        default=None,
    )
    proxy_country_to_gather_from: Optional[str] = pydantic.Field(
        default=None,
        serialization_alias="proxyCountryCode",
        description=(
            "Country to use for the proxy to gather from. "
            "If this is set a RESIDENTIAL group will be used and will increase the price."
        ),
    )
