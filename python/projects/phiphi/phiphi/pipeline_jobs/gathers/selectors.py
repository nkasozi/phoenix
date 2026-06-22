"""Selects inputs for subsequent gathers from previously gathered data."""

import prefect
from google.cloud import bigquery

from phiphi.api.projects.gathers import schemas as gather_schemas
from phiphi.pipeline_jobs import constants


@prefect.task
def get_post_ids_with_comments(
    bigquery_dataset: str,
    gather_id: int,
    gather_type: gather_schemas.ChildTypeName,
) -> list[str]:
    """Gets post ids with comments from previously gathered data."""
    logger = prefect.get_run_logger()
    client = bigquery.Client()

    gather_type_value = gather_type.value
    source_table_name = f"{bigquery_dataset}.{constants.GENERALISED_MESSAGES_TABLE_NAME}"
    query = f"""
    SELECT DISTINCT pi_platform_message_id
    FROM `{source_table_name}`
    WHERE gather_id = {gather_id}
    AND gather_type = '{gather_type_value}'
    AND comment_count > 0
    """
    logger.info(
        f"Querying post IDs: table={source_table_name}, "
        f"gather_id={gather_id}, gather_type={gather_type_value!r}"
    )
    logger.info(f"Query: {query.strip()}")
    job = client.query(query)
    rows = job.result()
    result = [row["pi_platform_message_id"] for row in rows]
    logger.info(f"Query returned {len(result)} post_ids")
    return result
