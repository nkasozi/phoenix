"""Perspective API classifier module.

This module defines a Prefect task that runs the Perspective API classifier.

Rough overview of batch loop:
1) Pulls batch of unclassified data from BigQuery.
2) Sends each text item to the Perspective API and maps the resulting scores to the user-defined
bucket labels, in parallel.
3) Writes classification results back to BigQuery.
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import pandas as pd
import prefect
import ratelimit
import requests
from google.cloud import bigquery
from prefect.concurrency.sync import concurrency
from pydantic import AliasChoices, BaseModel, Field

from phiphi import config
from phiphi.api.projects.classifiers.perspective_api import schemas
from phiphi.pipeline_jobs import classified_messages, classified_messages_errors, utils
from phiphi.pipeline_jobs import constants as pipeline_jobs_constants

API_URL = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"

BATCH_SIZE = 10000


def get_total_unclassified_count(
    bq_client: bigquery.Client,
    query_parameters: List[bigquery.ScalarQueryParameter],
    generalised_messages_table_name: str,
    classified_messages_table_name: str,
    classified_messages_errors_table_name: str,
) -> int:
    """Get the total number of unclassified messages before batching.

    Args:
        bq_client (bigquery.Client): A BigQuery client.
        query_parameters (List[bigquery.ScalarQueryParameter]): Query parameters.
        generalised_messages_table_name (str): Fully qualified generalised messages table name.
        classified_messages_table_name (str): Fully qualified classified messages table name.
        classified_messages_errors_table_name (str): Fully qualified classified messages errors
            table name.

    Returns:
        int: The total number of unclassified messages.
    """
    count_query = f"""
        WITH processed AS (
            SELECT
                phoenix_platform_message_id
            FROM
                `{classified_messages_table_name}`
            WHERE
                classifier_id = @classifier_id
                AND classifier_version_id = @classifier_version_id
            UNION DISTINCT
            SELECT
                phoenix_platform_message_id
            FROM
                `{classified_messages_errors_table_name}`
            WHERE
                classifier_id = @classifier_id
                AND classifier_version_id = @classifier_version_id
            )
        SELECT
            COUNT(*) AS total_unclassified
        FROM
            `{generalised_messages_table_name}` AS gm
        LEFT JOIN
            processed p
        ON
            gm.phoenix_platform_message_id = p.phoenix_platform_message_id
        WHERE
            p.phoenix_platform_message_id IS NULL
    """
    job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)
    query_job = bq_client.query(count_query, job_config=job_config)
    unclassified_messages_count_df = query_job.to_dataframe()
    return int(unclassified_messages_count_df["total_unclassified"][0])


def get_unclassified_messages(
    bq_client: bigquery.Client,
    query_parameters: List[bigquery.ScalarQueryParameter],
    generalised_messages_table_name: str,
    classified_messages_table_name: str,
    classified_messages_errors_table_name: str,
) -> pd.DataFrame:
    """Get a batch of unclassified messages from BigQuery."""
    query = f"""
        WITH processed AS (
            SELECT
                phoenix_platform_message_id
            FROM
                `{classified_messages_table_name}`
            WHERE
                classifier_id = @classifier_id
                AND classifier_version_id = @classifier_version_id
            UNION DISTINCT
            SELECT
                phoenix_platform_message_id
            FROM
                `{classified_messages_errors_table_name}`
            WHERE
                classifier_id = @classifier_id
                AND classifier_version_id = @classifier_version_id
        )
        SELECT
            gm.phoenix_platform_message_id,
            gm.pi_text
        FROM
            `{generalised_messages_table_name}` AS gm
        LEFT JOIN
            processed p
        ON
            gm.phoenix_platform_message_id = p.phoenix_platform_message_id
        WHERE
            p.phoenix_platform_message_id IS NULL
        ORDER BY
            gm.phoenix_platform_message_id
        LIMIT
            @batch_size
    """
    job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)
    query_job = bq_client.query(query, job_config=job_config)
    return query_job.to_dataframe()


def extract_enabled_attributes(
    params: schemas.PerspectiveAPIParams,
) -> List[str]:
    """Extract enabled attributes from the Perspective API params."""
    enabled_attrs = []
    for attribute_name, attribute_config in iter(params):
        if attribute_config.enabled:
            enabled_attrs.append(attribute_name)
    if not enabled_attrs:
        raise ValueError("At least one Perspective attribute should be enabled.")
    return enabled_attrs


class PerspectiveAPIAttributeSummaryScore(BaseModel):
    """Attribute summary score, part of a Perspective API response."""

    value: float
    type: str


class PerspectiveAPIAttributeScore(BaseModel):
    """Attribute score, part of a Perspective API response.

    Span scores are unlikely to be used, but the structure matches the API response.
    """

    summary_score: PerspectiveAPIAttributeSummaryScore = Field(
        ..., validation_alias=AliasChoices("summaryScore", "summary_score")
    )
    span_scores: Optional[List[Any]] = Field(
        default=None, validation_alias=AliasChoices("spanScores", "span_scores")
    )


class PerspectiveAPIResponse(BaseModel):
    """Perspective API response schema."""

    attribute_scores: Dict[str, PerspectiveAPIAttributeScore] = Field(
        ..., validation_alias=AliasChoices("attributeScores", "attribute_scores")
    )
    languages: Optional[List[str]] = None
    detected_languages: Optional[List[str]] = None


class PerspectiveAPISingleErrorResponse(BaseModel):
    """Perspective API single error response schema."""

    status_code: Optional[int] = Field(default=None)
    response_json: Optional[dict] = Field(default=None)
    error_message: Optional[str] = Field(default=None)


class PerspectiveAPIErrorResponse(BaseModel):
    """Perspective API error response schema."""

    payload: Dict[str, Any] = Field(...)
    errors: list[PerspectiveAPISingleErrorResponse]


@ratelimit.sleep_and_retry
@ratelimit.limits(
    calls=config.settings.PERSPECTIVE_API_REQUEST_LIMIT_FOR_PERIOD,
    period=config.settings.PERSPECTIVE_API_REQUEST_LIMIT_PERIOD_SECONDS,
)
def request_perspective_api(
    payload: Dict[str, Any],
) -> requests.Response:
    """Call the Perspective API to analyze text."""
    return requests.post(
        API_URL,
        params={"key": config.settings.PERSPECTIVE_API_KEY},
        json=payload,
        timeout=30,
    )


def call_perspective_api(
    text: str,
    attributes: List[str],
    backoff_factor: float = 1.0,
    max_retries: int = 4,
    rate_limit_error_backoff_factor: float = 4.0,
) -> PerspectiveAPIResponse | PerspectiveAPIErrorResponse:
    """Call the Perspective API to analyze text.

    The call will be retried if the response is a server error (5xx), rate limit or a connection
    error.

    Args:
        text (str): Text to analyze.
        attributes (List[str]): List of attributes to request.
        backoff_factor (float, optional): Backoff factor for retrying. Defaults to 1.0.
        max_retries (int, optional): Maximum number of retries. Defaults to 4.
        rate_limit_error_backoff_factor (float, optional): Backoff factor for retrying on rate
            limit errors. Defaults to 4.0. This is separate from the backoff factor as rate limit
            errors are likely to be more common and we want to back off more aggressively. The
            default means that the 4th retry will wait 64 seconds and allow for rate limits that
            are capped for a 60 second period.

    Returns:
        PerspectiveAPIResponse | PerspectiveAPIErrorResponse: API response or error.
    """
    if config.settings.PERSPECTIVE_API_KEY is None:
        raise ValueError("PERSPECTIVE_API_KEY is not set")
    attributes_with_configs: Dict[str, Dict] = {attr: {} for attr in attributes}
    payload = {
        "comment": {"text": text},
        "requestedAttributes": attributes_with_configs,
    }
    errors = []
    for attempt in range(max_retries):
        status_code = None
        response_json = None
        try:
            response = request_perspective_api(payload)
            status_code = response.status_code
            response_json = response.json()
            response.raise_for_status()
            # Any validation errors raised from the parsing of the response will not be caught
            # as they critical and should be raised.
            return PerspectiveAPIResponse.model_validate(response.json())

        except requests.exceptions.HTTPError as exc:
            errors.append(
                PerspectiveAPISingleErrorResponse(
                    status_code=status_code,
                    response_json=response_json,
                    error_message=str(exc),
                )
            )
            if status_code == 429 and attempt < max_retries:
                sleep_time = rate_limit_error_backoff_factor * (2**attempt)
                time.sleep(sleep_time)
                continue
            if status_code and 500 <= status_code < 600 and attempt < max_retries:
                sleep_time = backoff_factor * (2**attempt)
                time.sleep(sleep_time)
                continue
            else:
                return PerspectiveAPIErrorResponse(
                    payload=payload,
                    errors=errors,
                )

        except requests.exceptions.RequestException as exc:
            errors.append(
                PerspectiveAPISingleErrorResponse(
                    status_code=status_code,
                    response_json=response_json,
                    error_message=str(exc),
                )
            )
            # Covers various connection-related errors (ConnectionError, Timeout, etc.)
            # Retry on the assumption it's transient.
            if attempt < max_retries:
                sleep_time = backoff_factor * (2**attempt)
                time.sleep(sleep_time)
                continue
            else:
                return PerspectiveAPIErrorResponse(
                    payload=payload,
                    errors=errors,
                )

    # If we reach here, we've exhausted all retries
    return PerspectiveAPIErrorResponse(
        payload=payload,
        errors=errors,
    )


def map_score_to_class(
    score: float, attribute_name: str, attribute_config: schemas.PerspectiveAttributeConfig
) -> str:
    """Map a score to a class based on the attribute's bucket configuration."""
    for bucket in attribute_config.buckets:
        if score <= bucket.upper_threshold:
            return schemas.PerspectiveAPIVersionBase.format_class_name(bucket.name, attribute_name)
    raise ValueError("No bucket found for score")


