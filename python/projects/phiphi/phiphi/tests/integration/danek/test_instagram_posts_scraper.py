"""Integration tests for Danek Facebook search API.

This test script has real costs associated with it. It should be run sparingly, used only for the
development of key integration functions, and not as part of the regular test suite.
"""

import json
import logging
from unittest import mock

import pytest

from phiphi import config, utils
from phiphi.pipeline_jobs import dataframe_writers
from phiphi.pipeline_jobs.gathers import gather_batch_write_managers
from phiphi.pipeline_jobs.gathers.danek import instagram_posts_scraper
from phiphi.tests.pipeline_jobs.gathers import example_gathers

utils.init_logging()

logger = logging.getLogger(__name__)


@pytest.mark.danek_integration
def test_get_instagram_posts():
    """Integration test for get_facebook_posts function.

    This test verifies:
    1. The function can make a request to the actual API
    2. Returns results with the expected structure
    3. Handles pagination correctly

    It is also used to log the results of a real api call to the console.
    Use `pytest -rP test_facebook_search_scraper.py` to see the results.
    """
    # Retrieve API token from environment variable
    api_token = config.settings.DANEK_API_TOKENS.get("main")
    # Skip test if no token is available
    if not api_token:
        pytest.skip("No API token provided for Danek Facebook Scraper API")

    gather = example_gathers.danek_instagram_posts_gather_example()
    logger.info("Running get_instagram_posts with gather:")
    logger.info(gather)

    write_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=1,
            job_run_id=1,
            gather_type=gather.child_type,
        ),
        df_writer=dataframe_writers.DummyWriter(),
        # All data in one batch so that we can see the results easily
        max_mb_batch_size=1000000000000,
    )

    # Call the function
    instagram_posts_scraper.scrape_instagram_posts_and_add_to_write_manager(
        gather=gather,
        write_manager=write_manager,
    )

    manager_results = write_manager.complete_write()
    logger.info(manager_results.writer_results)

    assert manager_results.total_items_processed >= 1, "At least one item should be processed"
    assert manager_results.total_batches_processed == 1, "One batch should be processed"
    assert manager_results.error_count == 0, "No errors should be present"
    assert isinstance(manager_results.writer_results, dataframe_writers.DummyWriteResults), (
        "Writer should be a DummyWriteResults"
    )
    batch_data = manager_results.writer_results.dataframe
    assert batch_data.shape[0] == manager_results.total_batches_processed, (
        "Data length should match total batches"
    )

    json_data = json.loads(batch_data.iloc[0]["json_data"])
    for response in json_data:
        # Example of checking first result structure (adjust based on actual API response)
        assert isinstance(response, dict), "Individual responses should be dictionaries"

        # Add more specific checks based on expected result structure

        assert "items" in response, "First response should contain 'items'"
        result = response["items"][0]
        assert isinstance(result, dict), "Individual results should be a dictionary"
        node = result["node"]
        assert isinstance(node, dict), "Individual nodes in a result should be a dictionary"
        expected_keys = ["pk", "id", "user"]
        for key in expected_keys:
            assert key in node, f"Key {key} should be in node"

    logger.info("Scraped data:")
    logger.info(json.dumps(json_data, indent=4))


@pytest.mark.danek_integration
@mock.patch("phiphi.utils.get_danek_api_token", return_value="TestBuildUpInValidApiToken")
def test_get_instagram_posts_error_handling(
    mock_get_danek_api_token,
):
    """Test error handling for get_instagram_posts function.

    Verifies that the function handles invalid parameters gracefully.
    """
    logger.error("Starting to scrape Instagram posts with gather id.")
    gather = example_gathers.danek_instagram_posts_gather_example()
    write_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=1,
            job_run_id=1,
            # To change
            gather_type=gather.child_type,
        ),
        df_writer=dataframe_writers.DummyWriter(),
    )

    # Call the function and check it doesn't raise unhandled exceptions
    try:
        # Call the function
        instagram_posts_scraper.scrape_instagram_posts_and_add_to_write_manager(
            gather=gather,
            write_manager=write_manager,
        )
        manager_results = write_manager.complete_write()

    except Exception as e:
        pytest.fail(f"get_facebook_posts should handle errors gracefully: {e}")

    assert manager_results.total_items_processed == 2, "Only one item should be processed"
    assert manager_results.total_batches_processed == 1, "Only one batch should be processed"
    # logger.info(manager_results.error_count)
    assert manager_results.error_count == 2, "Two error should be present"

    assert isinstance(manager_results.writer_results, dataframe_writers.DummyWriteResults), (
        "Writer should be a DummyWriteResults"
    )
    batch_data = manager_results.writer_results.dataframe
    assert batch_data.shape[0] == manager_results.total_batches_processed, (
        "Data length should match error count"
    )
    json_data = json.loads(str(batch_data.loc[0]["json_data"]))
    assert len(json_data) == manager_results.error_count, "Error count should match error length"
    error_result = json_data[0]
    assert isinstance(error_result, dict), "Error result should be a dictionary"
    assert "error" in error_result, "Error message should be present"
    error = error_result["error"]
    assert "url" in error, "Error URL should be present"
    assert "payload" in error, "Error payload should be present"
    assert "401" in error["error"], "Error message should contain '401'"
