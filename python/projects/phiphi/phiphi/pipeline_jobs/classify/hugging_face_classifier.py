"""Hugging Face classifier module.

A Prefect task that orchestrates Phoenix’s external
`hugging_face_classifier` deployment:

1. **Export** unclassified messages directly from BigQuery to GCS Parquet.
2. **Invoke** the deployment, passing the Parquet URIs and model ID.
3. **Bucketing**: Read the raw scores Parquet from the external table in BigQuery,
   run a single INSERT…SELECT…UNION ALL using the model’s bucketing_configs,
   writing into `classified_messages`.

Bucket-lifecycle rules handle clean-up of temporary objects.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import prefect
from google.cloud import bigquery
from prefect.deployments import run_deployment

from phiphi import config, utils
from phiphi.api.projects.classifiers.hugging_face import schemas
from phiphi.pipeline_jobs import constants as pipeline_consts

utils.init_logging()
file_logger = logging.getLogger(__name__)


def build_unclassified_select_sql(
    dataset: str, source_table_name: str, destination_table_name: str
) -> str:
    """Return a SELECT statement that excludes already-classified messages."""
    return f"""
        SELECT
            src.phoenix_platform_message_id AS id,
            src.pi_text                     AS text
        FROM
            `{dataset}.{source_table_name}` AS src
        LEFT JOIN
            `{dataset}.{destination_table_name}` AS dst
        ON
            src.phoenix_platform_message_id = dst.phoenix_platform_message_id
            AND dst.classifier_id = @classifier_id
            AND dst.classifier_version_id = @classifier_version_id
        WHERE
            dst.phoenix_platform_message_id IS NULL
    """


def count_unclassified_rows(
    client: bigquery.Client,
    select_sql: str,
    query_parameters: List[bigquery.ScalarQueryParameter],
) -> int:
    """Count the number of unclassified messages.

    Args:
        client: BigQuery client.
        select_sql: The SELECT statement to count rows from.
        query_parameters: Query parameters for the SELECT statement.

    Returns:
        int: The number of unclassified rows.
    """
    count_sql = f"SELECT COUNT(*) as count FROM ({select_sql})"
    job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)
    result = client.query(count_sql, job_config=job_config).result()
    row = next(result)
    return int(row["count"])


def export_unclassified_to_gcs(
    client: bigquery.Client,
    select_sql: str,
    uri: str,
    query_parameters: List[bigquery.ScalarQueryParameter],
) -> None:
    """Run a BigQuery EXPORT DATA statement to export all unclassified messages."""
    export_sql = f"""
        EXPORT DATA OPTIONS(
            uri='{uri}',
            format='{pipeline_consts.HF_EXPORT_OPTIONS["format"]}',
            compression='{pipeline_consts.HF_EXPORT_OPTIONS["compression"]}',
            overwrite={str(pipeline_consts.HF_EXPORT_OPTIONS["overwrite"]).lower()}
        )
        AS
        {select_sql}
    """
    job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)
    client.query(export_sql, job_config=job_config).result()


async def invoke_hf_flow(
    input_uri: str,
    output_uri: str,
    failed_uri: str,
    model_id: str,
    logger: logging.Logger | logging.LoggerAdapter[logging.Logger] = file_logger,
) -> Any:
    """Trigger the external `hugging_face_classifier` deployment and wait for completion.

    Due to the magic detection of if the call is in a thread or not this function will behaviour
    differently if it is marks as sync and then run in a thread or if it is marked as async and
    run.

    It is now a async function so the behaviour is consistent and transparent.
    """
    logger.info(
        "Invoking Hugging Face flow %s with model %s, wait time %ss",
        config.settings.HF_FLOW_NAME,
        model_id,
        config.settings.HF_FLOW_TIMEOUT_SECONDS,
    )
    assert isinstance(config.settings.HF_FLOW_NAME, str), "HF_FLOW_NAME must be a string"
    flow_run = await run_deployment(
        name=config.settings.HF_FLOW_NAME,
        parameters={
            "input_file_path": input_uri,
            "output_file_path": output_uri,
            "failed_records_file_path": failed_uri,
            "model_name": model_id,
        },
        timeout=config.settings.HF_FLOW_TIMEOUT_SECONDS,
    )
    logger.info("Hugging Face flow invocation completed, flow run:")
    logger.info(flow_run)
    # The results of the hugging face classifier are in JSON.
    result = await flow_run.state.aresult(raise_on_failure=True)  # type: ignore[attr-defined]
    logger.info("Hugging Face flow run result: %s", result)
    return True


def build_bq_bucketing_query(
    params: schemas.HuggingFaceParams,
    dataset: str,
    hf_flow_results_table: str,
    classified_messages_table: str,
    classifier_id: int,
    classifier_version_id: int,
    job_run_id: int,
    output_uri: str,
) -> str:
    """Build a single INSERT…SELECT that applies bucketing_configs via UNION ALL.

    Expects ‘results_table’ over columns (id, label, score),
    plus the pseudo‐column _FILE_NAME.
    Only the exact file for this job_run_id will be included.
    """
    segments: List[str] = []
    # only pull the single parquet for this run
    file_filter = f"WHERE _FILE_NAME = '{output_uri}'"

    for cfg in params.bucketing_configs:
        # CASE blocks for each bucket
        case_clauses = "\n            ".join(
            f"WHEN score <= {b.upper_threshold} THEN CONCAT('{b.name}_', label)"
            for b in cfg.buckets
        )

        select = f"""
    SELECT
      {classifier_id}           AS classifier_id,
      {classifier_version_id}   AS classifier_version_id,
      CASE
            {case_clauses}
      END                       AS class_name,
      score                     AS class_probability,
      id                        AS phoenix_platform_message_id,
      {job_run_id}              AS job_run_id
    FROM `{dataset}.{hf_flow_results_table}`
    {file_filter}"""

        # Restrict to specific raw class if not catch-all
        if cfg.class_name != "*":
            select += f"\n  AND label = '{cfg.class_name}'"

        segments.append(select.strip())

    combined = "\nUNION ALL\n".join(segments)
    return f"""
        INSERT INTO `{dataset}.{classified_messages_table}` (
          classifier_id,
          classifier_version_id,
          class_name,
          class_probability,
          phoenix_platform_message_id,
          job_run_id
        )
        {combined}
    """.strip()


def read_scores_bucket_write_to_bq_classes_table(
    output_uri: str,
    classifier: schemas.HuggingFaceClassifierPipeline,
    bigquery_dataset: str,
    job_run_id: int,
) -> int:
    """Select the HF flow output scores, bucket in BQ, and write classified_messages."""
    client = bigquery.Client()

    params = classifier.latest_version.params
    sql = build_bq_bucketing_query(
        params=params,
        dataset=bigquery_dataset,
        hf_flow_results_table=pipeline_consts.HF_FLOW_RESULTS_EXTERNAL_TABLE_NAME,
        classified_messages_table=pipeline_consts.CLASSIFIED_MESSAGES_TABLE_NAME,
        classifier_id=classifier.id,
        classifier_version_id=classifier.latest_version.version_id,
        job_run_id=job_run_id,
        output_uri=output_uri,
    )
    job = client.query(sql)
    _ = job.result()  # wait for completion
    num_inserted = getattr(job, "num_dml_affected_rows", None)
    return num_inserted or 0


@prefect.task
async def classify(
    classifier: schemas.HuggingFaceClassifierPipeline,
    bigquery_dataset: str,
    job_run_id: int,
    hugging_face_gcs_bucket_name: str = config.settings.HF_GCS_BUCKET_NAME,
    logger: logging.Logger | logging.LoggerAdapter[logging.Logger] | None = None,
) -> Dict[str, Any]:
    """Run a Hugging Face classifier for all unclassified messages."""
    if logger is None:
        logger = prefect.get_run_logger()

    logger.info(
        "Starting Hugging Face classify task for job_run_id=%s and classifier_id=%s",
        job_run_id,
        classifier.id,
    )
    client = bigquery.Client()

    bucket = hugging_face_gcs_bucket_name
    prefix = bigquery_dataset

    input_uri = pipeline_consts.HF_INPUT_URI_TEMPLATE.format(
        bucket=bucket, prefix=prefix, job_run_id=job_run_id
    )
    output_uri = pipeline_consts.HF_RESULTS_URI_TEMPLATE.format(
        bucket=bucket, prefix=prefix, job_run_id=job_run_id
    )
    failed_uri = pipeline_consts.HF_FAILED_URI_TEMPLATE.format(
        bucket=bucket, prefix=prefix, job_run_id=job_run_id
    )

    source_table_name = pipeline_consts.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME
    destination_table_name = pipeline_consts.CLASSIFIED_MESSAGES_TABLE_NAME

    select_sql = build_unclassified_select_sql(
        dataset=bigquery_dataset,
        source_table_name=source_table_name,
        destination_table_name=destination_table_name,
    )
    query_parameters = [
        bigquery.ScalarQueryParameter("classifier_id", "INT64", classifier.id),
        bigquery.ScalarQueryParameter(
            "classifier_version_id", "INT64", classifier.latest_version.version_id
        ),
    ]

    logger.info("Counting unclassified rows")
    num_unclassified = count_unclassified_rows(client, select_sql, query_parameters)
    logger.info("Found %s unclassified rows", num_unclassified)

    # Skip invoking HF flow if there are no rows to classify
    if num_unclassified == 0:
        logger.info(
            "No unclassified messages found, skipping export and Hugging Face flow invocation"
        )
        return {"num_rows_written": 0}

    logger.info("Exporting unclassified rows to %s", input_uri)
    export_unclassified_to_gcs(client, select_sql, input_uri, query_parameters)

    logger.info(
        "Invoking Hugging Face flow for model %s", classifier.latest_version.params.model_id
    )
    result_from_invoke = await invoke_hf_flow(
        input_uri, output_uri, failed_uri, classifier.latest_version.params.model_id, logger=logger
    )
    logger.info(
        "Hugging Face flow completed with %s",
        result_from_invoke,
    )

    logger.info("Bucketing scores in BigQuery and writing end classes to BQ")
    num_rows_written = read_scores_bucket_write_to_bq_classes_table(
        output_uri=output_uri,
        classifier=classifier,
        bigquery_dataset=bigquery_dataset,
        job_run_id=job_run_id,
    )

    return {"num_rows_written": num_rows_written}
