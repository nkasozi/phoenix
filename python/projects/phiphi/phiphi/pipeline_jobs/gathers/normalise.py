"""Normalise functionality for the gather pipeline job."""

import dataclasses
import json
from datetime import datetime
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

import pandas as pd
import prefect

from phiphi.api.projects import gathers
from phiphi.config import settings
from phiphi.pipeline_jobs import constants as pipeline_jobs_constants
from phiphi.pipeline_jobs import gather_batches, generalised_messages, utils
from phiphi.pipeline_jobs.gathers import normalisers

NormaliserFuncType = Callable[[Dict], Dict | None]

APIFY_X_CHILD_TYPES = [
    gathers.schemas.ChildTypeName.apify_x_advanced_searches_posts_comments,
    gathers.schemas.ChildTypeName.apify_x_simple_searches_posts_comments,
]


@dataclasses.dataclass
class NormalisationMessageCounts:
    """Counts of messages processed during normalisation."""

    total_processed: int
    successfully_processed: int
    error_count: int


def flatten_danek_instagram_posts(
    json_blob: dict,
) -> Iterator[Tuple[Optional[dict], Optional[dict]]]:
    """Flatten a Danek Instagram posts JSON blob to yield single post dicts.

    Handles the new structure: {"items": [{"node": {post}, ...}, ...]}, which is different from
    the default usage which expects a list of dicts: [{post}, {post}, ...]

    Yields:
        Tuple[Optional[dict], Optional[dict]]:
            - (node, None): when a valid post dict is found under "node"
            - (None, item): when an item is malformed or missing a valid "node"
            - (None, json_blob): when the input is empty or invalid

    Notes:
        - This function preserves malformed entries as errors instead of silently dropping them,
          allowing downstream logging and debugging.
        - If no "items" or "child_comments" key is present, the entire `json_blob` is treated as
        a single post.
    """
    if not json_blob:
        yield None, json_blob
        return

    items = json_blob.get("items")
    # If it's a comment, it has parent_post_id injected by the gather batch manager
    parent_post_id = json_blob.get("parent_post_id")

    child_comment_items = json_blob.get("child_comments")
    if items and isinstance(items, list):
        for item in items:
            node = item.get("node")
            if node and isinstance(node, dict):
                if parent_post_id:
                    node["parent_post_id"] = parent_post_id
                yield node, None
            else:
                yield None, item  # <-- preserve bad item as error
    elif child_comment_items and isinstance(child_comment_items, list):
        for item in child_comment_items:
            if item and isinstance(item, dict):
                if parent_post_id:
                    item["parent_post_id"] = parent_post_id
                yield item, None
            else:
                yield None, item
    else:
        yield json_blob, None


def prepare_batch_json_for_normalisation(
    batch_json: List[Any], child_type_name: gathers.schemas.ChildTypeName
) -> tuple[List[Dict], List[Any]]:
    """Convert batch JSON into a flat list of dicts, separating invalid items as errors.

    Args:
        batch_json: List of Union[dict,Any] from a gather batch. Will send non-dicts to the
            error list
        child_type_name: The gather type enum to decide flattening.

    Returns:
        Tuple:
            A flat list of dicts, each representing a single post/comment.
            A flat list of errors
    """
    if child_type_name in [
        gathers.schemas.ChildTypeName.danek_instagram_posts,
        gathers.schemas.ChildTypeName.danek_instagram_comments,
    ]:
        flattened = []
        errors = []

        for blob in batch_json:
            if not isinstance(blob, dict):
                errors.append(blob)
                continue

            for node, err in flatten_danek_instagram_posts(blob):
                if err:
                    errors.append(err)
                elif node:
                    flattened.append(node)

        return flattened, errors

    return batch_json, []


