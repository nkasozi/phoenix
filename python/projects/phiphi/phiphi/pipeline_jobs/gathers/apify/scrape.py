"""Flow for gathering data from Apify.

Single flow that all Apify scrapers use.

Includes switch for using mock data read directly from file for testing purposes.
"""

import json
import logging
from typing import Dict, Iterator, Tuple

import apify_client
import prefect

from phiphi import config, utils
from phiphi.api.projects import gathers
from phiphi.pipeline_jobs import constants
from phiphi.pipeline_jobs.gathers import gather_batch_write_managers
from phiphi.pipeline_jobs.gathers import types as gather_types
from phiphi.pipeline_jobs.gathers import utils as gather_utils

utils.init_logging()

file_logger = logging.getLogger(__name__)

MOCK_APIFY_SCRAPE_COST = gather_types.ScrapeCost(
    cost=0.0,
    is_cost_estimated=False,
)

gather_apify_actor_map: dict[type[gathers.schemas.GatherChildResponseBase], str] = {
    gathers.apify_facebook_posts.schemas.ApifyFacebookPostsGatherResponse: (
        "apify/facebook-posts-scraper"
    ),
    gathers.apify_facebook_comments.schemas.ApifyFacebookCommentsGatherResponse: (
        "apify/facebook-comments-scraper"
    ),
    gathers.apify_facebook_search_posts.schemas.ApifyFacebookSearchPostsGatherResponse: (
        "danek/facebook-search-rental"
    ),
    gathers.apify_tiktok_accounts_posts.schemas.ApifyTikTokAccountsPostsGatherResponse: (
        "clockworks/tiktok-scraper"
    ),
    gathers.apify_tiktok_hashtags_posts.schemas.ApifyTikTokHashtagsPostsGatherResponse: (
        "clockworks/tiktok-scraper"
    ),
    gathers.apify_tiktok_searches_posts.schemas.ApifyTikTokSearchesPostsGatherResponse: (
        "clockworks/tiktok-scraper"
    ),
    gathers.apify_tiktok_comments.schemas.ApifyTikTokCommentsGatherResponse: (
        "apidojo/tiktok-comments-scraper"
    ),
    gathers.apify_x_advanced_searches_posts_comments.schemas.ApifyXAdvancedSearchesPostsCommentsGatherResponse: (  # noqa: E501
        "apidojo/twitter-scraper-lite"
    ),
    gathers.apify_x_simple_searches_posts_comments.schemas.ApifyXSimpleSearchesPostsCommentsGatherResponse: (  # noqa: E501
        "apidojo/twitter-scraper-lite"
    ),
}


def compute_cost_from_run_info(
    run_info: Dict,
    gather: gathers.schemas.GatherChildResponseBase,
    logger: None | logging.Logger | logging.LoggerAdapter = None,
) -> gather_types.ScrapeCost:
    """Compute the cost from Apify run_info.

    Args:
        run_info: The run info returned from Apify actor call.
        gather: The gather object used for logging purposes.
        logger: The logger to use for logging.

    Returns:
        ScrapeCost type.
    """
    if logger is None:
        logger = file_logger

    # There have been some cases when the `usageTotalUsd` is null
    # In this case we allow the user to have no costs but have a sentry alert
    if "usageTotalUsd" not in run_info:
        resource = {
            "prefect.resource.id": f"phoenix.apify.scrape.{gather.child_type.value}",
            # Have to be strings otherwise fails silently
            "phoenix.project.id": str(gather.project_id),
            "phoenix.gather.id": str(gather.id),
            "phoenix.apify.actor.id": str(run_info.get("actId", "not_found")),
            "phoenix.apify.run.id": str(run_info.get("id", "not_found")),
        }
        exception_info = json.dumps(resource)
        error_message = f"Missing 'usageTotalUsd' in Apify run_info. {exception_info}"
        logger.error(error_message)
        prefect.events.emit_event(
            event="phoenix.error.apify.malformed_run_info", resource=resource
        )
        return gather_types.ScrapeCost(
            cost=gather.job_run_resource_estimate.max_total_cost,
            is_cost_estimated=True,
        )
    else:
        cost_usd = float(run_info["usageTotalUsd"])

        # Currently the usageTotalUsd can be less than the minimum charge and the user is billed
        # for the minimum charge instead
        pricing_info = run_info.get("pricingInfo", {})
        min_charge = pricing_info.get("minimalMaxTotalChargeUsd")

        if min_charge is not None and cost_usd < min_charge:
            logger.info(
                f"Apify usage cost ({cost_usd}) is lower than minimum charge ({min_charge}). "
                f"Using minimum charge."
            )
            return gather_types.ScrapeCost(
                cost=min_charge,
                is_cost_estimated=False,
            )

        return gather_types.ScrapeCost(
            cost=cost_usd,
            is_cost_estimated=False,
        )


