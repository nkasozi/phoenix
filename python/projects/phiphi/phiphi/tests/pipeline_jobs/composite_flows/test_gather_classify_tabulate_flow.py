"""Test gather_classify_tabulate_flow.py."""

from unittest import mock

import pytest

from phiphi.pipeline_jobs.composite_flows import gather_classify_tabulate_flow
from phiphi.pipeline_jobs.gathers import types as gather_types
from phiphi.tests.pipeline_jobs.gathers import example_gathers

PATCH_SETTINGS = {
    "USE_MOCK_APIFY": True,
    "USE_MOCK_DANEK": True,
    # We are not using the mock Big Query as we are going to use a mock patch
    "USE_MOCK_BQ": False,
    "APIFY_API_KEYS": {"main": "dummy_key"},
}


@mock.patch("phiphi.pipeline_jobs.gathers.apify.scrape.mock_apify_scrape")
@mock.patch("phiphi.pipeline_jobs.classify.flow.classify_flow")
@mock.patch("google.cloud.bigquery.Client")
@mock.patch("pandas_gbq.to_gbq")
@mock.patch("pandas_gbq.read_gbq")
@pytest.mark.patch_settings(PATCH_SETTINGS)
@pytest.mark.asyncio
async def test_gather_classify_tabulate_flow(
    mock_read_gbq,
    mock_to_gbq,
    mock_bigquery_client,
    mock_classify_flow,
    mock_apify_scrape,
    patch_settings,
    prefect_test_fixture,
):
    """Test gather_classify_tabulate_flow runs correctly."""
    gather = example_gathers.facebook_comments_gather_example()
    mock_cost = gather_types.ScrapeCost(cost=1000.0, is_cost_estimated=True)
    mock_data = [{"test": "test"}] * 5
    total_items = len(mock_data)
    mock_apify_scrape.return_value = (mock_data, None, mock_cost)
    pipeline_job_result = await gather_classify_tabulate_flow.gather_classify_tabulate_flow(
        project_id=5,
        job_source_id=5,
        job_run_id=5,
        project_namespace="project_id5",
        gather_dict=gather.model_dump(),
        gather_child_type=gather.child_type,
        classifiers_dict_list=[],
        active_classifiers_versions=[],
        max_mb_batch_size=1,
    )
    mock_apify_scrape.assert_called_once()
    assert mock_bigquery_client.call_count == 7
    # BigQueryDataFrameWriter uses pandas_gbq.to_gbq and should have been called once
    mock_to_gbq.assert_called_once()
    mock_read_gbq.assert_called_once()
    mock_classify_flow.assert_not_called()
    assert pipeline_job_result.total_cost == mock_cost.cost
    assert pipeline_job_result.is_total_cost_estimated == mock_cost.is_cost_estimated
    assert pipeline_job_result.gather_job_result is not None
    assert pipeline_job_result.gather_job_result.cost == mock_cost.cost
    assert pipeline_job_result.gather_job_result.result_count == total_items


@mock.patch("phiphi.pipeline_jobs.gathers.danek.scrape.get_mock_danek_items")
@mock.patch("phiphi.pipeline_jobs.classify.flow.classify_flow")
@mock.patch("google.cloud.bigquery.Client")
@mock.patch("pandas_gbq.to_gbq")
@mock.patch("pandas_gbq.read_gbq")
@pytest.mark.patch_settings(PATCH_SETTINGS)
@pytest.mark.asyncio
async def test_gather_classify_tabulate_flow_with_danek(
    mock_read_gbq,
    mock_to_gbq,
    mock_bigquery_client,
    mock_classify_flow,
    mock_get_danek_items,
    patch_settings,
    prefect_test_fixture,
):
    """Test gather_classify_tabulate_flow runs correctly for danek_facebook_searches_posts."""
    gather = example_gathers.danek_facebook_searches_posts_gather_example()
    mock_data = [{"test": "test"}] * 5
    total_items = len(mock_data)
    # Uses the default cost of 1.2 per 1000 items
    total_cost = total_items / 1000 * 1.2
    mock_cost = gather_types.ScrapeCost(cost=total_cost, is_cost_estimated=False)
    mock_get_danek_items.return_value = mock_data
    pipeline_job_result = await gather_classify_tabulate_flow.gather_classify_tabulate_flow(
        project_id=5,
        job_source_id=5,
        job_run_id=5,
        project_namespace="project_id5",
        gather_dict=gather.model_dump(),
        gather_child_type=gather.child_type,
        classifiers_dict_list=[],
        active_classifiers_versions=[],
        max_mb_batch_size=1,
    )
    mock_get_danek_items.assert_called_once_with(gather.child_type)
    assert mock_bigquery_client.call_count == 7
    # BigQueryDataFrameWriter uses pandas_gbq.to_gbq and should have been called once
    mock_to_gbq.assert_called_once()
    mock_read_gbq.assert_called_once()
    mock_classify_flow.assert_not_called()
    assert pipeline_job_result.total_cost == total_cost
    assert pipeline_job_result.is_total_cost_estimated == mock_cost.is_cost_estimated
    assert pipeline_job_result.gather_job_result is not None
    assert pipeline_job_result.gather_job_result.cost == total_cost
    assert pipeline_job_result.gather_job_result.result_count == total_items


