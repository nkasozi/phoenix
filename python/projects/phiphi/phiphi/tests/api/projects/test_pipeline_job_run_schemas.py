"""Tests for the pipeline job result schemas.

This module contains tests for the PipelineJobResult class and its cost calculation
functionality.
"""

import pytest

from phiphi.api.projects.job_runs import pipeline_job_result_schemas as schemas


@pytest.mark.parametrize(
    "gather_result,classify_result,expected_total",
    [
        # Both results None
        (None, None, 0),
        # Only GatherJobResult present
        (schemas.GatherJobResult(cost=10.5), None, 10.5),
        # Only ClassifyJobResult present
        (None, schemas.ClassifyJobResult(cost=5.25), 5.25),
        # Both results present
        (schemas.GatherJobResult(cost=10.5), schemas.ClassifyJobResult(cost=5.25), 15.75),
        # Both present but with None costs
        (schemas.GatherJobResult(cost=None), schemas.ClassifyJobResult(cost=None), 0),
        # Mixed None and actual costs
        (schemas.GatherJobResult(cost=None), schemas.ClassifyJobResult(cost=5.25), 5.25),
        (schemas.GatherJobResult(cost=10.5), schemas.ClassifyJobResult(cost=None), 10.5),
        # Zero costs
        (schemas.GatherJobResult(cost=0), schemas.ClassifyJobResult(cost=0), 0),
    ],
)
def test_pipeline_job_result_total_cost_calculation(
    gather_result, classify_result, expected_total
):
    """Test that total_cost is correctly calculated for various input combinations."""
    result = schemas.create_result(
        gather_job_result=gather_result,
        classify_job_result=classify_result,
    )
    assert result.total_cost == expected_total


def test_pipeline_job_result_can_initialised():
    """Test that allows set total_cost."""
    result = schemas.PipelineJobResult(
        total_cost=10.0,
        gather_job_result=None,
        classify_job_result=None,
    )
    assert result.total_cost == 10.0


def test_pipeline_job_result_defaults():
    """Test that allows set total_cost."""
    result = schemas.PipelineJobResult()
    assert result.total_cost == 0.0
    assert result.gather_job_result is None
    assert result.classify_job_result is None


def test_pipeline_job_result_with_full_data():
    """Test PipelineJobResult with complete data in sub-results."""
    gather_result = schemas.GatherJobResult(
        cost=10.5,
        result_count=100,
        normalise_error_count=5,
    )
    classify_result = schemas.ClassifyJobResult(
        cost=5.25,
        successfully_classified_count=95,
        error_count=5,
    )

    result = schemas.PipelineJobResult(
        total_cost=100.0,
        gather_job_result=gather_result,
        classify_job_result=classify_result,
    )

    # Have to set the total cost manually as the sub-results have costs.
    assert result.total_cost == 100.0
    assert result.gather_job_result == gather_result
    assert result.classify_job_result == classify_result


def test_is_total_cost_estimated_processing():
    """Test that is_total_cost_estimated defaults to False."""
    # Test direct initialization
    result = schemas.PipelineJobResult()
    assert result.is_total_cost_estimated is False

    # Test via create_result with no gather result
    result = schemas.create_result()
    assert result.is_total_cost_estimated is False

    # Test via create_result with gather result that has is_total_cost_estimated=False
    gather_result = schemas.GatherJobResult(cost=10.0, is_cost_estimated=False)
    result = schemas.create_result(gather_job_result=gather_result)
    assert result.is_total_cost_estimated is False

    # Test via create_result with gather result that has is_total_cost_estimated=True
    gather_result = schemas.GatherJobResult(cost=10.0, is_cost_estimated=True)
    result = schemas.create_result(gather_job_result=gather_result)
    assert result.is_total_cost_estimated is True
