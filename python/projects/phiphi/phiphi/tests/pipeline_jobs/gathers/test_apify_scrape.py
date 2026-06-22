"""Tests for Apify gathers."""

import json
import logging

import pytest

from phiphi import utils
from phiphi.api.projects.gathers import schemas as gathers_schemas
from phiphi.pipeline_jobs import dataframe_writers
from phiphi.pipeline_jobs.gathers import apify, gather_batch_write_managers
from phiphi.pipeline_jobs.gathers import types as gather_types
from phiphi.tests.pipeline_jobs.gathers import example_gathers

utils.init_logging()

logger = logging.getLogger(__name__)


def manual_test_apify_scrape_and_batch_download():
    """Manually test the apify_scrape_and_batch_download_results flow.

    WARNING: this will incur costs on Apify (unless use have configured the mock settings).

    To use this test:
    - `export APIFY_API_KEYS='{"main":"<token>"}'` with a valid Apify token in (the docker) env
    - change `gather` to the corresponding desired Apify actor to test

    To use with docker environment:
    - check `python/projects/phiphi/docker_env.dev` for configuration.
        If you want to make an actual call to Apify, you will need to set `USE_MOCK_APIFY` to
        `False`, with `export USE_MOCK_APIFY=false`.
    - set up the prefect environment see phiphi/README.md
    - in terminal `make up`
    - in new terminal `make bash_in_api`
    - Run the function:
    ```
    python -c \
        "from phiphi.tests.pipeline_jobs.gathers import test_apify_scrape; \
        test_apify_scrape.manual_test_apify_scrape_and_batch_download()"
    ```
    - Data that has been scraped will be printed to the console
    """
    gather = example_gathers.x_simple_searches_posts_comments_gather_example()
    logger.info("Running apify_scrape_and_batch_download_results with gather:")
    logger.info(gather)
    writer_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=1, job_run_id=1, gather_type=gather.child_type
        ),
        df_writer=dataframe_writers.DummyWriter(),
        # All data in one batch so that we can see the results easily
        max_mb_batch_size=1000000000000,
    )
    costs = apify.scrape.apify_scrape_and_add_to_write_manager(
        gather=gather,
        write_manager=writer_manager,
        logger=logger,
    )
    manager_results = writer_manager.complete_write()
    logger.info("Completed Apify scrape.")
    logger.info("Total cost: %s", costs)
    logger.info(manager_results)
    assert isinstance(manager_results.writer_results, dataframe_writers.DummyWriteResults), (
        "Writer should be a DummyWriteResults"
    )
    batch_data = manager_results.writer_results.dataframe

    json_data = json.loads(str(batch_data.loc[0]["json_data"]))

    logger.info("Scraped data:")
    logger.info(json.dumps(json_data, indent=4))


@pytest.mark.patch_settings(
    {
        "USE_MOCK_APIFY": True,
        "APIFY_API_KEYS": {"main": "dummy_key"},
    }
)
def test_apify_scrape_and_add_to_write_manager(
    patch_settings, mocker, facebook_posts_gather_fixture
):
    """Test apify_scrape_and_batch_download_results with mocked out Apify function."""
    mock_cost = gather_types.ScrapeCost(cost=1.0, is_cost_estimated=False)
    mocker.patch.object(apify.scrape, "MOCK_APIFY_SCRAPE_COST", mock_cost)

    writer_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=1,
            job_run_id=1,
            gather_type=facebook_posts_gather_fixture.child_type,
        ),
        df_writer=dataframe_writers.DummyWriter(),
        # Using a small batch size to force multiple batches for testing
        max_mb_batch_size=0.01,
    )
    returned_costs = apify.scrape.apify_scrape_and_add_to_write_manager(
        gather=facebook_posts_gather_fixture,
        write_manager=writer_manager,
        logger=logger,
    )

    assert returned_costs.cost == 1.0
    assert returned_costs.is_cost_estimated is False

    manager_results = writer_manager.complete_write()
    assert manager_results.total_items_processed == 9
    assert manager_results.total_batches_processed == 3
    assert manager_results.error_count == 0
    assert isinstance(manager_results.writer_results, dataframe_writers.DummyWriteResults), (
        "Writer should be a DummyWriteResults"
    )

    read_df = manager_results.writer_results.dataframe
    assert not read_df.empty
    assert "gather_id" in read_df.columns
    assert read_df["gather_id"].iloc[0] == 1
    assert "json_data" in read_df.columns
    assert json.loads(read_df["json_data"].iloc[0])  # Ensure JSON data is valid
    assert read_df["batch_id"].iloc[0] == 0
    assert read_df["batch_id"].iloc[2] == 2
    assert len(read_df) == 3  # Note this depends on the sample data


