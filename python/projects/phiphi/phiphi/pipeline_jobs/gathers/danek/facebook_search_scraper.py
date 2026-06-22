"""Integration for the Danek Facebook search scraper."""

import logging
from enum import Enum
from typing import Any, Iterator, Optional

from phiphi import utils
from phiphi.api.projects.gathers.danek_facebook_searches_posts import schemas
from phiphi.pipeline_jobs.gathers import gather_batch_write_managers
from phiphi.pipeline_jobs.gathers.danek import api

utils.init_logging()

file_logger = logging.getLogger(__name__)

DEFAULT_URL = "https://fb-scraper-api.fly.dev/api/custom/build_up/search"


class SearchType(str, Enum):
    """Enum for Danek API type."""

    PAGES = "PAGES_TAB"
    PLACES = "PLACES_TAB"
    POSTS = "POSTS_TAB"
    GROUPS = "GROUPS_TAB"
    VIDEOS = "VIDEOS_TAB"
    EVENTS = "EVENTS_TAB"


def form_facebook_search_requests(
    token: str,
    gather: schemas.DanekFacebookSearchesPostsGatherResponse,
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
    search_config: dict[str, Any] = {
        "recent_posts": gather.recent_posts,
    }

    if gather.posts_created_after is not None:
        search_config["start_date"] = gather.posts_created_after

    if gather.posts_created_before is not None:
        search_config["end_date"] = gather.posts_created_before

    if gather.proxy_country_to_gather_from is not None:
        search_config["proxy_code"] = gather.proxy_country_to_gather_from.value

    for search_query in gather.search_list:
        payload = {
            "query": search_query,
            "cursor": cursor,
            "search_type": SearchType.POSTS,
            "search_config": search_config,
        }

        yield url, headers, payload


def scrape_facebook_searches_and_add_to_write_manager(
    gather: schemas.DanekFacebookSearchesPostsGatherResponse,
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
    token = utils.get_danek_api_token("facebook")
    logger.info(f"Starting to scrape Facebook searches for gather id: {gather.id}")
    for url, headers, payload in form_facebook_search_requests(token, gather):
        api.get_results_and_add_to_write_manager(
            url,
            headers,
            payload,
            write_manager,
            gather.stop_scraping_per_search_after_count,
            logger,
        )
    logger.info(f"Finished scraping all search queries for gather id: {gather.id}")
    return None