def classify_message(
    text: str,
    message_id: str,
    classifier: schemas.PerspectiveAPIClassifierPipeline,
) -> List[Dict[str, Any]]:
    """Classify a single message using the Perspective API and bucket configs.

    Note, returns same number of classes (dicts) as there are enabled attributes.
    """
    attributes_to_request = extract_enabled_attributes(classifier.latest_version.params)
    attributes_and_api_format = {attr: attr.upper() for attr in attributes_to_request}
    attrbutes_for_api = list(attributes_and_api_format.values())
    api_response_schema = call_perspective_api(text, attrbutes_for_api)

    if isinstance(api_response_schema, PerspectiveAPIErrorResponse):
        return [
            {
                "phoenix_platform_message_id": message_id,
                "error_json": json.dumps(api_response_schema.model_dump()),
            }
        ]

    class_rows = []
    for attribute, api_format_attribute in attributes_and_api_format.items():
        score = api_response_schema.attribute_scores[api_format_attribute].summary_score.value
        attribute_config = getattr(classifier.latest_version.params, attribute)
        class_name = map_score_to_class(score, attribute, attribute_config)
        class_rows.append(
            {
                "phoenix_platform_message_id": message_id,
                "class_name": class_name,
                "class_probability": score,
                "attribute": attribute,
            }
        )
    return class_rows


