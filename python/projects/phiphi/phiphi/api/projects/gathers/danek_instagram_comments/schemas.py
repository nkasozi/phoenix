"""Schemas for Danek Instagram comments."""

from typing import Optional

import pydantic

from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.gathers import utils
from phiphi.api.projects.job_runs import schemas as job_runs_schemas


class DanekInstagramCommentsGatherBase(gather_schemas.GatherBase):
    """Input schema for the Danek Instagram Scraper for comments."""

    post_id_list: list[str] = pydantic.Field(
        serialization_alias="post_ids",
        description="List of Instagram post IDs to scrape comments from",
    )
    limit_comments_per_post: int = pydantic.Field(
        serialization_alias="resultsLimit",
        default=50,
        description="Limit results per post; defaults to 50 if not set",
    )
    limit_child_comments_per_comment: int = pydantic.Field(
        serialization_alias="limitChildCommentsPerPost",
        default=0,
        description="Limit child comments per comment; defaults to 0 if not set",
    )


class DanekInstagramCommentsGatherResponse(
    gather_schemas.GatherChildResponseBase, DanekInstagramCommentsGatherBase
):
    """Danek Instagram comments gather schema."""

    # Both the property and computed_field decorators are used other wise mypy thinks that the
    # property is a function
    # Mypy doesn't allow both property and computed_field decorators, hence the ignore
    @pydantic.computed_field  # type: ignore[prop-decorator]
    @property
    def job_run_resource_estimate(self) -> job_runs_schemas.JobRunResourceEstimate:
        """Calculate the resource estimate for the job run."""
        max_comments: int = len(self.post_id_list) * self.limit_comments_per_post
        max_gather_result_count: int = max_comments + (
            max_comments * self.limit_child_comments_per_comment
        )

        return utils.calculate_job_run_resource_estimate_from_result_count(
            max_gather_result_count,
            utils.get_danek_costs_per_100k(gather_schemas.ChildTypeName.danek_instagram_comments),
        )


class DanekInstagramCommentsGatherCreate(
    DanekInstagramCommentsGatherBase, gather_schemas.GatherCreate
):
    """Apify TikTok Comments Gather create schema.

    Properties to receive via API on creation.
    """


class DanekInstagramCommentsGatherUpdate(gather_schemas.GatherUpdate):
    """Danek Instagram Comments Gather update schema.

    Only properties that are set will be updated.
    """

    limit_comments_per_post: Optional[int] = pydantic.Field(
        default=None,
        description="Limit results per post; defaults to 50 if not set",
    )
    limit_child_comments_per_comment: Optional[int] = pydantic.Field(
        default=None,
        description="Limit child comments per comment; defaults to 0 if not set",
    )
    post_id_list: Optional[list[str]] = pydantic.Field(
        default=None,
        description="List of Instagram post IDs to scrape comments from",
    )
