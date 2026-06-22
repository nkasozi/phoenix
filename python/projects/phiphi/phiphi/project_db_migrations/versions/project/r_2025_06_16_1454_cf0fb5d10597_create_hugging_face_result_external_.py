"""Create hugging_face_result_external_table.

Revision ID: cf0fb5d10597
Revises: 93d754d410be
Create Date: 2025-06-16 14:54:19.444530

"""

import logging
from typing import Sequence, Union

import pandas as pd
import sqlalchemy as sa
from alembic import context, op
from phiphi import utils
from phiphi.pipeline_jobs import constants as pipeline_consts

utils.init_logging()

# Have to use alembic.runtime otherwise the logs will not be captured by the alembic logger.
logger = logging.getLogger("alembic.runtime.migrations.create_hugging_face_result_external_table")

# revision identifiers, used by Alembic.
revision: str = "cf0fb5d10597"
down_revision: Union[str, Sequence[str], None] = "93d754d410be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create an external table over all Hugging Face scores in GCS."""
    logger.info("Creating external table for Hugging Face scores.")
    conn = op.get_bind()
    # Extract the BigQuery dataset from the SQLAlchemy URL: bigquery://PROJECT/DATASET
    dataset = conn.engine.url.database

    bucket = context.config.get_main_option("hugging_face_gcs_bucket_name")
    logger.debug(
        "Creating Hugging Face results external table in dataset %s, bucket %s",
        dataset,
        bucket,
    )

    # Write seed data into a “-1” placeholder path, to avoid "no files found" error when
    # creating the external table.
    placeholder_uri = pipeline_consts.HF_RESULTS_URI_TEMPLATE.format(
        bucket=bucket,
        prefix=dataset,
        job_run_id="-1",
    )
    ################
    # Warning!!!!!!!!!!!
    # Changes to this seed data schema must be reflected in the CREATE EXTERNAL TABLE statement
    # below.
    ################
    seed_df = pd.DataFrame(
        [
            {"id": "placeholder1", "label": "placeholder", "score": 0.0},
        ]
    )
    seed_df.to_parquet(placeholder_uri, index=False)

    wildcard_uri = pipeline_consts.HF_RESULTS_URI_TEMPLATE.format(
        bucket=bucket,
        prefix=dataset,
        job_run_id="*",
    )

    hive_url = pipeline_consts.HF_RESULTS_URI_HIVE_TEMPLATE.format(
        bucket=bucket,
        prefix=dataset,
    )
    table = pipeline_consts.HF_FLOW_RESULTS_EXTERNAL_TABLE_NAME
    query = f"""
        CREATE EXTERNAL TABLE `{dataset}.{table}` (
            id STRING,
            label STRING,
            score FLOAT64
        )
        WITH PARTITION COLUMNS (
            job_run_id INT64
        )
        OPTIONS (
          format='PARQUET',
          uris=['{wildcard_uri}'],
          hive_partition_uri_prefix='{hive_url}'
        );
        """
    logger.debug("Creating external table with query: %s", query)
    # Create the external table over that GCS wildcard
    r = conn.execute(sa.text(query))
    logger.debug("External table creation result: %s", r)
    logger.debug("External table created successfully.")


def downgrade() -> None:
    """Drop the external table for Hugging Face scores."""
    conn = op.get_bind()
    dataset = conn.engine.url.database
    table = pipeline_consts.HF_FLOW_RESULTS_EXTERNAL_TABLE_NAME

    conn.execute(sa.text(f"DROP EXTERNAL TABLE `{dataset}.{table}`"))