def apify_scrape(
    apify_token: str,
    actor_name: str,
    gather: gathers.schemas.GatherChildResponseBase,
    logger: None | logging.Logger | logging.LoggerAdapter = None,
    batch_size: int = constants.DEFAULT_APIFY_SCRAPE_PAGE_SIZE,
) -> Tuple[Iterator[list[Dict]], apify_client.clients.DatasetClient, gather_types.ScrapeCost]:
    """Scrape data using the Apify API and return an iterator of batches.

    Args:
        apify_token: The Apify API token.
        actor_name: The name of the Apify actor to run.
        gather: The gather object containing scraping parameters.
        logger: Optional logger for logging.
        batch_size: Number of items to fetch from the dataset per batch.

    Returns:
        Tuple containing:
        - Iterator yielding lists of items (batches)
        - DatasetClient for cleanup
        - ScrapeCost information
    """
    if logger is None:
        logger = file_logger

    client = apify_client.ApifyClient(apify_token)
    # Run the Apify actor
    # It is important to set the wait and timeout as:
    # some actors have a default timeout which can cause unexpected behaviour
    # the wait should be longer then the timeout as there has been cases here the timeout is
    # reached but the call does not return
    run_info = client.actor(actor_name).call(
        run_input=gather.serialize_to_apify_input(),
        timeout_secs=config.settings.APIFY_TIMEOUT_SECS,
        wait_secs=config.settings.APIFY_WAIT_SECS,
    )
    logger.info("Apify actor run info returned from call:")
    logger.info(run_info)
    assert run_info is not None
    # Access the dataset client associated with the actor's results
    dataset_client = client.dataset(run_info["defaultDatasetId"])
    logger.info("Apify dataset client created.")

    scrape_costs = compute_cost_from_run_info(run_info, gather, logger)

    def batch_iterator() -> Iterator[list[Dict]]:
        """Generate batches of items from the dataset using pagination."""
        offset = 0
        while True:
            # Fetch a batch of items using offset and limit
            batch = list(dataset_client.iterate_items(offset=offset, limit=batch_size))
            if not batch:
                # No more items to fetch
                break
            logger.debug(
                f"Fetched batch of {len(batch)} items from Apify dataset (offset={offset})"
            )
            yield batch
            offset += len(batch)

    return batch_iterator(), dataset_client, scrape_costs


def mock_apify_scrape(
    apify_token: str,
    actor_name: str,
    gather: gathers.schemas.GatherChildResponseBase,
    batch_size: int = constants.DEFAULT_APIFY_SCRAPE_PAGE_SIZE,
) -> Tuple[Iterator[list[Dict]], None, gather_types.ScrapeCost]:
    """Read mock scraping data and return an iterator of batches.

    Args:
        apify_token: The Apify API token (unused for mock).
        actor_name: The name of the Apify actor (unused for mock).
        gather: The gather object containing scraping parameters.
        batch_size: Number of items to include per batch.

    Returns:
        Tuple containing:
        - Iterator yielding lists of items (batches)
        - None (no dataset client for mock data)
        - ScrapeCost information (always 0 for mock)
    """
    sample_data = gather_utils.load_sample_raw_data(
        child_type_name=gather.child_type,
    )

    def batch_iterator() -> Iterator[list[Dict]]:
        """Generate batches from the sample data."""
        for i in range(0, len(sample_data), batch_size):
            yield sample_data[i : i + batch_size]

    return (
        batch_iterator(),
        None,
        MOCK_APIFY_SCRAPE_COST,
    )


