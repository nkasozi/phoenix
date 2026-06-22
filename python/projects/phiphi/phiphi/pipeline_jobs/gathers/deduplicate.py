"""Deduplicate functionality for the gather pipeline job."""

import prefect
from google.cloud import bigquery

from phiphi.pipeline_jobs import constants


@prefect.task
def refresh_deduplicated_messages_tables(
    bigquery_dataset: str,
) -> None:
    """Task which takes messages table and produces a de-duplicated version."""
    client = bigquery.Client()

    source_table_name = f"{bigquery_dataset}.{constants.GENERALISED_MESSAGES_TABLE_NAME}"
    deduped_table_name = (
        f"{bigquery_dataset}.{constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME}"
    )

    dedupe_query = f"""
    CREATE OR REPLACE TABLE `{deduped_table_name}` AS
    WITH time_ordered_messages AS (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY platform, data_type, phoenix_platform_message_id
                ORDER BY platform_message_last_updated_at DESC, phoenix_processed_at DESC
            ) AS row_num
        FROM
            `{source_table_name}`
    )
    SELECT
        * EXCEPT (row_num)
    FROM
        time_ordered_messages
    WHERE
        row_num = 1
    """

    dedupe_job = client.query(dedupe_query)
    dedupe_job.result()


@prefect.task
def refresh_deduplicated_authors_tables(
    bigquery_dataset: str,
) -> None:
    """Task which takes messages table and produces a de-duplicated authors version.

    This must be run after the deduplicated messages table has been created.

    !! IMPORTANT !!
    The `deduplicated_generalised_authors` table must be in sync with the schema:
    `deduplicated_generalised_authors` in `pipeline_jobs/generalised_authors.py`
    """
    client = bigquery.Client()

    source_table_name = (
        f"{bigquery_dataset}.{constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME}"
    )
    deduped_table_name = (
        f"{bigquery_dataset}.{constants.DEDUPLICATED_GENERALISED_AUTHORS_TABLE_NAME}"
    )

    dedupe_query = f"""
    CREATE OR REPLACE TABLE `{deduped_table_name}` AS
    WITH
        time_ordered_authors AS (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY platform, phoenix_platform_message_author_id
                    ORDER BY platform_message_last_updated_at DESC, phoenix_processed_at DESC
                ) AS row_num
            FROM
                `{source_table_name}`
        ),
        deduplicated_authors AS (
            SELECT
                phoenix_platform_message_author_id,
                pi_platform_message_author_id,
                pi_platform_message_author_name,
                -- Currently we don't have any metadata about the created at or updated at of the
                -- author. `phoenix_processed_at` is the best option for understanding when the
                -- author was added to the system.
                phoenix_processed_at,
                platform,
            FROM
                time_ordered_authors
            WHERE
                row_num = 1
        ),
        counts_per_author AS (
            SELECT
                phoenix_platform_message_author_id,
                COUNT(
                    DISTINCT IF(
                        data_type = 'posts', phoenix_platform_message_id, NULL
                    )
                ) AS post_count,
                COUNT(
                    DISTINCT IF(
                        data_type = 'comments', phoenix_platform_message_id, NULL
                    )
                ) AS comment_count
            FROM
                `{source_table_name}`
            GROUP BY
                phoenix_platform_message_author_id
        )
    SELECT
        da.*,
        cpa.post_count,
        cpa.comment_count
    FROM
        deduplicated_authors AS da
    LEFT JOIN
        counts_per_author AS cpa
    ON da.phoenix_platform_message_author_id = cpa.phoenix_platform_message_author_id
    """
    dedupe_job = client.query(dedupe_query)
    dedupe_job.result()
