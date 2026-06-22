"""API functions for making requests to the Danek API."""

import json
import logging
import time
from typing import Callable, Optional

import requests

from phiphi import utils
from phiphi.pipeline_jobs.gathers import gather_batch_write_managers

utils.init_logging()

file_logger = logging.getLogger(__name__)

# Timeout in seconds for HTTP requests to the Danek API.
# This prevents requests from hanging indefinitely if the server is slow or unresponsive.
DANEK_REQUEST_TIMEOUT_SECS = 600


def make_single_request(
    url: str, headers: dict, payload: dict, max_retries: int = 3, backoff_factor: float = 1.0
) -> tuple[list, dict[str, str] | None]:
    """Makes a single request to the Danek API, with retry logic.

    Args:
        url: Complete endpoint URL.
        headers: HTTP request headers.
        payload: JSON body to post.
        max_retries: Maximum number of retry attempts for transient errors.
        backoff_factor: Factor by which the sleep time increases
            after each retry (exponential backoff).

    Returns:
        A tuple containing the search results (list) and the cursor dict[str,str] for pagination.

    Raises:
        RuntimeError: For any request or response parsing issues after exhausting retries.
    """
    for attempt in range(max_retries):
        status_code = None
        response_json = None
        try:
            request_start_time = time.time()
            response = requests.post(
                url, headers=headers, json=payload, timeout=DANEK_REQUEST_TIMEOUT_SECS
            )
            request_duration = time.time() - request_start_time
            status_code = response.status_code
            response_json = response.json()
            response.raise_for_status()

            # Attempt to parse the JSON for facebook searches.
            results = response_json.get("results", [])

            # if this is an instagram posts, comments or child comments,
            # Wrap the entire response json as a single dict in a list so that we have one
            # response being the unit of thing being saved instead of parsing a "post" from
            # results.
            if response_json.get("items") or response_json.get("child_comments"):
                # enrich/inject parent_post_id for comments and child_comments as it is not in the
                # response. If post_id is in the payload, it's a comment type
                if payload.get("post_id"):
                    response_json["parent_post_id"] = payload.get("post_id")
                results = [response_json]

            cursor = get_cursor_from_response_json(response_json)
            file_logger.info(
                f"Request completed: status={status_code}, "
                f"duration={request_duration:.2f}s, "
                f"results_count={len(results)}, "
                f"has_cursor={cursor is not None}, "
                f"cursor={cursor}"
            )
            return results, cursor

        except requests.exceptions.HTTPError as exc:
            # Check if it's a server error (5xx). If so, retry; otherwise, re-raise.
            if status_code and 500 <= status_code < 600 and attempt < max_retries:
                sleep_time = backoff_factor * (2**attempt)
                file_logger.warning(
                    f"HTTP {status_code} error, retrying in {sleep_time:.1f}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(sleep_time)
                continue
            else:
                raise RuntimeError(
                    f"HTTP error occurred (status code {status_code}): {exc}"
                ) from exc

        except requests.exceptions.RequestException as exc:
            # Covers various connection-related errors (ConnectionError, Timeout, etc.)
            # Retry on the assumption it's transient.
            if attempt < max_retries:
                sleep_time = backoff_factor * (2**attempt)
                file_logger.warning(
                    f"Request failed with {type(exc).__name__}: {exc}, "
                    f"retrying in {sleep_time:.1f}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(sleep_time)
                continue
            else:
                raise RuntimeError(f"Network or connection error occurred: {exc}") from exc

        except ValueError as exc:
            # JSON parsing error: typically not transient, so we do not retry.
            raise RuntimeError(f"Failed to parse JSON response: {exc}") from exc

    # If we exited the loop without returning or raising, raise a generic error.
    raise RuntimeError("Failed to complete request after all retries.")


def _process_page_results(
    results: list,
    write_manager: gather_batch_write_managers.GatherBatchWriteManager,
    payload: dict,
    on_result: None | Callable,
    pagination_stop_condition: Optional[Callable[[dict, int], bool]],
    page_number: int,
) -> tuple[int, bool]:
    """Write results to the manager and check stop conditions.

    Returns:
        Tuple of (count of results processed, whether pagination should stop).
    """
    stop_pagination = False
    for result in results:
        write_manager.add(result)
        if on_result:
            on_result(result, payload)
        if pagination_stop_condition and pagination_stop_condition(result, page_number):
            stop_pagination = True
    return len(results), stop_pagination


def get_results_and_add_to_write_manager(
    url: str,
    headers: dict,
    payload: dict,
    write_manager: gather_batch_write_managers.GatherBatchWriteManager,
    stop_requesting_pages_after_message_result_count: Optional[int] = None,
    logger: None | logging.Logger | logging.LoggerAdapter = None,
    on_result: None | Callable = None,
    pagination_stop_condition: Optional[Callable[[dict, int], bool]] = None,
) -> None:
    """Get results from the Danek API and add them to the write_manager.

    Args:
        url: URL for the Danek API
        headers: Headers for the request
        payload: Payload for the request
        stop_requesting_pages_after_message_result_count: Optional limit to stop requesting pages
            after a certain number of results. If None, all pages will be requested.
        write_manager: Writer to collect the search results.
        logger: Logger to use for logging.
        on_result: Optional callable that gets called for each result as it is scraped.
                   Signature: on_result(result_dict, payload)
        pagination_stop_condition: Optional callable, returns True if pagination should stop.
                           Signature: pagination_stop_condition(result_dict, page_number) -> bool

    Returns:
        Writer with collected search results.
    """
    if logger is None:
        logger = file_logger
    page_count = 0
    scraped_count = 0
    cursor = None

    while True:
        logger.info(f"Requesting page {page_count} for API {url}, payload {payload}")
        page_count += 1
        if cursor:
            payload.update(cursor)
        try:
            results, cursor = make_single_request(url, headers, payload)
        except RuntimeError as exc:
            logger.error(f"Error occurred while scraping. Error message: {str(exc)}")
            write_manager.add_error(
                {
                    "error": str(exc),
                    "url": url,
                    "payload": payload,
                }
            )
            return None

        results_in_page, stop_pagination = _process_page_results(
            results, write_manager, payload, on_result, pagination_stop_condition, page_count
        )
        scraped_count += results_in_page

        logger.info(
            f"Page {page_count - 1} processed: "
            f"results_in_page={results_in_page}, "
            f"total_scraped={scraped_count}, "
            f"has_next_cursor={cursor is not None}, "
            f"next_cursor={cursor}"
        )

        if stop_pagination:
            logger.info("Stopping: pagination_stop_condition returned True")
            break

        if (
            stop_requesting_pages_after_message_result_count
            and scraped_count >= stop_requesting_pages_after_message_result_count
        ):
            logger.info(
                f"Stopping: reached result limit "
                f"({scraped_count} >= {stop_requesting_pages_after_message_result_count})"
            )
            break

        if not cursor:
            logger.info("Stopping: no more pages (cursor is None)")
            break

    logger.info(
        f"Finished scraping query: total_pages={page_count}, total_results={scraped_count}"
    )
    return None


def get_cursor_from_response_json(response_json: dict) -> Optional[dict[str, str]]:
    """Normalize the cursor from Danek API response to a single-key dict.

    Rules:
    - 'end_cursor' may be a dict or stringified JSON → always return as {"end_cursor": str}.
    - 'after_cursor' (Instagram posts) → {"cursor": str} to match request payload key.
    - 'cursor' → {"cursor": str}.
    - 'next_min_child_cursor' → {"max_id": str}.
    - Return None if no cursor exists.
    """
    file_logger.debug(f"Parsing cursor from response keys: {list(response_json.keys())}")
    end_cursor = response_json.get("end_cursor")
    if end_cursor is not None:
        if isinstance(end_cursor, dict):
            # The API expects a stringified json
            end_cursor = json.dumps(end_cursor)
        if not isinstance(end_cursor, str):
            raise RuntimeError(f"end_cursor must be a string/dict/None: {end_cursor}")
        file_logger.info(f"Cursor found: end_cursor={end_cursor[:50]!r}")
        return {"end_cursor": end_cursor}  # Keep stringified json

    # Try after_cursor (used by Instagram posts API response).
    # Keep as "after_cursor" to match the request payload key expected by the API.
    after_cursor = response_json.get("after_cursor")
    if after_cursor is not None:
        file_logger.info(f"Cursor found: after_cursor={after_cursor!r}")
        return {"after_cursor": after_cursor}

    # Try cursor
    cursor = response_json.get("cursor")
    if cursor is not None:
        file_logger.info(f"Cursor found: cursor={cursor!r}")
        return {"cursor": cursor}

    # Try next_min_child_cursor
    max_id = response_json.get("next_min_child_cursor")
    if max_id is not None:
        file_logger.info(f"Cursor found: next_min_child_cursor (mapped to max_id)={max_id!r}")
        return {"max_id": max_id}

    file_logger.info("No cursor found in response — pagination complete.")
    return None
