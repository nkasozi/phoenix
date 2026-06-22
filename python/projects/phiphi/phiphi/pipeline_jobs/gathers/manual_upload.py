"""Manual upload pipeline gathers."""

import logging

import pandas as pd
import pandera.pandas as pa

from phiphi.api.projects.gathers import schemas
from phiphi.api.projects.gathers.manual_upload import schemas as manual_upload_schemas
from phiphi.pipeline_jobs.gathers import gather_batch_write_managers
from phiphi.pipeline_jobs.gathers import types as gather_types

logger = logging.getLogger(__name__)

manual_upload_schema = pa.DataFrameSchema(
    {
        "platform": pa.Column(
            pa.String,
            checks=pa.Check.isin([e.value for e in schemas.Platform]),
            nullable=False,
        ),
        "data_type": pa.Column(
            pa.String, checks=pa.Check.isin([e.value for e in schemas.DataType]), nullable=False
        ),
        "message_id_pi": pa.Column(pa.String, nullable=False, coerce=True),
        "message_author_id_pi": pa.Column(pa.String, nullable=False, coerce=True),
        "message_author_name_pi": pa.Column(pa.String, nullable=False, coerce=True),
        # For comments this is the post that the comment is on OR the comment that the reply is on.
        "comment_replied_to_id_pi": pa.Column(pa.String, nullable=True, coerce=True),
        # For comments this is the root post for that comment. For posts this is None.
        "comment_parent_post_id_pi": pa.Column(pa.String, nullable=True, coerce=True),
        "message_text_pi": pa.Column(pa.String, nullable=False),
        "message_url_pi": pa.Column(pa.String, nullable=False, coerce=True),
        "message_datetime": pa.Column(
            pa.engines.pandas_engine.DateTime(  # type: ignore[call-arg]
                unit="ms",
                tz="UTC",
                to_datetime_kwargs={"utc": True, "format": "ISO8601"},
            ),
            coerce=True,
            nullable=False,
        ),
        # Stats
        # These are not nullable as should be set to 0 if not present.
        "like_count": pa.Column(pa.Int, nullable=False, default=0, coerce=True),
        "share_count": pa.Column(pa.Int, nullable=False, default=0, coerce=True),
        "comment_count": pa.Column(pa.Int, nullable=False, default=0, coerce=True),
        "tiktok_post_plays": pa.Column(pa.Int64, nullable=True, default=None),
        "x_post_retweeted_id": pa.Column(pa.String, nullable=True, default=None, coerce=True),
        "x_is_quote": pa.Column(pa.Bool, nullable=True, default=None, coerce=True),
        "x_is_reply": pa.Column(pa.Bool, nullable=True, default=None, coerce=True),
    },
    strict=True,
)


def to_json(manual_upload_df: pd.DataFrame) -> str:
    """Convert manual upload DataFrame to JSON.

    This is needed as to_json will convert datetimes to integers, this then allows for a more
    controlled conversion to JSON.

    Args:
        manual_upload_df: DataFrame containing manual upload data.

    Returns:
        JSON string.
    """
    formatted_df = manual_upload_df.copy()

    formatted_df["message_datetime"] = formatted_df["message_datetime"].dt.strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    return formatted_df.to_json(orient="records")


def convert_manual_upload_row_to_dict(row: pd.Series) -> dict:
    """Convert a manual upload DataFrame row to a dictionary with proper datetime formatting.

    Args:
        row: A single row from a manual upload DataFrame.

    Returns:
        Dictionary representation of the row with formatted datetime.
    """
    row_dict = row.to_dict()
    # Format datetime properly for JSON serialization
    if "message_datetime" in row_dict and pd.notna(row_dict["message_datetime"]):
        row_dict["message_datetime"] = row_dict["message_datetime"].strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )
    return row_dict


def validate_manual_upload_df(manual_upload_df: pd.DataFrame) -> pd.DataFrame:
    """Validate a manual upload DataFrame against the schema.

    Args:
        manual_upload_df: DataFrame containing manual upload data.

    Returns:
        Validated DataFrame.
    """
    if "tiktok_post_plays" in manual_upload_df.columns:
        manual_upload_df["tiktok_post_plays"] = manual_upload_df["tiktok_post_plays"].astype(
            "Int64"
        )
    # validate the manual_upload_df
    validated_df = manual_upload_schema.validate(manual_upload_df)
    return validated_df


def write_manual_upload_to_gather_batches(
    manual_upload_gather: manual_upload_schemas.ManualUploadGatherResponse,
    write_manager: gather_batch_write_managers.GatherBatchWriteManager,
) -> gather_types.ScrapeResponse:
    """Write manual upload data to gather batches using GatherBatchWriteManager.

    This function reads the manual_uploaded data in chunks and writes it to gather batches
    using the same GatherBatchWriteManager used by other gather types.

    Memory-based batching is used to ensure batches stay within BigQuery's row size limits.

    Args:
        manual_upload_gather: Manual upload gather response.
        write_manager: GatherBatchWriteManager to handle writing the data.

    Returns:
        Scrape response.
    """
    # Read in chunks to avoid loading entire file into memory
    # Use a conservative estimate of rows per chunk
    estimated_rows_per_chunk = 10000
    read_chunk_size = estimated_rows_per_chunk

    # Iterate through CSV in batches
    # read_csv support gs and s3 paths
    # https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
    for df_batch in pd.read_csv(manual_upload_gather.file_url, chunksize=read_chunk_size):
        # Validate the batch
        validated_df = validate_manual_upload_df(df_batch)

        # Add each row to the write manager
        for _, row in validated_df.iterrows():
            row_dict = convert_manual_upload_row_to_dict(row)
            write_manager.add(row_dict)

    # Complete the write and get results
    results = write_manager.complete_write()

    return gather_types.ScrapeResponse(
        total_items=results.total_items_processed,
        total_batches=results.total_batches_processed,
        total_cost=0,
    )
