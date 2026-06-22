"""Classified Messages table definition."""

import pandera.pandas as pa
import sqlalchemy as sa

from phiphi import project_db
from phiphi.pipeline_jobs import constants

classified_messages_schema = pa.DataFrameSchema(
    {
        "classifier_id": pa.Column(pa.Int, nullable=False),
        "classifier_version_id": pa.Column(pa.Int, nullable=False),
        "class_name": pa.Column(pa.String, nullable=False),
        "phoenix_platform_message_id": pa.Column(pa.String, nullable=False),
        "job_run_id": pa.Column(pa.Int, nullable=False),
        # The table has been created with nullable due to limitations on adding columns to BigQuery
        # tables. The column is not nullable in the schema.
        "class_probability": pa.Column(pa.Float, nullable=False, default=1.0),
    }
)


classified_messages_table = sa.Table(
    constants.CLASSIFIED_MESSAGES_TABLE_NAME,
    project_db.metadata,
    sa.Column("classifier_id", sa.Integer, nullable=False),
    sa.Column("classifier_version_id", sa.Integer, nullable=False),
    sa.Column("class_name", sa.String, nullable=False),
    sa.Column("phoenix_platform_message_id", sa.String, nullable=False),
    sa.Column("job_run_id", sa.Integer, nullable=False),
    sa.Column("class_probability", sa.Float, nullable=True, default=1.0),
)