def normalise_batch(
    normaliser: NormaliserFuncType,
    batch_json: List[Dict],
    gather_id: int,
    gather_child_type: gathers.schemas.ChildTypeName,
    gather_batch_id: int,
    gathered_at: datetime,
) -> tuple[pd.DataFrame | None, list[dict]]:
    """Process a list of JSON blobs and normalize them into a DataFrame."""
    errors = []
    normalized_records = []

    # Attempt to normalize each blob
    # Collect any errors and continue processing the rest
    for blob in batch_json:
        result = normaliser(blob)
        if result is None:
            errors.append(blob)
        else:
            normalized_records.append(result)

            if gather_child_type in APIFY_X_CHILD_TYPES:
                retweeted_post = normalisers.extract_retweeted_tweet_as_post(blob)
                if retweeted_post is not None:
                    normalized_records.append(retweeted_post)

                quoted_post = normalisers.extract_quoted_tweet_as_post(blob)
                if quoted_post is not None:
                    normalized_records.append(quoted_post)

    if not normalized_records:
        return None, errors

    messages_df = pd.DataFrame(normalized_records)
    messages_df = generalised_messages.coerce_optional_values(messages_df)

    # Add constant columns to the DataFrame
    messages_df["gather_id"] = gather_id
    messages_df["gather_batch_id"] = gather_batch_id
    messages_df["gathered_at"] = gathered_at
    messages_df["gather_type"] = gather_child_type

    # If x gather, `platform` and `data_type` are set in the normaliser, as it outputs both posts
    # and comments.
    if gather_child_type not in [
        gathers.schemas.ChildTypeName.manual_upload,
        gathers.schemas.ChildTypeName.apify_x_advanced_searches_posts_comments,
        gathers.schemas.ChildTypeName.apify_x_simple_searches_posts_comments,
    ]:
        gather_creation_defaults = gathers.child_types.get_gather_project_db_defaults(
            gather_child_type
        )
        messages_df["platform"] = gather_creation_defaults.platform
        messages_df["data_type"] = gather_creation_defaults.data_type

    messages_df["phoenix_processed_at"] = datetime.utcnow()

    # Validate the DataFrame using the schema
    validated_df = generalised_messages.validate(messages_df)

    return validated_df, errors


gather_normalisation_map: Dict[gathers.schemas.ChildTypeName, NormaliserFuncType] = {
    gathers.schemas.ChildTypeName.apify_facebook_posts: (
        normalisers.normalise_single_facebook_posts_json
    ),
    gathers.schemas.ChildTypeName.apify_facebook_search_posts: (
        normalisers.normalise_single_facebook_search_posts_json
    ),
    gathers.schemas.ChildTypeName.apify_facebook_comments: (
        normalisers.normalise_single_facebook_comments_json
    ),
    gathers.schemas.ChildTypeName.apify_tiktok_accounts_posts: (
        normalisers.normalise_single_tiktok_posts_json
    ),
    gathers.schemas.ChildTypeName.apify_tiktok_hashtags_posts: (
        normalisers.normalise_single_tiktok_posts_json
    ),
    gathers.schemas.ChildTypeName.apify_tiktok_searches_posts: (
        normalisers.normalise_single_tiktok_posts_json
    ),
    gathers.schemas.ChildTypeName.apify_tiktok_comments: (
        normalisers.normalise_single_tiktok_comments_json
    ),
    gathers.schemas.ChildTypeName.apify_x_advanced_searches_posts_comments: (
        normalisers.normalise_single_x_advanced_searches_posts_comments_json
    ),
    gathers.schemas.ChildTypeName.apify_x_simple_searches_posts_comments: (
        normalisers.normalise_single_x_advanced_searches_posts_comments_json
    ),
    gathers.schemas.ChildTypeName.danek_facebook_searches_posts: (
        normalisers.normalise_single_danek_facebook_searches_posts_json
    ),
    gathers.schemas.ChildTypeName.danek_instagram_posts: (
        normalisers.normalise_single_danek_instagram_posts_json
    ),
    gathers.schemas.ChildTypeName.danek_instagram_comments: (
        normalisers.normalise_single_instagram_comments_json
    ),
    gathers.schemas.ChildTypeName.manual_upload: (normalisers.normalise_single_manual_upload_json),
    # Add other gather types and their corresponding normalization functions here
}