@pytest.mark.patch_settings(
    {
        "USE_MOCK_APIFY": True,
        "APIFY_API_KEYS": {"main": "dummy_key"},
    }
)
def test_apify_scrape_batched_and_add_to_write_manager(mocker, facebook_posts_gather_fixture):
    """Batches the target list attr, calls the single-run helper per batch, and sums costs."""
    # Capture the slices that flow through to the single-run helper
    seen_slices: list[list[str]] = []
    fixed_cost_per_batch = 1.5

    def fake_single_run(gather, write_manager, logger=None):
        # Record the current batch's slice
        seen_slices.append(gather.account_url_list.copy())
        # Return a deterministic cost to test summing behavior
        return gather_types.ScrapeCost(cost=fixed_cost_per_batch, is_cost_estimated=False)

    mocker.patch.object(
        apify.scrape, "apify_scrape_and_add_to_write_manager", side_effect=fake_single_run
    )

    # The write_manager is unused - pass a simple DummyWriter-backed manager anyway
    writer_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=-1,
            job_run_id=-2,
            gather_type=gathers_schemas.ChildTypeName.apify_facebook_posts,
        ),
        df_writer=dataframe_writers.DummyWriter(),
        max_mb_batch_size=999999,  # irrelevant to this test;
    )

    queries = ["q1", "q2", "q3", "q4", "q5"]
    extended_gather = facebook_posts_gather_fixture.model_copy(
        update={"account_url_list": queries}
    )

    result = apify.scrape.apify_scrape_batched_and_add_to_write_manager(
        gather=extended_gather,
        write_manager=writer_manager,
        batch_attr_name="account_url_list",
        batch_size=2,
        logger=logger,
    )

    # Assert cost is sum of per-batch costs
    assert result.cost == fixed_cost_per_batch * 3
    assert result.is_cost_estimated is False

    # Assert the helper was invoked with the correct slices in-order
    assert seen_slices == [
        ["q1", "q2"],
        ["q3", "q4"],
        ["q5"],
    ]


@pytest.mark.patch_settings(
    {
        "USE_MOCK_APIFY": True,
        "APIFY_API_KEYS": {"main": "dummy_key"},
    }
)
def test_apify_scrape_batched_and_add_to_write_manager_estimated_costs(
    mocker, facebook_posts_gather_fixture
):
    """Test that is_cost_estimated=True propagates when any batch has estimated costs."""
    # Capture the slices that flow through to the single-run helper
    seen_slices: list[list[str]] = []
    fixed_cost_per_batch = 2.0
    batch_call_count = 0

    def fake_single_run(gather, write_manager, logger=None):
        nonlocal batch_call_count
        # Record the current batch's slice
        seen_slices.append(gather.account_url_list.copy())
        batch_call_count += 1
        # Second batch (batch_call_count == 2) will have is_cost_estimated=True
        is_estimated = batch_call_count == 2
        return gather_types.ScrapeCost(cost=fixed_cost_per_batch, is_cost_estimated=is_estimated)

    mocker.patch.object(
        apify.scrape, "apify_scrape_and_add_to_write_manager", side_effect=fake_single_run
    )

    # The write_manager is unused - pass a simple DummyWriter-backed manager anyway
    writer_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=-1,
            job_run_id=-2,
            gather_type=gathers_schemas.ChildTypeName.apify_facebook_posts,
        ),
        df_writer=dataframe_writers.DummyWriter(),
        max_mb_batch_size=999999,  # irrelevant to this test;
    )

    queries = ["q1", "q2", "q3", "q4", "q5"]
    extended_gather = facebook_posts_gather_fixture.model_copy(
        update={"account_url_list": queries}
    )

    result = apify.scrape.apify_scrape_batched_and_add_to_write_manager(
        gather=extended_gather,
        write_manager=writer_manager,
        batch_attr_name="account_url_list",
        batch_size=2,
        logger=logger,
    )

    # Assert cost is sum of per-batch costs (3 batches)
    assert result.cost == fixed_cost_per_batch * 3
    # Assert that is_cost_estimated is True because one batch had it as True
    assert result.is_cost_estimated is True

    # Assert the helper was invoked with the correct slices in-order
    assert seen_slices == [
        ["q1", "q2"],
        ["q3", "q4"],
        ["q5"],
    ]


