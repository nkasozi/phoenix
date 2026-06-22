"""Unit tests for pipeline_jobs Gather Flow module."""

from unittest.mock import MagicMock, patch

import pytest

import phiphi.tests.pipeline_jobs.gathers.example_gathers as example_gathers
from phiphi.api.projects.gathers.danek_instagram_comments.schemas import (
    DanekInstagramCommentsGatherResponse,
)
from phiphi.api.projects.job_runs import pipeline_job_result_schemas
from phiphi.pipeline_jobs.gathers.flow import (
    aggregate_gather_job_results,
    get_next_gather_flow_params,
)


@patch("phiphi.pipeline_jobs.gathers.flow.selectors.get_post_ids_with_comments")
def test_get_next_gather_returns_comments_gather(mock_get_post_ids):
    """Test that a comments gather is returned when posts have comments to scrape."""
    mock_logger = MagicMock()
    mock_get_post_ids.return_value = ["1", "2", "3"]

    previous = example_gathers.danek_instagram_posts_with_comments_gather_example()

    result = get_next_gather_flow_params(
        root_gather=previous,
        job_run_id=42,
        prefect_logger=mock_logger,
        project_namespace="test_dataset",
        results=[],
        previous_gathers=[previous],
    )

    assert isinstance(result, DanekInstagramCommentsGatherResponse)
    assert result.post_id_list == ["1", "2", "3"]
    assert result.limit_comments_per_post == 20
    assert result.limit_child_comments_per_comment == 0

    mock_get_post_ids.assert_called_once_with(
        bigquery_dataset="test_dataset",
        gather_id=previous.id,
        gather_type=previous.child_type,
    )


@patch("phiphi.pipeline_jobs.gathers.flow.selectors.get_post_ids_with_comments")
def test_get_next_gather_returns_none_when_no_posts_with_comments(mock_get_post_ids):
    """Test that None is returned when post_id_list is empty."""
    mock_logger = MagicMock()
    mock_get_post_ids.return_value = []

    previous = example_gathers.danek_instagram_posts_with_comments_gather_example()

    result = get_next_gather_flow_params(
        root_gather=previous,
        job_run_id=42,
        prefect_logger=mock_logger,
        project_namespace="test_dataset",
        results=[],
        previous_gathers=[previous],
    )

    assert result is None
    mock_logger.info.assert_called()


@patch("phiphi.pipeline_jobs.gathers.flow.selectors.get_post_ids_with_comments")
def test_get_next_gather_returns_none_when_no_comments(mock_get_post_ids):
    """Test that None is returned when scrape_comments_count_per_post is 0."""
    mock_logger = MagicMock()

    previous = example_gathers.danek_instagram_posts_gather_example()

    result = get_next_gather_flow_params(
        root_gather=previous,
        job_run_id=42,
        prefect_logger=mock_logger,
        project_namespace="test_dataset",
        results=[],
        previous_gathers=[previous],
    )

    assert result is None
    mock_get_post_ids.assert_not_called()


@patch("phiphi.pipeline_jobs.gathers.flow.selectors.get_post_ids_with_comments")
def test_get_next_gather_returns_none_for_other_types(mock_get_post_ids):
    """Test that None is returned for non-Instagram-post gather types."""
    mock_logger = MagicMock()

    previous = example_gathers.x_advanced_searches_posts_comments_gather_example()

    result = get_next_gather_flow_params(
        root_gather=previous,
        job_run_id=42,
        prefect_logger=mock_logger,
        project_namespace="test_dataset",
        results=[],
        previous_gathers=[previous],
    )

    assert result is None
    mock_get_post_ids.assert_not_called()


def make_result(
    cost=None,
    result_count=0,
    total=0,
    success=0,
    errors=0,
    estimated=False,
):
    """Helper to create GatherJobResult instances."""
    return pipeline_job_result_schemas.GatherJobResult(
        cost=cost,
        result_count=result_count,
        normalise_total_processed=total,
        normalise_successfully_processed=success,
        normalise_error_count=errors,
        is_cost_estimated=estimated,
    )


def test_aggregate_basic_sum():
    """Test that numeric fields are summed correctly across results."""
    results = [
        make_result(cost=1.5, result_count=10, total=8, success=7, errors=1),
        make_result(cost=2.5, result_count=5, total=5, success=5, errors=0),
    ]

    aggregated = aggregate_gather_job_results(results)

    assert aggregated.cost == 4.0
    assert aggregated.result_count == 15
    assert aggregated.normalise_total_processed == 13
    assert aggregated.normalise_successfully_processed == 12
    assert aggregated.normalise_error_count == 1
    assert aggregated.is_cost_estimated is False


def test_aggregate_with_none_costs():
    """Test that cost is 0.0 if all input costs are None."""
    results = [
        make_result(cost=None, result_count=3),
        make_result(cost=None, result_count=7),
    ]

    aggregated = aggregate_gather_job_results(results)

    assert aggregated.cost == 0.0
    assert aggregated.result_count == 10


def test_aggregate_mixed_costs():
    """Test that cost sums only non-None values."""
    results = [
        make_result(cost=None, result_count=3),
        make_result(cost=2.0, result_count=7),
    ]

    aggregated = aggregate_gather_job_results(results)

    assert aggregated.cost == 2.0
    assert aggregated.result_count == 10


def test_aggregate_single_result():
    """Test aggregation with single result."""
    results = [
        make_result(cost=2.0, result_count=7),
    ]

    aggregated = aggregate_gather_job_results(results)

    assert aggregated.cost == 2.0
    assert aggregated.result_count == 7


def test_aggregate_cost_estimated_flag():
    """Test that is_cost_estimated is True if any result is estimated."""
    results = [
        make_result(cost=1.0, estimated=False),
        make_result(cost=2.0, estimated=True),
    ]

    aggregated = aggregate_gather_job_results(results)

    assert aggregated.is_cost_estimated is True


def test_aggregate_empty_input_raises():
    """Test that an empty input list raises a ValueError."""
    with pytest.raises(ValueError, match="No job results"):
        aggregate_gather_job_results([])
