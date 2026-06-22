"""Delete gather tasks."""

import prefect
from google.cloud import bigquery

from phiphi.pipeline_jobs import constants


@prefect.task
def delete_gathered_data(
    gather_id: int,
    bigquery_dataset: str,
    gather_batches_table: str = constants.GATHER_BATCHES_TABLE_NAME,
    generalised_messages_table: str = constants.GENERALISED_MESSAGES_TABLE_NAME,
) -> None:
    """Delete gathered data from a BigQuery table.

    Deleted both the gather batches and generalised messages for a gather id. It is important to
    delete all the data to be GDPR compliant.

    Args:
        gather_id (int): The gather id.
        bigquery_dataset (str): The BigQuery dataset.
        gather_batches_table (str): The gather batches table.
            Default is constants.GATHER_BATCHES_TABLE_NAME.
        generalised_messages_table (str): The generalised messages table.
            Default is constants.GENERALISED_MESSAGES_TABLE_NAME.
    """
    logger = prefect.get_run_logger()
    client = bigquery.Client()
    query = f"""
        DELETE FROM {bigquery_dataset}.{gather_batches_table}
        WHERE gather_id = {gather_id}
    """
    delete_job_1 = client.query(query)
    query = f"""
        DELETE FROM {bigquery_dataset}.{generalised_messages_table}
        WHERE gather_id = {gather_id}
    """
    delete_job_2 = client.query(query)
    # Using results to wait for the jobs to finish
    delete_job_1.result()
    logger.info(f"Deleted gather batches for gather_id {gather_id}.")
    delete_job_2.result()
    logger.info(f"Deleted generalised messages for gather_id {gather_id}.")
    return None
