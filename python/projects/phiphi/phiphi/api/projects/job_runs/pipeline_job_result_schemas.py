"""The schemas for the pipeline jobs results.

This is in `job_runs` as it is the main interface between pipeline jobs and flow_runner_flow. It
also follows the convention of having schemas defined in `phiphi.api` that are used in
`phiphi.pipeline_jobs`.
"""

import dataclasses
from typing import Optional


@dataclasses.dataclass
class GatherJobResult:
    """Pipeline job result for gather."""

    cost: Optional[float] = None
    result_count: int = 0
    normalise_total_processed: int = 0
    normalise_successfully_processed: int = 0
    normalise_error_count: int = 0
    is_cost_estimated: bool = False


@dataclasses.dataclass
class ClassifyJobResult:
    """Pipeline job result for classify."""

    cost: Optional[float] = None
    successfully_classified_count: int = 0
    error_count: int = 0


@dataclasses.dataclass
class PipelineJobResult:
    """Pipeline job result that aggregates results from gather and classify jobs.

    Because this is will be a persist result from Prefect it is important not to add any complex
    functionality so that when Prefect gets the result (stored as Pickle) it can be loaded without
    any issues.

    Use `create_result` to create an instance of this class from the sub-results.

    Attributes:
        total_cost: The computed total cost of gather and classify operations.
        gather_job_result: Results from the gather operation.
        classify_job_result: Results from the classify operation.
    """

    total_cost: float = dataclasses.field(default=0.0)
    is_total_cost_estimated: bool = False
    gather_job_result: Optional[GatherJobResult] = None
    classify_job_result: Optional[ClassifyJobResult] = None


def create_result(
    gather_job_result: Optional[GatherJobResult] = None,
    classify_job_result: Optional[ClassifyJobResult] = None,
) -> PipelineJobResult:
    """Create the pipeline job result.

    Returns:
        PipelineJobResult: The pipeline job result.
    """
    gather_cost = (
        gather_job_result.cost
        if gather_job_result is not None and gather_job_result.cost is not None
        else 0
    )

    classify_cost = (
        classify_job_result.cost
        if classify_job_result is not None and classify_job_result.cost is not None
        else 0
    )

    total_cost = gather_cost + classify_cost
    is_total_cost_estimated = gather_job_result.is_cost_estimated if gather_job_result else False
    return PipelineJobResult(
        gather_job_result=gather_job_result,
        classify_job_result=classify_job_result,
        total_cost=total_cost,
        is_total_cost_estimated=is_total_cost_estimated,
    )