@prefect.task
def normalise_batches(
    gather_job_run_pairs: list[tuple[int, int]],
    bigquery_dataset: str,
    batch_of_batches_size: int = settings.DEFAULT_BATCH_OF_BATCHES_SIZE,
) -> NormalisationMessageCounts:
    """Normalize batches and write to a BigQuery table.

    This function reads multiple batches at once from the gather_batches table for multiple
    gather-job_run pairs, normalizes them, and writes the normalized data to the
    generalised_messages table.

    Args:
        gather_job_run_pairs (list[tuple[int, int]]): List of (gather_id, job_run_id) pairs.
        bigquery_dataset (str): The BigQuery dataset.
        batch_of_batches_size (int, optional): The number of batches to read at once. Defaults to
            settings.DEFAULT_BATCH_OF_BATCHES_SIZE.

    Returns:
        NormalisationMessageCounts: The result of the normalisation.
    """
    prefect_logger = prefect.get_run_logger()

    gather_job_run_filter = ", ".join(
        [f"({gather_id}, {job_run_id})" for gather_id, job_run_id in gather_job_run_pairs]
    )

    total_processed = 0
    successfully_processed = 0
    error_count = 0
    while True:
        # Using a CTE to order and limit the batches to mean that big query process less data:
        # In that it does the order and limit on a (much) smaller dataset and then joins back to
        # get the full rows. Since most of the data is in `json_data` this should reduce the costs
        # and chance of running into BQ limits.
        # Ordering by gathered_at DESC so that the most recent batches are processed first. This
        # prioritises newer data when a gather has been re-run multiple times.
        # gathered_at is included in the JOIN because BigQuery does not enforce unique constraints,
        # so (gather_id, job_run_id, batch_id) alone may match more rows than the CTE selected.
        query = f"""
            WITH ordered_batches AS (
              SELECT gather_id, job_run_id, batch_id, gathered_at
              FROM {bigquery_dataset}.{pipeline_jobs_constants.GATHER_BATCHES_TABLE_NAME}
              WHERE (gather_id, job_run_id) IN ({gather_job_run_filter})
              ORDER BY gathered_at DESC, gather_id ASC, job_run_id ASC, batch_id ASC
              LIMIT {batch_of_batches_size} OFFSET {total_processed}
            )
            SELECT gb.*
            FROM {bigquery_dataset}.{pipeline_jobs_constants.GATHER_BATCHES_TABLE_NAME} gb
            INNER JOIN ordered_batches ob
              ON gb.gather_id = ob.gather_id
              AND gb.job_run_id = ob.job_run_id
              AND gb.batch_id = ob.batch_id
              AND gb.gathered_at = ob.gathered_at
        """
        batches_df = utils.read_data(
            query,
            dataset=bigquery_dataset,
            table=pipeline_jobs_constants.GATHER_BATCHES_TABLE_NAME,
        )

        if batches_df.empty:
            break

        validated_batches_df = gather_batches.gather_batches_schema.validate(batches_df)

        normalized_data = []

        for _, batch in validated_batches_df.iterrows():
            prefect_logger.info(
                f"Normalizing batch {batch.batch_id} for gather_id "
                f"{batch.gather_id}, job_run_id {batch.job_run_id}"
                f" gathered at {batch.gathered_at}"
            )
            child_type_name = gathers.schemas.ChildTypeName(batch.gather_type)
            norm_func = gather_normalisation_map[child_type_name]

            batch_json = json.loads(batch.json_data)
            batch_json_flattened, flatten_errors = prepare_batch_json_for_normalisation(
                batch_json, child_type_name
            )
            normalized_df, errors = normalise_batch(
                normaliser=norm_func,
                batch_json=batch_json_flattened,
                gather_id=batch.gather_id,
                gather_child_type=child_type_name,
                gather_batch_id=batch.batch_id,
                gathered_at=batch.gathered_at,
            )
            errors.extend(flatten_errors)
            if errors:
                prefect_logger.warning(
                    "Batch %s (gather_id: %s, job_run_id: %s) had %d errors during normalization.",
                    batch.batch_id,
                    batch.gather_id,
                    batch.job_run_id,
                    len(errors),
                )
                prefect_logger.info("Errors: %s", errors)
                error_count += len(errors)

            if normalized_df is not None:
                normalized_data.append(normalized_df)

        if normalized_data:
            all_normalized_df = pd.concat(normalized_data, ignore_index=True)
            utils.write_data(
                df=all_normalized_df,
                dataset=bigquery_dataset,
                table=pipeline_jobs_constants.GENERALISED_MESSAGES_TABLE_NAME,
            )

            start_batch = validated_batches_df.iloc[0]
            end_batch = validated_batches_df.iloc[-1]
            prefect_logger.info(
                f"Processed batches from (gather_id: {start_batch.gather_id}, job_run_id: "
                f"{start_batch.job_run_id}, batch_id: {start_batch.batch_id}) "
                f"to (gather_id: {end_batch.gather_id}, job_run_id: {end_batch.job_run_id}, "
                f"batch_id: {end_batch.batch_id})"
            )
            successfully_processed += len(normalized_data)

        total_processed += batch_of_batches_size
    return NormalisationMessageCounts(
        total_processed=total_processed,
        successfully_processed=successfully_processed,
        error_count=error_count,
    )


def get_gather_and_job_run_ids(
    bigquery_dataset: str, gather_ids: Optional[list[int]] = None
) -> pd.DataFrame:
    """Get the unique gather ID and job run ID for all gather batches.

    Args:
        bigquery_dataset: The BigQuery dataset.
        gather_ids (Optional): The gather IDs to filter for. If none then all gathers will be
            gotten.

    Returns:
        DataFrame: The gather ID and job run ID for all gather batches.
    """
    where_query = ""
    if gather_ids:
        gather_ids_str = ",".join([str(gather_id) for gather_id in gather_ids])
        where_query += f" WHERE gather_id IN ({gather_ids_str}) "
    query = f"""
        SELECT
            gather_id, job_run_id
        FROM {bigquery_dataset}.{pipeline_jobs_constants.GATHER_BATCHES_TABLE_NAME}
        {where_query}
        GROUP BY 1, 2
    """
    return utils.read_data(
        query, dataset=bigquery_dataset, table=pipeline_jobs_constants.GATHER_BATCHES_TABLE_NAME
    )
