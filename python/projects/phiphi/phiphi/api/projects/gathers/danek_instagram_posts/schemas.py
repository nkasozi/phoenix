"""Danek instagram posts gather schema."""

from typing import Annotated, List, Optional

import pydantic
from annotated_types import Len

from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.gathers import utils
from phiphi.api.projects.job_runs import schemas as job_runs_schemas

ValidatedDate = Annotated[
    Optional[str], pydantic.AfterValidator(utils.validate_and_normalise_datetime)
]
VALIDATED_DATE_DESCRIPTION = (
    "A Datetime in any format support by library dateutil."
    " Will be converted to ISO 8601 and UTC timezone."
    "If only date is given it will be converted to 00:00:00 UTC."
)

POSTS_CREATED_AFTER_DESCRIPTION = (
    f"Fetch posts created after this date. {VALIDATED_DATE_DESCRIPTION}"
)

SCRAPE_COMMENTS_COUNT_DESCRIPTION = (
    "Add a number to scrape that number of comments under each scraped post."
    "Maximum number is 50 comments per post. Create a separate comments scraper for posts that "
    "you are interested in."
)

# Adding max number of account urls to limit the risk of large costs on Apify
MAX_ACCOUNT_URLS = 200
AccountUsernameList = Annotated[
    List[str],
    Len(max_length=MAX_ACCOUNT_URLS),
    pydantic.Field(
        serialization_alias="startUsernames",
        description="List of Instagram page/profile usernames to scrape from",
    ),
]
OptionalAccountUsernameList = Annotated[
    Optional[List[str]],
    Len(max_length=MAX_ACCOUNT_URLS),
    pydantic.Field(
        serialization_alias="startUsernames",
        description="List of Instagram page/profile usernames to scrape from",
        default=None,
    ),
]


class DanekInstagramPostsGatherBase(gather_schemas.GatherBase):
    """Input schema for the Danek Instagram Scraper for posts from accounts."""

    limit_posts_per_account: int = pydantic.Field(
        serialization_alias="resultsLimit", description="Limit results per account"
    )
    account_username_list: AccountUsernameList
    posts_created_after: ValidatedDate = pydantic.Field(
        default=None,
        description=POSTS_CREATED_AFTER_DESCRIPTION,
    )
    scrape_comments_count_per_post: int = pydantic.Field(
        default=0, description=SCRAPE_COMMENTS_COUNT_DESCRIPTION, le=200
    )
    limit_child_comments_per_comment: int = pydantic.Field(
        serialization_alias="limitChildCommentsPerPost",
        default=0,
        description="Limit child comments per comment; defaults to 0 if not set.",
    )


class DanekInstagramPostsGatherResponse(
    gather_schemas.GatherChildResponseBase, DanekInstagramPostsGatherBase
):
    """Danek Instagram posts gather schema."""

    # Both the property and computed_field decorators are used otherwise mypy thinks that the
    # property is a function
    # Mypy doesn't allow both property and computed_field decorators, hence the ignore
    @pydantic.computed_field  # type: ignore[prop-decorator]
    @property
    def job_run_resource_estimate(self) -> job_runs_schemas.JobRunResourceEstimate:
        """Calculate the resource estimate for the job run."""
        max_gather_result_count: int = (
            len(self.account_username_list) * self.limit_posts_per_account
        )
        posts_estimate: job_runs_schemas.JobRunResourceEstimate = (
            utils.calculate_job_run_resource_estimate_from_result_count(
                max_gather_result_count,
                utils.get_danek_costs_per_100k(gather_schemas.ChildTypeName.danek_instagram_posts),
            )
        )
        # Total comments per post = top-level comments + (top-level * child comments per comment)
        # e.g. 3 top-level comments with 2 child each = 3 * (1 + 2) = 9
        max_comments_per_post = self.scrape_comments_count_per_post * (
            1 + self.limit_child_comments_per_comment
        )
        max_comment_count: int = max_gather_result_count * max_comments_per_post

        if max_comment_count > 0:
            comments_estimate: job_runs_schemas.JobRunResourceEstimate = (
                utils.calculate_job_run_resource_estimate_from_result_count(
                    max_comment_count,
                    utils.get_danek_costs_per_100k(
                        gather_schemas.ChildTypeName.danek_instagram_comments
                    ),
                )
            )
        else:
            comments_estimate = job_runs_schemas.JobRunResourceEstimate(
                max_gather_result_count=0,
                max_total_cost=0,
            )
        total_max_estimate: job_runs_schemas.JobRunResourceEstimate = (
            job_runs_schemas.JobRunResourceEstimate(
                max_gather_result_count=(
                    comments_estimate.max_gather_result_count
                    + posts_estimate.max_gather_result_count
                ),
                max_total_cost=(comments_estimate.max_total_cost + posts_estimate.max_total_cost),
            )
        )
        return total_max_estimate


class DanekInstagramPostsGatherCreate(gather_schemas.GatherCreate, DanekInstagramPostsGatherBase):
    """Danek Gather Instagram posts create schema.

    Properties to receive via API on creation.
    """


class DanekInstagramPostsGatherUpdate(gather_schemas.GatherUpdate):
    """Danek Gather Instagram update schema.

    Properties to receive via API on update.
    """

    limit_posts_per_account: Optional[int] = pydantic.Field(
        description="Limit number of posts per account."
    )
    account_username_list: OptionalAccountUsernameList = pydantic.Field(
        description=("List of accounts to scrape Instagram Posts for."),
    )
    posts_created_after: ValidatedDate = pydantic.Field(
        default=None,
        description=POSTS_CREATED_AFTER_DESCRIPTION,
    )
    scrape_comments_count_per_post: Optional[int] = pydantic.Field(
        default=None,
        description=SCRAPE_COMMENTS_COUNT_DESCRIPTION,
    )
    limit_child_comments_per_comment: Optional[int] = pydantic.Field(
        serialization_alias="limitChildCommentsPerPost",
        default=None,
        description="Limit child comments per comment; defaults to 0 if not set.",
    )
