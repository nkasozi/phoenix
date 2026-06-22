"""Schemas for manual_upload.

Manual uploads use form data (rather than JSON) for the POST (create) request because they require
a file to be uploaded. Therefore, only no create schema is needed. The POST (create) definition
will be added in the route. Furthermore, a manual upload cannot be updated, as the gather run is
started on POST/create.
"""

from typing import Any

import pydantic

from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.api.projects.job_runs import schemas as job_runs_schemas


class ManualUploadGatherResponse(gather_schemas.GatherChildResponseBase):
    """Manual upload gather response schema."""

    file_url: str
    uploaded_file_name: str
    file_size: int
    file_row_count: int

    def serialize_to_apify_input(self) -> dict[str, Any]:
        """Serialize to Apify input.

        Manual upload does not have Apify input.
        """
        raise AttributeError

    # Both the property and computed_field decorators are used other wise mypy thinks that the
    # property is a function
    # Mypy doesn't allow both property and computed_field decorators, hence the ignore
    @pydantic.computed_field  # type: ignore[prop-decorator]
    @property
    def job_run_resource_estimate(self) -> job_runs_schemas.JobRunResourceEstimate:
        """Calculate the resource estimate for the job run."""
        return job_runs_schemas.JobRunResourceEstimate(
            max_total_cost=0,
            # This is temporary until we persist the length of the file that is uploaded in to
            # the orm
            max_gather_result_count=0,
        )