def form_classified_messages_df(
    class_dicts: List[Dict[str, Any]],
    classifier_id: int,
    classifier_version_id: int,
    job_run_id: int,
) -> pd.DataFrame:
    """Form classified messages dataframe for writing to BigQuery."""
    if not class_dicts:
        raise ValueError("No classes to form classified messages DataFrame.")
    classified_messages_df = pd.DataFrame(class_dicts)
    classified_messages_df["classifier_id"] = classifier_id
    classified_messages_df["classifier_version_id"] = classifier_version_id
    classified_messages_df["job_run_id"] = job_run_id
    classified_messages_df = classified_messages_df[
        [
            "classifier_id",
            "classifier_version_id",
            "class_name",
            "class_probability",
            "phoenix_platform_message_id",
            "job_run_id",
        ]
    ]

    classified_messages.classified_messages_schema.validate(classified_messages_df)
    return classified_messages_df


def form_classified_messages_errors_df(
    error_rows: List[Dict[str, Any]],
    classifier_id: int,
    classifier_version_id: int,
    job_run_id: int,
) -> pd.DataFrame:
    """Build a DataFrame for classified_messages_errors.

    Args:
        error_rows: List of dicts with phoenix_platform_message_id and error_json.
        classifier_id: ID of the classifier.
        classifier_version_id: Version ID of the classifier.
        job_run_id: Current job run ID.

    Returns:
        pd.DataFrame validated against classified_messages_errors_schema.
    """
    if not error_rows:
        raise ValueError("No errors to form classified messages errors DataFrame.")
    classified_messages_errors_df = pd.DataFrame(error_rows)
    classified_messages_errors_df["classifier_id"] = classifier_id
    classified_messages_errors_df["classifier_version_id"] = classifier_version_id
    classified_messages_errors_df["job_run_id"] = job_run_id
    classified_messages_errors_df = classified_messages_errors_df[
        [
            "classifier_id",
            "classifier_version_id",
            "phoenix_platform_message_id",
            "job_run_id",
            "error_json",
        ]
    ]
    classified_messages_errors.classified_messages_errors_schema.validate(
        classified_messages_errors_df
    )
    return classified_messages_errors_df


