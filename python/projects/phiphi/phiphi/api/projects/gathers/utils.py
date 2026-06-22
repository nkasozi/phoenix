"""Utils for the gather."""

import datetime
from typing import Any, Callable, Optional

import pydantic
from dateutil import parser

from phiphi import config
from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.job_runs import schemas as job_runs_schemas


def validate_both_not_set(attribute_2: str) -> Callable[[Any, Any, pydantic.ValidationInfo], Any]:
    """Utility function to validate both attributes are not set.

    For example, if attribute_1 is set, the attribute_2 should be None.

    This would be added to a pydantic model like this:
    ```
    _validate_dependency_<attribute_1> = pydantic.field_validator(
        "<attribute_1>"
    )(utils.validate_dependency("<attribute_2>"))
    ```

    Args:
        attribute_2 (str): The attribute that should be None.
    """

    def fn(cls: Any, v: Any, info: pydantic.ValidationInfo) -> Any:
        if v is not None and info.data[attribute_2] is not None:
            raise ValueError(
                f"{info.field_name} can only be set if {attribute_2} is not set (None)"
            )

        return v

    return fn


def calculate_job_run_resource_estimate_from_result_count(
    max_gather_result_count: int, mean_cost_per_100k_results: float | None
) -> job_runs_schemas.JobRunResourceEstimate:
    """Compute the job run resource estimate using result count and expected cost per 100k results.

    Used as a generic way to estimate the cost of a gather based on the number of results.

    If no mean_cost_per_100k_results is provided, the default estimate value is used.

    Args:
        max_gather_result_count: The maximum number of results expected from the gather.
        mean_cost_per_100k_results: The expected cost per 100k results.

    Returns:
        JobRunResourceEstimate: The resource estimate.
    """
    if mean_cost_per_100k_results is not None:
        max_total_cost = max_gather_result_count * mean_cost_per_100k_results / 100_000
    else:
        max_total_cost = job_runs_schemas.ESTIMATE_DEFAULT

    return job_runs_schemas.JobRunResourceEstimate(
        max_total_cost=max_total_cost,
        max_gather_result_count=max_gather_result_count,
    )


def get_mean_cost_per_100k_results(
    child_type: gather_schemas.ChildTypeName,
) -> float | None:
    """Get the mean cost per 100k results for child type.

    Args:
        child_type (gather_schemas.ChildTypeName): The child type.

    Returns:
        float | None: The mean cost per 100k results or None if not found.
    """
    return config.settings.MEAN_COST_PER_100K_RESULTS_DICT.get(child_type.value, None)


def parse_datetime_string(input_value: str) -> datetime.datetime:
    """Parse a datetime string."""
    date_obj = parser.parse(input_value)
    if date_obj.tzinfo is None:
        date_obj = date_obj.replace(tzinfo=datetime.timezone.utc)
    else:
        # Convert to UTC if it has a different timezone
        date_obj = date_obj.astimezone(datetime.timezone.utc)
    return date_obj


def validate_and_normalise_datetime(
    v: Optional[str], utc_as_z: bool = False, **kwargs: Any
) -> Optional[str]:
    """Validate and normalise the date string.

    Apify facebook has updated the accepted date formats to only include ISO 8601 format.
    kwargs are needed for the pydantic extra args.
    """
    if v is None:
        return v
    try:
        dt_string = parse_datetime_string(v).isoformat()
        if utc_as_z:
            return dt_string.replace("+00:00", "Z")
        return dt_string
    except ValueError:
        raise ValueError(
            "Datetime cannot be processed."
            f" Expected string containing a date/time stamp but got {v}"
        )


def get_danek_costs_per_100k(gather_child_type: gather_schemas.ChildTypeName) -> float:
    """Get the cost for the number of results."""
    if gather_child_type not in config.settings.DANEK_COST_PER_100K_RESULTS_DICT:
        raise ValueError(f"DANEK_COST_PER_100K_RESULTS_DICT does not contain {gather_child_type}")

    return config.settings.DANEK_COST_PER_100K_RESULTS_DICT[gather_child_type]