@mock.patch("phiphi.pipeline_jobs.gathers.apify.scrape.mock_apify_scrape")
@mock.patch("phiphi.pipeline_jobs.classify.flow.classify_flow")
@mock.patch("google.cloud.bigquery.Client")
@mock.patch("pandas_gbq.to_gbq")
@mock.patch("pandas_gbq.read_gbq")
@pytest.mark.patch_settings(PATCH_SETTINGS)
@pytest.mark.asyncio
async def test_gather_classify_tabulate_flow_exception_propagate(
    mock_read_gbq,
    mock_to_gbq,
    mock_bigquery_client,
    mock_classify_flow,
    mock_apify_scrape,
    patch_settings,
    prefect_test_fixture,
):
    """Test subflow exceptions are propagated in gather_classify_tabulate_flow."""
    gather = example_gathers.facebook_comments_gather_example()
    mock_read_gbq.side_effect = Exception("Test")
    with pytest.raises(Exception):
        await gather_classify_tabulate_flow.gather_classify_tabulate_flow(
            project_id=5,
            job_source_id=5,
            job_run_id=5,
            project_namespace="project_id5",
            gather_dict=gather.model_dump(),
            gather_child_type=gather.child_type,
            classifiers_dict_list=[],
            active_classifiers_versions=[],
            max_mb_batch_size=1,
        )
        mock_apify_scrape.assert_called_once()
        mock_bigquery_client.assert_not_called()
        mock_to_gbq.assert_not_called()
        mock_classify_flow.assert_not_called()


@mock.patch("phiphi.pipeline_jobs.gathers.apify.scrape.mock_apify_scrape")
@mock.patch("phiphi.pipeline_jobs.classify.flow.classify_flow", new_callable=mock.AsyncMock)
@mock.patch("google.cloud.bigquery.Client")
@mock.patch("pandas_gbq.to_gbq")
@mock.patch("pandas_gbq.read_gbq")
@pytest.mark.patch_settings(PATCH_SETTINGS)
@pytest.mark.asyncio
async def test_gather_classify_tabulate_flow_with_classify(
    mock_read_gbq,
    mock_to_gbq,
    mock_bigquery_client,
    mock_classify_flow,
    mock_apify_scrape,
    patch_settings,
    prefect_test_fixture,
):
    """Test gather_classify_tabulate_flow."""
    gather = example_gathers.facebook_comments_gather_example()
    classify_dict = {"check": "check"}
    active_classifiers_versions = [(1, 1)]
    total_cost = 1000.00
    mock_cost = gather_types.ScrapeCost(cost=total_cost, is_cost_estimated=True)
    mock_data = [{"test": "test"}] * 5
    mock_apify_scrape.return_value = (mock_data, None, mock_cost)
    # Due to prefect doing some magic with flows that return None we are not testing the return
    # value.
    await gather_classify_tabulate_flow.gather_classify_tabulate_flow(
        project_id=5,
        job_source_id=5,
        job_run_id=5,
        project_namespace="project_id5",
        gather_dict=gather.model_dump(),
        gather_child_type=gather.child_type,
        classifiers_dict_list=[classify_dict, classify_dict],
        active_classifiers_versions=active_classifiers_versions,
        max_mb_batch_size=1,
    )
    mock_apify_scrape.assert_called_once()
    assert mock_classify_flow.call_count == 2
    assert mock_bigquery_client.call_count == 7
    mock_to_gbq.assert_called_once()
    mock_read_gbq.assert_called_once()


@mock.patch("phiphi.pipeline_jobs.gathers.apify.scrape.mock_apify_scrape")
@mock.patch("phiphi.pipeline_jobs.classify.flow.classify_flow", new_callable=mock.AsyncMock)
@mock.patch("google.cloud.bigquery.Client")
@mock.patch("pandas_gbq.to_gbq")
@mock.patch("pandas_gbq.read_gbq")
@pytest.mark.patch_settings(PATCH_SETTINGS)
@pytest.mark.asyncio
async def test_gather_classify_tabulate_flow_with_classify_exception(
    mock_read_gbq,
    mock_to_gbq,
    mock_bigquery_client,
    mock_classify_flow,
    mock_apify_scrape,
    patch_settings,
    prefect_test_fixture,
):
    """Test gather_classify_tabulate_flow.

    Currently we do not raise the exception from classify_flow.
    """
    gather = example_gathers.facebook_comments_gather_example()
    classify_dict = {"check": "check"}
    active_classifiers_versions = [(1, 1)]
    mock_classify_flow.side_effect = Exception("Test")
    total_cost = 1000.00
    mock_cost = gather_types.ScrapeCost(cost=total_cost, is_cost_estimated=True)
    mock_data = [{"test": "test"}] * 5
    mock_apify_scrape.return_value = (mock_data, None, mock_cost)
    # Due to prefect doing some magic with flows that return None we are not testing the return
    # value.
    await gather_classify_tabulate_flow.gather_classify_tabulate_flow(
        project_id=5,
        job_source_id=5,
        job_run_id=5,
        project_namespace="project_id5",
        gather_dict=gather.model_dump(),
        gather_child_type=gather.child_type,
        classifiers_dict_list=[classify_dict, classify_dict],
        active_classifiers_versions=active_classifiers_versions,
        max_mb_batch_size=1,
    )
    mock_apify_scrape.assert_called_once()
    assert mock_classify_flow.call_count == 2
    assert mock_bigquery_client.call_count == 7
    mock_to_gbq.assert_called_once()
    mock_read_gbq.assert_called_once()
