"""Gather batches.

It is important that the schema and table definitions match exactly.
"""

import pandera.pandas as pa
import sqlalchemy as sa

from phiphi import project_db
from phiphi.api.projects.gathers import schemas
from phiphi.pipeline_jobs import constants
from phiphi.pipeline_jobs import utils as pipeline_jobs_utils

# TODO: should add BQ cluster specification on columns: gather_id, job_run_id, gather_batch_id
# Schema for gather batches
gather_batches_schema = pa.DataFrameSchema(
    {
        "gather_id": pa.Column(pa.Int, nullable=False),
        "job_run_id": pa.Column(pa.Int, nullable=False),
        "gather_type": pa.Column(
            pa.String,
            checks=pa.Check.isin([e.value for e in schemas.ChildTypeName]),
            nullable=False,
        ),
        "batch_id": pa.Column(pa.Int, nullable=False),
        "gathered_at": pipeline_jobs_utils.utc_datetime_column(nullable=False),
        "json_data": pa.Column(pa.String, nullable=False),
        "last_processed_at": pipeline_jobs_utils.utc_datetime_column(nullable=True),
    }
)

gather_batches_table = sa.Table(
    constants.GATHER_BATCHES_TABLE_NAME,
    project_db.metadata,
    sa.Column("gather_id", sa.Integer, nullable=False),
    sa.Column("job_run_id", sa.Integer, nullable=False),
    sa.Column("gather_type", sa.String, nullable=False),
    sa.Column("batch_id", sa.Integer, nullable=False),
    # Pandas datetime is parsed into Bigquery as TIMESTAMP by default
    sa.Column("gathered_at", sa.TIMESTAMP, nullable=False),
    # This has to be a string because sqlalchemy has not yet implemented
    # a JSON type for BigQuery.
    # https://github.com/googleapis/python-bigquery-sqlalchemy/issues/546
    # And not in pandas gbq:
    # https://github.com/googleapis/python-bigquery/issues/1966
    sa.Column("json_data", sa.String, nullable=False),
    sa.Column("last_processed_at", sa.TIMESTAMP, nullable=True),
)