def test_compute_cost_from_run_info_with_valid_cost(facebook_posts_gather_fixture):
    """Test compute_cost_from_run_info when usageTotalUsd is present."""
    run_info = {
        "usageTotalUsd": 1.23,
        "actId": "test_actor_id",
        "id": "test_run_id",
    }

    result = apify.scrape.compute_cost_from_run_info(
        run_info=run_info,
        gather=facebook_posts_gather_fixture,
        logger=logger,
    )

    assert result.cost == 1.23
    assert result.is_cost_estimated is False


def test_compute_cost_from_run_info_with_zero_cost(facebook_posts_gather_fixture):
    """Test compute_cost_from_run_info when usageTotalUsd is 0."""
    run_info = {
        "usageTotalUsd": 0.0,
        "actId": "test_actor_id",
        "id": "test_run_id",
    }

    result = apify.scrape.compute_cost_from_run_info(
        run_info=run_info,
        gather=facebook_posts_gather_fixture,
        logger=logger,
    )

    assert result.cost == 0.0
    assert result.is_cost_estimated is False


def test_compute_cost_from_run_info_missing_usage_total_usd(facebook_posts_gather_fixture, mocker):
    """Test compute_cost_from_run_info when usageTotalUsd is missing."""
    run_info = {
        "actId": "test_actor_id",
        "id": "test_run_id",
    }

    # Mock prefect.events.emit_event to verify it's called
    mock_emit_event = mocker.patch("prefect.events.emit_event")

    result = apify.scrape.compute_cost_from_run_info(
        run_info=run_info,
        gather=facebook_posts_gather_fixture,
        logger=logger,
    )

    assert result.cost == facebook_posts_gather_fixture.job_run_resource_estimate.max_total_cost
    assert result.is_cost_estimated is True

    # Verify that an event was emitted
    mock_emit_event.assert_called_once()
    call_args = mock_emit_event.call_args
    assert call_args[1]["event"] == "phoenix.error.apify.malformed_run_info"
    assert "phoenix.project.id" in call_args[1]["resource"]
    assert "phoenix.gather.id" in call_args[1]["resource"]


def test_compute_cost_from_run_info_missing_usage_with_missing_actor_id(
    facebook_posts_gather_fixture, mocker
):
    """Test compute_cost_from_run_info when usageTotalUsd and actId are missing."""
    run_info = {
        "id": "test_run_id",
    }

    # Mock prefect.events.emit_event to verify it's called with 'not_found' for actId
    mock_emit_event = mocker.patch("prefect.events.emit_event")

    result = apify.scrape.compute_cost_from_run_info(
        run_info=run_info,
        gather=facebook_posts_gather_fixture,
        logger=logger,
    )

    assert result.cost == facebook_posts_gather_fixture.job_run_resource_estimate.max_total_cost
    assert result.is_cost_estimated is True

    # Verify that the resource contains 'not_found' for missing actId
    mock_emit_event.assert_called_once()
    call_args = mock_emit_event.call_args
    resource = call_args[1]["resource"]
    assert resource["phoenix.apify.actor.id"] == "not_found"
    assert resource["phoenix.apify.run.id"] == "test_run_id"


def test_compute_cost_from_run_info_with_minimum_charge_applied(facebook_posts_gather_fixture):
    """Test compute_cost_from_run_info when usage is below minimum charge."""
    run_info = {
        "usageTotalUsd": 0.05,
        "pricingInfo": {
            "minimalMaxTotalChargeUsd": 0.10,
        },
        "actId": "test_actor_id",
        "id": "test_run_id",
    }

    result = apify.scrape.compute_cost_from_run_info(
        run_info=run_info,
        gather=facebook_posts_gather_fixture,
        logger=logger,
    )

    # Should return the minimum charge when usage is lower
    assert result.cost == 0.10
    assert result.is_cost_estimated is False


