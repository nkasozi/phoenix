"""Classified Messages Errors table definition."""

import pandera.pandas as pa
import sqlalchemy as sa

from phiphi import project_db
from phiphi.pipeline_jobs import constants

classified_messages_errors_schema = pa.DataFrameSchema(
    {
        "classifier_id": pa.Column(pa.Int, nullable=False),
        "classifier_version_id": pa.Column(pa.Int, nullable=False),
        "phoenix_platform_message_id": pa.Column(pa.String, nullable=False),
        "job_run_id": pa.Column(pa.Int, nullable=False),
        "error_json": pa.Column(pa.String, nullable=False),
    }
)

classified_messages_errors_table = sa.Table(
    constants.CLASSIFIED_MESSAGES_ERRORS_TABLE_NAME,
    project_db.metadata,
    sa.Column("classifier_id", sa.Integer, nullable=False),
    sa.Column("classifier_version_id", sa.Integer, nullable=False),
    sa.Column("phoenix_platform_message_id", sa.String, nullable=False),
    sa.Column("job_run_id", sa.Integer, nullable=False),
    sa.Column("error_json", sa.String, nullable=False),
)
