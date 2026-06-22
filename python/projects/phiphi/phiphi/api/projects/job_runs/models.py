"""Job runs models.

Implementation notes:
    - It may be possible that we can get real foreign key constraints by using the parent-child
      table pattern, and have one child tables per job type.
"""

import datetime
from typing import Optional

from sqlalchemy import Index, orm

from phiphi import platform_db
from phiphi.api import base_models


class JobRunsBase(platform_db.Base):
    """Job runs model."""

    __abstract__ = True

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    project_id: orm.Mapped[int]
    foreign_id: orm.Mapped[int]
    foreign_job_type: orm.Mapped[str]
    status: orm.Mapped[Optional[str]]
    flow_run_id: orm.Mapped[Optional[str]]
    # Note: name of the _flow run_, not the flow. Useful for searching in Prefect UI.
    flow_run_name: orm.Mapped[Optional[str]]
    started_processing_at: orm.Mapped[Optional[datetime.datetime]]
    completed_at: orm.Mapped[Optional[datetime.datetime]]
    total_cost: orm.Mapped[Optional[float]]
    gather_result_count: orm.Mapped[Optional[int]]
    estimated_total_cost: orm.Mapped[Optional[float]]
    gather_normalise_error_count: orm.Mapped[Optional[int]]
    is_total_cost_estimated: orm.Mapped[bool] = orm.mapped_column(default=False)


class JobRuns(JobRunsBase, base_models.TimestampModel):
    """Job runs model that can inherit from multiple models."""

    __tablename__ = "job_runs"
    __table_args__ = (
        # Requests with `WHERE project_id` will also use this index.
        Index(
            "idx_project_id_foreign_job_type_foreign_id",
            "project_id",
            "foreign_job_type",
            "foreign_id",
        ),
        # This index is added to make sure that the queries with two columns as there is a high
        # chance that the queries will not use `idx_project_id_foreign_job_type_foreign_id` index.
        Index(
            "idx_foreign_job_type_foreign_id",
            "foreign_job_type",
            "foreign_id",
        ),
    )
