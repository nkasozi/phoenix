"""Scrape interface for danek.

A generalised scrape interface that will also for the scraping of different types of data from
Danek.
"""

import logging

from phiphi import config, utils
from phiphi.api.projects import gathers
from phiphi.pipeline_jobs.gathers import gather_batch_write_managers
from phiphi.pipeline_jobs.gathers import types as gather_types
from phiphi.pipeline_jobs.gathers import utils as gather_utils
from phiphi.pipeline_jobs.gathers.danek import (
    facebook_search_scraper,
    instagram_comments_scraper,
    instagram_posts_scraper,
)

utils.init_logging()

file_logger = logging.getLogger(__name__)


def get_mock_danek_items(child_type: gathers.schemas.ChildTypeName) -> list[dict]:
    """Get mock items for the given child type.

    This test is used for testing purposes only.
    """
    return gather_utils.load_sample_raw_data(child_type_name=child_type)


def mock_danek_scrape(
    child_type: gathers.schemas.ChildTypeName,
    write_manager: gather_batch_write_managers.GatherBatchWriteManager,
) -> None:
    """Mock the scraping.

    Args:
        child_type: The child type to scrape.
        write_manager: The write manager to add the scraped data to. Should be used and mutated. Do
            not make a copy or recreate.

    Returns:
        Writer with collected search results.
    """
    for item in get_mock_danek_items(child_type):
        write_manager.add(item)
    return None


def danek_scrape(
    gather: gathers.schemas.GatherChildResponseBase,
    write_manager: gather_batch_write_managers.GatherBatchWriteManager,
    logger: None | logging.Logger | logging.LoggerAdapter = None,
) -> gather_types.ScrapeCost:
    """Scrape data using the Danek API and write them using the GatherBatchWriteManager.

    Args:
        gather: The gather object to scrape.
        write_manager: The write manager to add the scraped data to. Should be used and mutated. Do
            not make a copy or recreate.
        logger: The logger to use for logging. Defaults to file logger

    Returns:
        The cost of the scrape.
    """
    if logger is None:
        logger = file_logger
    child_type = gather.child_type

    cost_per_100k = gathers.utils.get_danek_costs_per_100k(gather_child_type=child_type)

    if config.settings.USE_MOCK_DANEK:
        logger.info("Reading mock data.")
        mock_danek_scrape(child_type, write_manager)
        # Using isinstance so the type checker knows the type of gather
    elif isinstance(
        gather,
        gathers.danek_facebook_searches_posts.schemas.DanekFacebookSearchesPostsGatherResponse,
    ):
        facebook_search_scraper.scrape_facebook_searches_and_add_to_write_manager(
            gather=gather, write_manager=write_manager, logger=logger
        )
    elif isinstance(
        gather,
        gathers.danek_instagram_posts.schemas.DanekInstagramPostsGatherResponse,
    ):
        instagram_posts_scraper.scrape_instagram_posts_and_add_to_write_manager(
            gather=gather, write_manager=write_manager, logger=logger
        )
    elif isinstance(
        gather,
        gathers.danek_instagram_comments.schemas.DanekInstagramCommentsGatherResponse,
    ):
        instagram_comments_scraper.scrape_instagram_comments_and_add_to_write_manager(
            gather=gather, write_manager=write_manager, logger=logger
        )
    else:
        raise ValueError(
            f"Unknown gather type for danek scraper: {child_type} for gather id: {gather.id}"
        )

    cost = cost_per_100k * (write_manager.item_count / 100000)
    return gather_types.ScrapeCost(cost=cost, is_cost_estimated=False)