def test_compute_cost_from_run_info_with_minimum_charge_not_applied(
    facebook_posts_gather_fixture,
):
    """Test compute_cost_from_run_info when usage is above minimum charge."""
    run_info = {
        "usageTotalUsd": 0.50,
        "pricingInfo": {
            "minimalMaxTotalChargeUsd": 0.10,
        },
        "actId": "test_actor_id",
        "id": "test_run_id",
    }

    result = apify.scrape.compute_cost_from_run_info(
        run_info=run_info,
        gather=facebook_posts_gather_fixture,
        logger=logger,
    )

    # Should return the actual usage when it's higher than minimum
    assert result.cost == 0.50
    assert result.is_cost_estimated is False


def test_compute_cost_from_run_info_without_pricing_info(facebook_posts_gather_fixture):
    """Test compute_cost_from_run_info when pricingInfo is not present."""
    run_info = {
        "usageTotalUsd": 0.25,
        "actId": "test_actor_id",
        "id": "test_run_id",
    }

    result = apify.scrape.compute_cost_from_run_info(
        run_info=run_info,
        gather=facebook_posts_gather_fixture,
        logger=logger,
    )

    # Should return the actual usage when no pricing info is present
    assert result.cost == 0.25
    assert result.is_cost_estimated is False


def test_compute_cost_from_run_info_with_empty_pricing_info(facebook_posts_gather_fixture):
    """Test compute_cost_from_run_info when pricingInfo is empty."""
    run_info = {
        "usageTotalUsd": 0.25,
        "pricingInfo": {},
        "actId": "test_actor_id",
        "id": "test_run_id",
    }

    result = apify.scrape.compute_cost_from_run_info(
        run_info=run_info,
        gather=facebook_posts_gather_fixture,
        logger=logger,
    )

    # Should return the actual usage when pricing info doesn't contain minimalMaxTotalChargeUsd
    assert result.cost == 0.25
    assert result.is_cost_estimated is False


@pytest.mark.patch_settings(
    {
        "USE_MOCK_APIFY": True,
        "APIFY_API_KEYS": {"main": "dummy_key"},
    }
)
def test_apify_scrape_processes_batches_correctly(
    patch_settings, mocker, facebook_posts_gather_fixture
):
    """Test that apify_scrape correctly processes datasets larger than the batch size.

    This test verifies:
    1. The batch iterator yields multiple batches when dataset size > batch_size
    2. All items are processed across batches
    3. The write_manager receives all items in the correct order
    """
    # Create a large mock dataset (25 items)
    large_dataset = [{"id": i, "data": f"item_{i}"} for i in range(25)]

    # Mock the load_sample_raw_data to return our large dataset
    mocker.patch(
        "phiphi.pipeline_jobs.gathers.utils.load_sample_raw_data",
        return_value=large_dataset,
    )

    # Use a small batch size (10) to force multiple batches
    apify_dataset_batch_size = 10

    writer_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=1,
            job_run_id=1,
            gather_type=facebook_posts_gather_fixture.child_type,
        ),
        df_writer=dataframe_writers.DummyWriter(),
        # Large enough to hold all items in one batch
        max_mb_batch_size=1000,
    )

    # Track items added to verify they're processed in order
    added_items = []
    original_add = writer_manager.add

    def track_add(item):
        added_items.append(item)
        return original_add(item)

    # Use mocker to patch the add method
    mocker.patch.object(writer_manager, "add", side_effect=track_add)

    returned_costs = apify.scrape.apify_scrape_and_add_to_write_manager(
        gather=facebook_posts_gather_fixture,
        write_manager=writer_manager,
        logger=logger,
        apify_dataset_batch_size=apify_dataset_batch_size,
    )

    assert returned_costs.cost == 0.0
    assert returned_costs.is_cost_estimated is False

    # Verify all items were processed
    assert len(added_items) == 25
    assert added_items == large_dataset

    # Verify the manager processed them correctly
    manager_results = writer_manager.complete_write()
    assert manager_results.total_items_processed == 25

    # Verify data integrity
    assert isinstance(manager_results.writer_results, dataframe_writers.DummyWriteResults)
    read_df = manager_results.writer_results.dataframe
    assert not read_df.empty

    # Parse the JSON data and verify all items are present
    json_data = json.loads(read_df["json_data"].iloc[0])
    assert len(json_data) == 25
    assert json_data == large_dataset
