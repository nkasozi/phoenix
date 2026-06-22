"""Schemas for apify facebook post gathers."""

from functools import partial
from typing import Annotated, Any, Dict, List, Optional

import pydantic
from annotated_types import Len

from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.gathers import utils
from phiphi.api.projects.gathers.apify_facebook_posts import job_run_resource_estimate
from phiphi.api.projects.job_runs import schemas as job_runs_schemas
from phiphi.pydantic_types import UrlStr

MAX_DAYS_BETWEEN_DATES = 365


def validate_date_range(
    posts_created_after: Optional[str], posts_created_before: Optional[str]
) -> None:
    """Validate that range between posts_created_after and posts_created_before.

    The range must be less than MAX_DAYS_BETWEEN_DATES days. The decision to limit this was made
    to limit the risks on costs of very large gathers.
    """
    if posts_created_after is None or posts_created_before is None:
        return

    before = utils.parse_datetime_string(posts_created_before)
    after = utils.parse_datetime_string(posts_created_after)

    if before <= after:
        raise ValueError("posts_created_before must be after posts_created_after")

    days_between = (before - after).days

    if days_between > MAX_DAYS_BETWEEN_DATES:
        raise ValueError(
            f"Date range must be less than {MAX_DAYS_BETWEEN_DATES} days, got {days_between}"
        )


ValidatedDate = Annotated[
    Optional[str],
    pydantic.AfterValidator(partial(utils.validate_and_normalise_datetime, utc_as_z=True)),
]
VALIDATED_DATE_DESCRIPTION = (
    "A Datetime in any format support by libary dateutil."
    " Will be converted to ISO 8601 and UTC timezone."
    "If only date is given it will be converted to 00:00:00 UTC."
)

POSTS_CREATED_AFTER_DESCRIPTION = (
    f"Fetch posts created after this date. {VALIDATED_DATE_DESCRIPTION}"
)
POSTS_CREATED_BEFORE_DESCRIPTION = (
    f"Fetch posts created before this date. {VALIDATED_DATE_DESCRIPTION}"
)


# Adding max number of account urls to limit the risk of large costs on Apify
MAX_ACCOUNT_URLS = 200
AccountUrlList = Annotated[
    List[UrlStr],
    Len(max_length=MAX_ACCOUNT_URLS),
    pydantic.Field(
        serialization_alias="startUrls",
        description="List of Facebook page/profile URLs to scrape from",
    ),
]
OptionalAccountUrlList = Annotated[
    Optional[List[UrlStr]],
    Len(max_length=MAX_ACCOUNT_URLS),
    pydantic.Field(
        serialization_alias="startUrls",
        description="List of Facebook page/profile URLs to scrape from",
        default=None,
    ),
]


class ApifyFacebookPostsGatherBase(gather_schemas.GatherBase):
    """Input schema for the Apify Facebook posts scraper.

    Ref to relevant Apify actor docs: https://apify.com/apify/facebook-posts-scraper/input-schema
    """

    limit_posts_per_account: int = pydantic.Field(
        serialization_alias="resultsLimit", description="Limit results per account"
    )
    account_url_list: AccountUrlList
    posts_created_after: ValidatedDate = pydantic.Field(
        default=None,
        serialization_alias="onlyPostsNewerThan",
        description=POSTS_CREATED_AFTER_DESCRIPTION,
    )
    posts_created_before: ValidatedDate = pydantic.Field(
        default=None,
        serialization_alias="onlyPostsOlderThan",
        description=POSTS_CREATED_BEFORE_DESCRIPTION,
    )

    @pydantic.model_validator(mode="after")
    def validate_dates_order(self) -> "ApifyFacebookPostsGatherBase":
        """Validate that posts_created_before is after posts_created_after."""
        validate_date_range(self.posts_created_after, self.posts_created_before)
        return self


class ApifyFacebookPostsGatherResponse(
    gather_schemas.GatherChildResponseBase, ApifyFacebookPostsGatherBase
):
    """Apify Gather schema.

    Properties to return to client.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    def serialize_to_apify_input(self) -> Dict[str, Any]:
        """Serialize the instance to a dictionary suitable for Apify API."""
        apify_dict = super().serialize_to_apify_input()
        if "startUrls" in apify_dict:
            apify_dict["startUrls"] = self.serialize_account_urls(apify_dict["startUrls"])
        return apify_dict

    @staticmethod
    def serialize_account_urls(urls: List[str]) -> List[Dict[str, str]]:
        """Convert a list of plain URLs to the list of dicts required for Apify."""
        return [{"url": str(url)} for url in urls]

    # Both the property and computed_field decorators are used other wise mypy thinks that the
    # property is a function
    # Mypy doesn't allow both property and computed_field decorators, hence the ignore
    @pydantic.computed_field  # type: ignore[prop-decorator]
    @property
    def job_run_resource_estimate(self) -> job_runs_schemas.JobRunResourceEstimate:
        """Calculate the resource estimate for the job run."""
        max_gather_result_count = job_run_resource_estimate.compute_max_gather_result_count(
            self.account_url_list,
            self.limit_posts_per_account,
            self.posts_created_after,
            self.posts_created_before,
        )
        return utils.calculate_job_run_resource_estimate_from_result_count(
            max_gather_result_count,
            utils.get_mean_cost_per_100k_results(
                gather_schemas.ChildTypeName.apify_facebook_posts
            ),
        )


class ApifyFacebookPostsGatherCreate(gather_schemas.GatherCreate, ApifyFacebookPostsGatherBase):
    """Apify Gather create schema.

    Properties to receive via API on creation.
    """


class ApifyFacebookPostsGatherUpdate(gather_schemas.GatherUpdate):
    """Apify Gather update schema."""

    limit_posts_per_account: Optional[int] = pydantic.Field(
        default=None, description="Limit results per account"
    )
    account_url_list: OptionalAccountUrlList
    posts_created_after: ValidatedDate = pydantic.Field(
        default=None, description=POSTS_CREATED_AFTER_DESCRIPTION
    )
    posts_created_before: ValidatedDate = pydantic.Field(
        default=None, description=POSTS_CREATED_BEFORE_DESCRIPTION
    )

    @pydantic.model_validator(mode="after")
    def validate_dates_order(self) -> "ApifyFacebookPostsGatherUpdate":
        """Validate that posts_created_before is after posts_created_after."""
        validate_date_range(self.posts_created_after, self.posts_created_before)
        return self
