"""Classified authors table and schema definition.

!!Important!!
The `manually_classified_authors_table` and `manually_classified_authors_schema` should match.
"""

import pandera.pandas as pa
import sqlalchemy as sa

from phiphi import project_db
from phiphi.pipeline_jobs import constants
from phiphi.pipeline_jobs import utils as pipeline_jobs_utils

manually_classified_authors_schema = pa.DataFrameSchema(
    {
        "class_name": pa.Column(pa.String, nullable=False),
        "phoenix_platform_author_id": pa.Column(pa.String, nullable=False),
        "last_updated_at": pipeline_jobs_utils.utc_datetime_column(nullable=False),
    }
)


manually_classified_authors_table = sa.Table(
    constants.MANUALLY_CLASSIFIED_AUTHORS_TABLE_NAME,
    project_db.metadata,
    sa.Column("class_name", sa.String, nullable=False),
    sa.Column("phoenix_platform_author_id", sa.String, nullable=False),
    sa.Column("last_updated_at", sa.TIMESTAMP, nullable=False),
)

classified_authors_schema = pa.DataFrameSchema(
    {
        "classifier_id": pa.Column(pa.Int, nullable=False),
        "classifier_version_id": pa.Column(pa.Int, nullable=False),
        "class_name": pa.Column(pa.String, nullable=False),
        "phoenix_platform_message_author_id": pa.Column(pa.String, nullable=False),
        "job_run_id": pa.Column(pa.Int, nullable=False),
    }
)

classified_authors_table = sa.Table(
    constants.CLASSIFIED_AUTHORS_TABLE_NAME,
    project_db.metadata,
    sa.Column("classifier_id", sa.Integer, nullable=False),
    sa.Column("classifier_version_id", sa.Integer, nullable=False),
    sa.Column("class_name", sa.String, nullable=False),
    sa.Column("phoenix_platform_message_author_id", sa.String, nullable=False),
    sa.Column("job_run_id", sa.Integer, nullable=False),
)
