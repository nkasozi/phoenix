"""Schemas for Apify TikTok accounts posts gathers.

This schemas is a subset of the available inputs for the Apify TikTok Scraper.

For reference see the Apify actor docs:
https://apify.com/clockworks/tiktok-scraper/input-schema
"""

from typing import Any, Optional

import pydantic

from phiphi.api.projects.gathers import constants, utils
from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.job_runs import schemas as job_runs_schemas


class ApifyTikTokAccountsPostsGatherBase(gather_schemas.GatherBase):
    """Input schema for the Apify TikTok Scraper for accounts."""

    limit_posts_per_account: int = pydantic.Field(
        serialization_alias="resultsPerPage", description="Limit results per account"
    )
    account_username_list: list[str] = pydantic.Field(
        serialization_alias="profiles",
        description="List of TikTok account usernames.",
    )
    posts_created_after: Optional[str] = pydantic.Field(
        default=None,
        serialization_alias="oldestPostDate",
        description="Fetch posts created after this date (YYYY-MM-DD)",
    )
    posts_created_since_num_days: Optional[int] = pydantic.Field(
        default=None,
        serialization_alias="scrapeLastNDays",
        description=(
            "Specify how old the scraped videos should be (in days). "
            "Putting 1 will get you only today's posts, 2 - yesterday's and today's, and so on. "
            "If the posts_created_after field was set, "
            "the most recent videos will be scraped. "
            "See docs of field for more information: "
            "https://apify.com/clockworks/tiktok-scraper/input-schema#scrapeLastNDays"
        ),
    )
    proxy_country_to_gather_from: Optional[str] = pydantic.Field(
        default=None,
        serialization_alias="proxyCountryCode",
        description=(
            "Country to use for the proxy to gather from. "
            "If this is set a RESIDENTIAL group will be used and will increase the price. "
        ),
    )

    _validate_both_filters_by_date_not_set = pydantic.field_validator(
        "posts_created_since_num_days"
    )(utils.validate_both_not_set("posts_created_after"))


class ApifyTikTokAccountsPostsGatherResponse(
    gather_schemas.GatherChildResponseBase, ApifyTikTokAccountsPostsGatherBase
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
        max_gather_result_count: int = (
            len(self.account_username_list) * self.limit_posts_per_account
        )
        return utils.calculate_job_run_resource_estimate_from_result_count(
            max_gather_result_count,
            utils.get_mean_cost_per_100k_results(
                gather_schemas.ChildTypeName.apify_tiktok_accounts_posts
            ),
        )


class ApifyTikTokAccountsPostsGatherCreate(
    gather_schemas.GatherCreate, ApifyTikTokAccountsPostsGatherBase
):
    """Apify Gather create schema.

    Properties to receive via API on creation.
    """


class ApifyTikTokAccountsPostsGatherUpdate(gather_schemas.GatherUpdate):
    """Apify Gather update schema."""

    limit_posts_per_account: Optional[int] = pydantic.Field(
        default=None, description="Limit results per account"
    )
    account_username_list: Optional[list[str]] = pydantic.Field(
        default=None, description="List of TikTok account usernames."
    )
    posts_created_after: Optional[str] = pydantic.Field(
        default=None, description="Fetch posts created after this date (YYYY-MM-DD)"
    )
    posts_created_since_num_days: Optional[int] = pydantic.Field(
        default=None,
        description=(
            "Specify how old the scraped videos should be (in days). "
            "Putting 1 will get you only today's posts, 2 - yesterday's and today's, and so on. "
            "If the posts_created_after field was set, "
            "the most recent videos will be scraped. "
            "See docs of field for more information: "
            "https://apify.com/clockworks/tiktok-scraper/input-schema#scrapeLastNDays"
        ),
    )
    proxy_country_to_gather_from: Optional[str] = pydantic.Field(
        default=None,
        description=(
            "Country to use for the proxy to gather from. "
            "If this is set a RESIDENTIAL group will be used and will increase the price. "
        ),
    )

    _validate_both_filters_by_date_not_set = pydantic.field_validator(
        "posts_created_since_num_days"
    )(utils.validate_both_not_set("posts_created_after"))
