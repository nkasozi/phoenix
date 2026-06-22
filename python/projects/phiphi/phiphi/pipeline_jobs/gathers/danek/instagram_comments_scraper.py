"""Integration for the Danek Instagram comments scraper."""

import logging
import math
from typing import Iterator, Optional

from phiphi import utils
from phiphi.api.projects.gathers.danek_instagram_comments import schemas
from phiphi.api.projects.gathers.schemas import ChildTypeName
from phiphi.pipeline_jobs.gathers import gather_batch_write_managers, normalise
from phiphi.pipeline_jobs.gathers.danek import api, constants

utils.init_logging()

file_logger = logging.getLogger(__name__)

DEFAULT_URL = "https://ig-scraper-api.fly.dev/custom/build_up/post/comments"
DEFAULT_CHILDCOMMENT_URL = "https://ig-scraper-api.fly.dev/custom/build_up/post/comments/nested"


def form_instagram_comments_requests(
    token: str,
    gather: schemas.DanekInstagramCommentsGatherResponse,
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

    for post_id in gather.post_id_list:
        payload = {
            "post_id": str(post_id),
            "end_cursor": cursor,
        }

        yield url, headers, payload


def form_instagram_child_comments_requests(
    token: str,
    comment_ids_with_child_comments: list[tuple[str, str]],
    cursor: Optional[str] = None,
) -> Iterator[tuple[str, dict, dict]]:
    """Prepare URL, headers, and payload for the child_comments request.

    Args:
        token: Danek API token.
        gather: Gather object.
        comment_ids_with_child_comments: List of (comment_pk, post_id) tuples.
        cursor: Cursor for pagination.

    Returns:
        Tuple of (url, headers, payload) for each request.
        payload can include optional fields like max_id for pagination.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for comment_pk, post_id in comment_ids_with_child_comments:
        url = DEFAULT_CHILDCOMMENT_URL

        # cursor for child comments is called max_id
        payload = {
            "post_id": str(post_id),
            "comment_pk": str(comment_pk),
            "max_id": cursor,
        }

        yield url, headers, payload


def collect_child_comments_from_raw_json(
    comment_response: dict, payload: dict, collected: list[tuple[str, str]]
) -> None:
    """Appends tuple(comment_pk, post_id) to the collected list for subcomment scraping.

    Uses the normaliser's flattening logic to determine if a comment has child comments.
    """
    # Only flatten; don't do full normalisation
    batch_json_flattened, _ = normalise.prepare_batch_json_for_normalisation(
        [comment_response], ChildTypeName.danek_instagram_comments
    )
    for node in batch_json_flattened:
        if int(node.get("child_comment_count", 0)) > 0:
            comment_pk = node.get("pk")
            post_id = payload.get("post_id")
            if comment_pk and post_id:
                collected.append((comment_pk, post_id))


def scrape_instagram_comments_and_add_to_write_manager(
    gather: schemas.DanekInstagramCommentsGatherResponse,
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
    comment_ids_with_child_comments: list[tuple[str, str]] = []

    on_result_callback = None
    if gather.limit_child_comments_per_comment > 0:

        def child_comment_callback(comment_json: dict, payload: dict) -> None:
            collect_child_comments_from_raw_json(
                comment_json, payload, comment_ids_with_child_comments
            )

        on_result_callback = child_comment_callback

    token = utils.get_danek_api_token("instagram")
    max_response_count = math.ceil(
        gather.limit_child_comments_per_comment / constants.INSTAGRAM_API_PAGE_SIZE
    )
    logger.info(
        f"Starting to scrape Instagram comments with gather id: {gather.id}, "
        f"post_id_list={gather.post_id_list}, "
        f"limit_comments_per_post={gather.limit_comments_per_post}, "
        f"limit_child_comments_per_comment={gather.limit_child_comments_per_comment}, "
        f"max_response_count={max_response_count}"
    )
    for url, headers, payload in form_instagram_comments_requests(token, gather):
        logger.info(
            f"Scraping comments for payload: post_id={payload.get('post_id')},"
            f" end_cursor={payload.get('end_cursor')}"
        )
        items_before = write_manager.item_count
        api.get_results_and_add_to_write_manager(
            url,
            headers,
            payload,
            write_manager,
            # We currently save entire responses as a unit of results. Each response gets a max of
            # 10 comments. This makes it
            max_response_count,
            logger,
            on_result=on_result_callback,
        )
        logger.info(
            f"Finished scraping comments for post_id={payload.get('post_id')}: "
            f"responses_scraped={write_manager.item_count - items_before}"
        )
    logger.info(
        f"Finished scraping all comments for gather id: {gather.id}, "
        f"total_responses={write_manager.item_count}, "
        f"child_comments_to_scrape={len(comment_ids_with_child_comments)}"
    )

    if gather.limit_child_comments_per_comment > 0:
        logger.info(
            f"Gather child comments flag is turned on."
            f"Gathering max {gather.limit_child_comments_per_comment} child_comments."
            f"Start scraping child_comments from {len(comment_ids_with_child_comments)} "
            f"comments that have child_comments"
        )
        for url, headers, payload in form_instagram_child_comments_requests(
            token, comment_ids_with_child_comments
        ):
            logger.info(
                f"Scraping child comments for post_id={payload.get('post_id')}, "
                f"comment_pk={payload.get('comment_pk')}"
            )
            api.get_results_and_add_to_write_manager(
                url,
                headers,
                payload,
                write_manager,
                # We currently save entire responses as a unit of results.
                # Each response gets a max of 10 comments.
                max_response_count,
                logger,
            )

    return None