@prefect.task
def classify_with_concurrency(
    classifier: schemas.PerspectiveAPIClassifierPipeline,
    bigquery_dataset: str,
    job_run_id: int,
) -> None:
    """Classify messages using Perspective API Classifier with concurrency.

    This task is designed to be run with concurrency limit set to 1. It will ensure that only one
    of the inner `classify` calls runs at a time, which is necessary to avoid hitting the
    Perspective API rate limits - it in effect makes the `classify` function be in a queue. This is
    managed by the Prefect concurrency context manager.

    To achieve this, you will need to manually set up the concurrency limit in the Prefect UI, as
    well as setting the related but separate environment variables for the Perspective-API
    Classifier request limits in the Phiphi config.

    The recommended configuration is:
    - `perspective_api_classify_task`, set manually in prefect UI, set to concurrency 1 and active
    - PERSPECTIVE_API_REQUEST_LIMIT_FOR_PERIOD, config env variable, set to the QPS that the
      Perspective team has allocated for your API access
    - PERSPECTIVE_API_REQUEST_LIMIT_PERIOD_SECONDS, config env variable, set to 1
    """
    prefect_logger = prefect.get_run_logger()
    prefect_logger.info("Started Perspective API Classifier task with concurrency limit.")
    prefect_logger.info("Waiting for concurrency to be available...")
    with concurrency("perspective_api_classify_task", occupy=1):
        prefect_logger.info("Concurrency available, proceeding with classification.")
        return classify(classifier, bigquery_dataset, job_run_id)


