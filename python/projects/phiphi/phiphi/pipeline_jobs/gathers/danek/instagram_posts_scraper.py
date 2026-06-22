"""Integration for the Danek Instagram posts scraper."""

import logging
import math
from datetime import datetime, timezone
from typing import Callable, Iterator, Optional

from phiphi import utils
from phiphi.api.projects.gathers.danek_instagram_posts import schemas
from phiphi.pipeline_jobs.gathers import gather_batch_write_managers
from phiphi.pipeline_jobs.gathers.danek import api, constants

utils.init_logging()

file_logger = logging.getLogger(__name__)

DEFAULT_URL = "https://ig-scraper-api.fly.dev/custom/build_up/user/posts"


def form_instagram_posts_requests(
    token: str,
    gather: schemas.DanekInstagramPostsGatherResponse,
    cursor: Optional[str] = None,
) -> Iterator[tuple[str, dict, dict]]:
    """Prepare URL, headers, and payload for the search request.

    Args:
        token: Danek API token.
        gather: Gather object.
        cursor: Cursor for pagination.

    Returns:
        Tuple of (url, headers, payload) for each request.
    """
    url = DEFAULT_URL
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for username in gather.account_username_list:
        payload = {
            "username": username,
            "after_cursor": cursor,
        }

        yield url, headers, payload


# Instagram allows up to 3 pinned posts per account. These appear first on the account page
# and may be old, so we skip them on the first page to avoid stopping pagination prematurely.
MAX_PINNED_POSTS = 3


def make_posts_created_after_stop_condition(
    posts_created_after: str,
    num_pinned_posts_to_skip: int = MAX_PINNED_POSTS,
) -> Callable[[dict, int], bool]:
    """Return a stop condition that halts pagination when the oldest post predates the cutoff.

    On the first page, up to num_pinned_posts_to_skip leading items are ignored to account
    for pinned posts which may be old but do not reflect the account's recent activity.

    Args:
        posts_created_after: ISO 8601 datetime string (UTC). Pagination stops when the oldest
            post's taken_at timestamp in a page is before this value.
        num_pinned_posts_to_skip: Number of leading items to skip on the first page.

    Returns:
        A callable that takes a page result dict and page number and returns True if pagination
        should stop.
    """
    cutoff = datetime.fromisoformat(posts_created_after)
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)

    def stop_condition(result: dict, page_number: int) -> bool:
        items = result.get("items", [])
        if not items:
            return False
        if page_number == 1:
            items = items[num_pinned_posts_to_skip:]
        if not items:
            return False
        taken_at_values = [
            item["node"]["taken_at"]
            for item in items
            if isinstance(item.get("node"), dict) and item["node"].get("taken_at")
        ]
        if not taken_at_values:
            return False
        oldest_post_dt = datetime.fromtimestamp(min(taken_at_values), tz=timezone.utc)
        return oldest_post_dt < cutoff

    return stop_condition


def scrape_instagram_posts_and_add_to_write_manager(
    gather: schemas.DanekInstagramPostsGatherResponse,
    write_manager: gather_batch_write_managers.GatherBatchWriteManager,
    logger: None | logging.Logger | logging.LoggerAdapter = None,
) -> None:
    """Scrape data using the Danek API and write them using the GatherBatchWriteManager.

    Important: You will need to run `write_manager.complete_write()` after this task to ensure
    that all data is written to the data store.

    Args:
        gather: The gather object to scrape.
        write_manager: The write manager to add the scraped data to. Should be used and mutated. Do
            not make a copy or recreate.
        logger: The logger to use for logging. Defaults to file logger

    Returns:
        Writer with collected search results.
    """
    if logger is None:
        logger = file_logger
    token = utils.get_danek_api_token("instagram")
    max_response_count = math.ceil(
        gather.limit_posts_per_account / constants.INSTAGRAM_API_PAGE_SIZE
    )
    logger.info(f"Starting to scrape Instagram posts with gather id: {gather.id}")
    for url, headers, payload in form_instagram_posts_requests(token, gather):
        # A fresh stop condition is created per username so that the first-page pinned-post
        # skip state resets correctly for each account.
        pagination_stop_condition = None
        if gather.posts_created_after is not None:
            pagination_stop_condition = make_posts_created_after_stop_condition(
                gather.posts_created_after
            )
        api.get_results_and_add_to_write_manager(
            url,
            headers,
            payload,
            write_manager,
            max_response_count,
            logger,
            pagination_stop_condition=pagination_stop_condition,
        )
    logger.info(f"Finished scraping all search queries for gather id: {gather.id}")
    return None
