"""Schemas for Apify X Simple Search → Posts+Comments gathers.

Actor: https://apify.com/apidojo/twitter-scraper-lite

Simple interface for users to do keyword and handle searches.
"""

from datetime import timezone
from functools import cached_property
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


class ApifyXSimpleSearchesPostsCommentsGatherBase(gather_schemas.GatherBase):
    """Input schema for X search-terms → posts comments."""

    handle_list: List[str] = pydantic.Field(
        description=("Twitter handles to search for (without @). Example: ['NASA', 'ESA']."),
    )
    keywords_list: List[str] = pydantic.Field(
        description=("Keywords to search for. Example: ['Mars exploration']."),
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
        description=("Sort order. One of 'Latest', 'Top'."),
    )
    location_near: Optional[str] = pydantic.Field(
        default=None,
        description=(
            "If set, will add `near:` filter to each query. Example: 'London' or 'London, UK'."
        ),
    )

    @pydantic.computed_field  # type: ignore[prop-decorator]
    @cached_property  # Cached to avoid recomputation
    def search_list(self) -> List[str]:
        """Generate search terms based on handle_list and keywords_list.

        Rules:
        - If both handle_list and keywords_list are given, create a query for each
          handle with `from:` including all the keywords.
        - If only one of handle_list or keywords_list is given, build search terms
          from just that list.
        - For each query, since, until and near fragments are added if given.
        """
        # Build the base query list
        terms: list[str] = []

        handles = [h.strip() for h in (self.handle_list or []) if h and h.strip()]
        keywords = [k.strip() for k in (self.keywords_list or []) if k and k.strip()]

        if handles and keywords:
            # Both handles and keywords: one query per handle, including all keywords.
            for h in handles:
                terms.extend([f"from:{h} {q}" for q in keywords])
        elif handles:
            # Only handles: one query per handle.
            for h in handles:
                terms.append(f"from:{h}")
        elif keywords:
            terms.extend(keywords)
        else:
            terms = [""]

        # Append date and location filters to each term, if present.
        since_frag = self._format_since_until(self.posts_created_after, "since")
        until_frag = self._format_since_until(self.posts_created_before, "until")
        near_frag = (
            f"near:{self.location_near.strip()}"
            if self.location_near and self.location_near.strip()
            else None
        )

        suffix_parts = [p for p in (since_frag, until_frag, near_frag) if p]
        suffix = " ".join(suffix_parts)

        if suffix:
            terms = [f"{q} {suffix}".strip() for q in terms]

        return terms

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


class ApifyXSimpleSearchesPostsCommentsGatherResponse(
    gather_schemas.GatherChildResponseBase, ApifyXSimpleSearchesPostsCommentsGatherBase
):
    """Response schema for X search-terms → posts comments."""

    def serialize_to_apify_input(self) -> dict[str, Any]:
        """Build a single-actor payload using the computed search_list.

        - searchTerms: Uses the search_list property which generates queries
          based on handle_list and keywords_list with date/location filters.
        - maxItems: limit_results_per_search (per-query cap)
        - includeSearchTerms: True (for downstream attribution)
        - sort: 'Latest' (default if not set)
        """
        apify_dict: dict[str, Any] = {
            "searchTerms": self.search_list,
            # The apify scraper will do a maxItems cap per query
            "maxItems": int(self.limit_results_per_search),
            "includeSearchTerms": True,
            "sort": self.sort or "Latest",
        }

        # Do not leak internal-only inputs to the actor.
        # (These have been consumed to build `searchTerms`/`maxItems`.)
        # Intentionally NOT including: handle_list, keywords_list, posts_created_after,
        # posts_created_before, limit_results_per_search, location_near.
        return apify_dict

    @pydantic.computed_field  # type: ignore[prop-decorator]
    @property
    def job_run_resource_estimate(self) -> job_runs_schemas.JobRunResourceEstimate:
        """Estimate using total results cap (queries * per-query cap)."""
        full_count_of_queries = len(self.search_list)
        max_gather_result_count: int = full_count_of_queries * self.limit_results_per_search
        estimate_mean_cost_per_100k = utils.get_mean_cost_per_100k_results(
            gather_schemas.ChildTypeName.apify_x_simple_searches_posts_comments
        )
        return utils.calculate_job_run_resource_estimate_from_result_count(
            max_gather_result_count,
            estimate_mean_cost_per_100k,
        )


class ApifyXSimpleSearchesPostsCommentsGatherCreate(
    gather_schemas.GatherCreate, ApifyXSimpleSearchesPostsCommentsGatherBase
):
    """Create schema."""


class ApifyXSimpleSearchesPostsCommentsGatherUpdate(gather_schemas.GatherUpdate):
    """Update schema (partial)."""

    handle_list: List[str] | None = pydantic.Field(
        default=None,
        description=("Twitter handles to search for (without @). Example: ['NASA', 'ESA']."),
    )
    keywords_list: List[str] | None = pydantic.Field(
        default=None,
        description=("Keywords to search for. Example: ['Mars exploration']."),
    )
    limit_results_per_search: int | None = pydantic.Field(
        default=None,
        description="Max tweets to collect per query (we compute global maxItems from this).",
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
        default=None,
        description=("Sort order. One of 'Latest', 'Top'."),
    )
    location_near: Optional[str] | None = pydantic.Field(
        default=None,
        description=(
            "If set, will add `near:` filter to each query. Example: 'London' or 'London, UK'."
        ),
    )