@prefect.task
def classify(
    classifier: schemas.PerspectiveAPIClassifierPipeline,
    bigquery_dataset: str,
    job_run_id: int,
) -> None:
    """Classify messages using Perspective API Classifier."""
    prefect_logger = prefect.get_run_logger()
    # Prepare BQ query parameters
    generalised_messages_table_name = (
        f"{bigquery_dataset}."
        f"{pipeline_jobs_constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME}"
    )
    classified_messages_table_name = (
        f"{bigquery_dataset}.{pipeline_jobs_constants.CLASSIFIED_MESSAGES_TABLE_NAME}"
    )
    classified_messages_errors_table_name = (
        f"{bigquery_dataset}.{pipeline_jobs_constants.CLASSIFIED_MESSAGES_ERRORS_TABLE_NAME}"
    )

    bigquery_parameters = [
        bigquery.ScalarQueryParameter("classifier_id", "INT64", classifier.id),
        bigquery.ScalarQueryParameter(
            "classifier_version_id", "INT64", classifier.latest_version.version_id
        ),
        bigquery.ScalarQueryParameter("job_run_id", "INT64", job_run_id),
        bigquery.ScalarQueryParameter("batch_size", "INT64", BATCH_SIZE),
    ]

    client = bigquery.Client()

    # Get the total number of unclassified messages before starting the loop
    total_unclassified = get_total_unclassified_count(
        client,
        bigquery_parameters,
        generalised_messages_table_name,
        classified_messages_table_name,
        classified_messages_errors_table_name,
    )
    prefect_logger.info(f"Total unclassified messages found: {total_unclassified}")

    processed_count = 0

    # Batch loop
    while processed_count < total_unclassified:
        # Get a batch of unclassified messages
        unclassified_messages_df = get_unclassified_messages(
            client,
            bigquery_parameters,
            generalised_messages_table_name,
            classified_messages_table_name,
            classified_messages_errors_table_name,
        )

        if unclassified_messages_df.empty:
            prefect_logger.info("No more unclassified messages returned; breaking loop.")
            break

        # Classify messages in parallel
        class_dicts: List[dict] = []
        classification_errors: List[dict] = []
        with ThreadPoolExecutor(
            max_workers=config.settings.PERSPECTIVE_API_MAX_PARALLEL_WORKERS
        ) as executor:
            futures = []
            for _, row in unclassified_messages_df.iterrows():
                text = row["pi_text"]
                message_id = row["phoenix_platform_message_id"]
                prefect_logger.debug(f"Classifying message {message_id}")
                futures.append(executor.submit(classify_message, text, message_id, classifier))
            for future in as_completed(futures):
                class_dicts_for_single_message = future.result()
                prefect_logger.debug(f"Classified message {message_id}")
                prefect_logger.debug(f"Classes: {class_dicts_for_single_message}")
                if (
                    class_dicts_for_single_message
                    and "error_json" in class_dicts_for_single_message[0]
                ):
                    classification_errors.extend(class_dicts_for_single_message)
                else:
                    class_dicts.extend(class_dicts_for_single_message)

        # Currently we are just logging this but in the future it would be great to persist it and
        # make it viewable to the end user.
        prefect_logger.info(f"Successfully classified {len(class_dicts)} messages")
        prefect_logger.info(
            f"Failed to classify {len(classification_errors)} messages due to errors."
        )
        if classification_errors:
            errors_df = form_classified_messages_errors_df(
                classification_errors,
                classifier.id,
                classifier.latest_version.version_id,
                job_run_id,
            )
            utils.write_data(
                errors_df,
                bigquery_dataset,
                pipeline_jobs_constants.CLASSIFIED_MESSAGES_ERRORS_TABLE_NAME,
            )

        if class_dicts:
            classified_messages_df = form_classified_messages_df(
                class_dicts,
                classifier.id,
                classifier.latest_version.version_id,
                job_run_id,
            )
            utils.write_data(
                classified_messages_df,
                bigquery_dataset,
                pipeline_jobs_constants.CLASSIFIED_MESSAGES_TABLE_NAME,
            )

        # Update how many messages we've processed
        processed_count += len(unclassified_messages_df)
        prefect_logger.info(f"Processed {processed_count} messages of {total_unclassified} total.")