def apify_scrape_and_add_to_write_manager(
    gather: gathers.schemas.GatherChildResponseBase,
    write_manager: gather_batch_write_managers.GatherBatchWriteManager,
    logger: None | logging.Logger | logging.LoggerAdapter = None,
    apify_dataset_batch_size: int = constants.DEFAULT_APIFY_SCRAPE_PAGE_SIZE,
) -> gather_types.ScrapeCost:
    """Scrape data using the Apify API and write them using the GatherBatchWriteManager.

    Important: You will need to run `write_manager.complete_write()` after this task to ensure
    that all data is written to the data store.

    Args:
        gather: The gather object to scrape.
        write_manager: The write manager to add the scraped data to. Should be used and mutated. Do
            not make a copy or recreate.
        logger: The logger to use for logging.
        apify_dataset_batch_size: Number of items to fetch from the Apify dataset per batch.
            This controls how many items are retrieved from Apify in each pagination request.

    Returns:
        ScrapeCost type.
    """
    if logger is None:
        logger = file_logger
    apify_token = utils.get_apify_api_key()
    apify_actor_name = gather_apify_actor_map[type(gather)]

    if config.settings.USE_MOCK_APIFY:
        logger.info("Reading mock data.")
        batch_iterator, dataset_client, scrape_costs = mock_apify_scrape(
            apify_token, apify_actor_name, gather, apify_dataset_batch_size
        )
    else:
        logger.info("Making Apify call.")
        batch_iterator, dataset_client, scrape_costs = apify_scrape(
            apify_token, apify_actor_name, gather, logger, apify_dataset_batch_size
        )

    # Iterate over batches and add each item to the write manager
    logger.info("Adding items to write manager.")
    total_items = 0
    batch_count = 0
    for batch in batch_iterator:
        batch_count += 1
        logger.info(f"Processing batch {batch_count} with {len(batch)} items from Apify dataset.")
        for item in batch:
            write_manager.add(item)
            total_items += 1

    logger.info(
        f"Completed processing {total_items} items from {batch_count} Apify dataset batches."
    )

    # Delete the dataset after downloading to save on storage costs
    if dataset_client is not None:
        logger.info("Deleting Apify dataset.")
        dataset_client.delete()

    return scrape_costs


def apify_scrape_batched_and_add_to_write_manager(
    gather: gathers.schemas.GatherChildResponseBase,
    write_manager: gather_batch_write_managers.GatherBatchWriteManager,
    batch_attr_name: str,
    batch_size: int,
    logger: None | logging.Logger | logging.LoggerAdapter = None,
) -> gather_types.ScrapeCost:
    """Run multiple Apify scrapes by batching a list attribute on the gather.

    - Sequential execution (no concurrency).
    - Copies the original gather for each batch, only replacing the target list attribute
      with a slice of length <= batch_size.
    - Returns the sum of costs from each batch.

    Args:
        gather: The full gather object (will NOT be mutated).
        write_manager: Existing write manager to which batch results are appended.
        batch_attr_name: Name of the list attribute to batch over (e.g., "search_list").
        batch_size: Max number of items from that list per batch.
        logger: Optional logger.

    Returns:
        Total scrape costs across all batches.
    """
    if logger is None:
        logger = file_logger

    items = getattr(gather, batch_attr_name)
    # If the list is empty or None, just do nothing and return 0 cost.
    if not items:
        return gather_types.ScrapeCost(cost=0.0, is_cost_estimated=False)

    cost = 0.0
    n = len(items)

    is_cost_estimated = False

    # Iterate sequentially over slices of the target list attribute.
    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        batch_slice = items[start:end]

        # Create a new gather instance with the same fields but sliced list attribute.
        batched_gather = gather.model_copy(update={batch_attr_name: batch_slice})

        batch_scrape_cost = apify_scrape_and_add_to_write_manager(
            gather=batched_gather,
            write_manager=write_manager,
            logger=logger,
        )
        cost += batch_scrape_cost.cost
        if batch_scrape_cost.is_cost_estimated:
            logger.warning(
                f"Batch scrape cost estimated for gather ID {gather.id} "
                f"from index {start} to {end}."
            )
            is_cost_estimated = True

    return gather_types.ScrapeCost(
        cost=cost,
        is_cost_estimated=is_cost_estimated,
    )
