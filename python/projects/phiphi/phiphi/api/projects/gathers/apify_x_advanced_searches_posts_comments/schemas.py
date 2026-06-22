"""Schemas for Apify X Advanced Search → Posts+Comments gathers.

Actor: https://apify.com/apidojo/twitter-scraper-lite
We put everything in `searchTerms` exactly as the user writes it.
"""

from datetime import timezone
from typing import Annotated, Any, List, Literal, Optional

import pydantic
from dateutil import parser as dateutil_parser

from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.gathers import utils
from phiphi.api.projects.job_runs import schemas as job_runs_schemas

ValidatedDate = Annotated[
    Optional[str], pydantic.AfterValidator(utils.validate_and_normalise_datetime)
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


class ApifyXAdvancedSearchesPostsCommentsGatherBase(gather_schemas.GatherBase):
    """Input schema for X search-terms → posts comments."""

    search_list: List[str] = pydantic.Field(
        serialization_alias="searchTerms",
        description=(
            "Advanced X queries. Example: ['from:NASA to:buildup']. Shouldn't include "
            "`since:` or `until:` filters as we have separate fields for that."
        ),
    )
    limit_results_per_search: int = pydantic.Field(
        description="Max tweets to collect per query (we compute global maxItems from this)."
    )
    posts_created_after: ValidatedDate = pydantic.Field(
        default=None,
        description=POSTS_CREATED_AFTER_DESCRIPTION,
    )
    posts_created_before: ValidatedDate = pydantic.Field(
        default=None,
        description=POSTS_CREATED_BEFORE_DESCRIPTION,
    )
    sort: Literal["Latest", "Top"] | None = pydantic.Field(
        serialization_alias="sort",
        default="Latest",
        description=("Sort order. One of 'Latest', 'Top'. Defaults to 'Latest' in serialization."),
    )


class ApifyXAdvancedSearchesPostsCommentsGatherResponse(
    gather_schemas.GatherChildResponseBase, ApifyXAdvancedSearchesPostsCommentsGatherBase
):
    """Response schema for X search-terms → posts comments."""

    def _format_since_until(self, dt_str: Optional[str], kind: str) -> Optional[str]:
        """Format per Twitter Advance Search docs.

        - Date-only -> kind:YYYY-MM-DD
        - Datetime  -> kind:YYYY-MM-DD_HH:MM:SS_UTC (explicit UTC)
        """
        if not dt_str:
            return None
        dt = dateutil_parser.isoparse(dt_str).astimezone(timezone.utc)
        is_midnight = (dt.hour, dt.minute, dt.second, dt.microsecond) == (0, 0, 0, 0)
        if is_midnight:
            return f"{kind}:{dt.date().isoformat()}"
        return f"{kind}:{dt.strftime('%Y-%m-%d_%H:%M:%S_UTC')}"

    def serialize_to_apify_input(self) -> dict[str, Any]:
        """Build a single-actor payload.

        - searchTerms: search_list with appended since:/until: fragments
        - maxItems: limit_results_per_search
        - includeSearchTerms: True (for downstream attribution)
        - sort: 'Latest' (default if not set)
        """
        apify_dict = super().serialize_to_apify_input()

        # Pull terms (key is 'searchTerms' thanks to the alias)
        terms: list[str] = list(apify_dict.get("searchTerms", []) or [])

        since_frag = self._format_since_until(self.posts_created_after, "since")
        until_frag = self._format_since_until(self.posts_created_before, "until")
        date_suffix = " ".join(x for x in (since_frag, until_frag) if x)

        if date_suffix:
            terms = [f"{q.strip()} {date_suffix}".strip() for q in terms]

        apify_dict["searchTerms"] = terms
        # The actor can only limit total results for a actor run, not per-query. The pipeline will
        # run one actor run per query so we set maxItems to the per-query limit.
        apify_dict["maxItems"] = self.limit_results_per_search
        apify_dict["includeSearchTerms"] = True
        apify_dict["sort"] = apify_dict.get("sort") or "Latest"

        # Don't leak internal fields to the actor
        apify_dict.pop("limit_results_per_search", None)
        apify_dict.pop("posts_created_after", None)
        apify_dict.pop("posts_created_before", None)

        return apify_dict

    @pydantic.computed_field  # type: ignore[prop-decorator]
    @property
    def job_run_resource_estimate(self) -> job_runs_schemas.JobRunResourceEstimate:
        """Estimate using total results cap (queries * per-query cap)."""
        max_gather_result_count: int = len(self.search_list) * self.limit_results_per_search
        return utils.calculate_job_run_resource_estimate_from_result_count(
            max_gather_result_count,
            utils.get_mean_cost_per_100k_results(
                gather_schemas.ChildTypeName.apify_x_advanced_searches_posts_comments
            ),
        )


class ApifyXAdvancedSearchesPostsCommentsGatherCreate(
    gather_schemas.GatherCreate, ApifyXAdvancedSearchesPostsCommentsGatherBase
):
    """Create schema."""


class ApifyXAdvancedSearchesPostsCommentsGatherUpdate(gather_schemas.GatherUpdate):
    """Update schema (partial)."""

    search_list: list[str] | None = pydantic.Field(default=None)
    limit_results_per_search: int | None = pydantic.Field(default=None)
    posts_created_after: ValidatedDate = pydantic.Field(
        default=None,
        description=POSTS_CREATED_AFTER_DESCRIPTION,
    )
    posts_created_before: ValidatedDate = pydantic.Field(
        default=None,
        description=POSTS_CREATED_BEFORE_DESCRIPTION,
    )
    sort: Literal["Latest", "Top"] | None = pydantic.Field(
        serialization_alias="sort",
        default=None,
        description=("Sort order. One of 'Latest', 'Top'."),
    )
