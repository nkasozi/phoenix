"""Tables and schemas for the generalised_messages.

Important:
    The generalised_messages_table and generalised_messages_schema must be kept in sync. The order
    of columns in the generalised_messages_table definition must match the order of columns in the
    schema.
"""

import datetime

import pandas as pd
import pandera.pandas as pa
import sqlalchemy as sa

from phiphi import project_db
from phiphi.api.projects.gathers import schemas
from phiphi.pipeline_jobs import constants
from phiphi.pipeline_jobs import utils as pipeline_jobs_utils

# TODO: should add BQ cluster specification on columns:
#  - platform, data_type, phoenix_platform_message_id, platform_message_last_updated_at
# Even better would be including `phoenix_processed_at` on the end, but BQ limits to 4 cols.
# We could assuming that messages IDs are unique across platforms, but I don't think this is really
# guaranteed.
generalised_messages_schema = pa.DataFrameSchema(
    {
        "gather_id": pa.Column(pa.Int, nullable=False),
        "gather_batch_id": pa.Column(pa.Int, nullable=False),
        "gathered_at": pipeline_jobs_utils.utc_datetime_column(nullable=False),
        "phoenix_processed_at": pipeline_jobs_utils.utc_datetime_column(nullable=False),
        "gather_type": pa.Column(
            pa.String,
            checks=pa.Check.isin([e.value for e in schemas.ChildTypeName]),
            nullable=False,
        ),
        # NOTE: combination of (platform, data_type, pi_platform_message_id) should give a unique
        # message, but it won't be a unique row as we process the same message multiple times.
        # Doing groupby on these columns then getting MAX(phoenix_processed_at) will give the
        # latest set of unique messages. `phoenix_platform_message_id` can be used instead of
        # `pi_platform_message_id` in the groupby also.
        "platform": pa.Column(
            pa.String,
            checks=pa.Check.isin([e.value for e in schemas.Platform]),
            nullable=False,
        ),
        "data_type": pa.Column(
            pa.String, checks=pa.Check.isin([e.value for e in schemas.DataType]), nullable=False
        ),
        "pi_platform_message_id": pa.Column(pa.String, nullable=True),
        "pi_platform_message_author_id": pa.Column(pa.String, nullable=True),
        "pi_platform_message_author_name": pa.Column(pa.String, nullable=True),
        # For comments this is the post that the comment is on OR the comment that the reply is on.
        "pi_platform_parent_message_id": pa.Column(pa.String, nullable=True),
        # For comments this is the root post for that comment. For posts this is None.
        "pi_platform_root_message_id": pa.Column(pa.String, nullable=True),
        "pi_text": pa.Column(pa.String, nullable=True),
        "pi_platform_message_url": pa.Column(pa.String, nullable=True),
        "platform_message_last_updated_at": pipeline_jobs_utils.utc_datetime_column(
            nullable=False
        ),
        # Hash of `pi_platform_message_id`.
        "phoenix_platform_message_id": pa.Column(pa.String, nullable=False),
        # Hash of `pi_platform_message_author_id`.
        "phoenix_platform_message_author_id": pa.Column(pa.String, nullable=False),
        # Note, no version of the author name, as the id serves as the non-pi identifier.
        # Hash of `pi_platform_parent_message_id`.
        "phoenix_platform_parent_message_id": pa.Column(pa.String, nullable=True),
        "phoenix_platform_root_message_id": pa.Column(pa.String, nullable=True),
        # Stats
        # These are not nullable as should be set to 0 if not present.
        "like_count": pa.Column(pa.Int, nullable=False),
        "share_count": pa.Column(pa.Int, nullable=False),
        "comment_count": pa.Column(pa.Int, nullable=False),
        # Specific to platform
        # For the moment we are adding them in to generalised_messages with the idea that
        # generalised messages is going to be refactored to store in a more optimal way in the
        # future.
        # Has to be an Int64 so we can make it Nullable
        "tiktok_post_plays": pa.Column(pa.Int64, nullable=True),
        "x_post_retweeted_id": pa.Column(pa.String, nullable=True),
        "x_is_quote": pa.Column(pa.Bool, nullable=True),
        "x_is_reply": pa.Column(pa.Bool, nullable=True),
    }
)

# It is important that this Table definition is kept in sync with the generalised_messages_schema.
# Including the order!
generalised_messages_table = sa.Table(
    constants.GENERALISED_MESSAGES_TABLE_NAME,
    project_db.metadata,
    sa.Column("gather_id", sa.Integer, nullable=False),
    sa.Column("gather_batch_id", sa.Integer, nullable=False),
    sa.Column("gathered_at", sa.TIMESTAMP, nullable=False),
    sa.Column("phoenix_processed_at", sa.TIMESTAMP, nullable=False),
    sa.Column("gather_type", sa.String, nullable=False),
    sa.Column("platform", sa.String, nullable=False),
    sa.Column("data_type", sa.String, nullable=False),
    sa.Column("pi_platform_message_id", sa.String, nullable=True),
    sa.Column("pi_platform_message_author_id", sa.String, nullable=True),
    sa.Column("pi_platform_message_author_name", sa.String, nullable=True),
    sa.Column("pi_platform_parent_message_id", sa.String, nullable=True),
    sa.Column("pi_platform_root_message_id", sa.String, nullable=True),
    sa.Column("pi_text", sa.String, nullable=True),
    sa.Column("pi_platform_message_url", sa.String, nullable=True),
    sa.Column("platform_message_last_updated_at", sa.TIMESTAMP, nullable=False),
    sa.Column("phoenix_platform_message_id", sa.String, nullable=False),
    sa.Column("phoenix_platform_message_author_id", sa.String, nullable=False),
    sa.Column("phoenix_platform_parent_message_id", sa.String, nullable=True),
    sa.Column("phoenix_platform_root_message_id", sa.String, nullable=True),
    sa.Column("like_count", sa.Integer, nullable=False),
    sa.Column("share_count", sa.Integer, nullable=False),
    sa.Column("comment_count", sa.Integer, nullable=False),
    # Although this is has a Int64 type in the schema, Integer in bigquery covers the same range.
    sa.Column("tiktok_post_plays", sa.Integer, nullable=True),
    sa.Column("x_post_retweeted_id", sa.String, nullable=True),
    sa.Column("x_is_quote", sa.Boolean, nullable=True),
    sa.Column("x_is_reply", sa.Boolean, nullable=True),
)


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and reorder DataFrame columns according to a Pandera schema.

    This function performs two key operations:
    1. Validates the DataFrame against a predefined Pandera schema
    2. Reorders the columns to match the schema's column order

    The function addresses a limitation in Pandera's validation process where column
    ordering is not preserved during validation. This is particularly important when
    the DataFrame will be used to create database tables, as it ensures consistent
    column ordering between the DataFrame and SQLAlchemy table definitions.

    Args:
        df (pd.DataFrame): Input DataFrame to validate and reorder.
            Must contain all columns defined in generalised_messages_schema.

    Returns:
        pd.DataFrame: Validated DataFrame with columns reordered to match the schema.

    Raises:
        ValueError: If any columns defined in the schema are missing from the DataFrame.
        pandera.errors.SchemaError: If the DataFrame fails schema validation
            (wrong data types, invalid values, etc.).
    """
    validated_df = generalised_messages_schema.validate(df)
    schema_columns = list(generalised_messages_schema.columns.keys())

    # Verify all table columns exist in the DataFrame
    missing_columns = set(schema_columns) - set(validated_df.columns)
    if missing_columns:
        raise ValueError(f"DataFrame is missing columns defined in table: {missing_columns}")

    # Reorder DataFrame columns to match table definition
    return validated_df[schema_columns]


def create_example(n_rows: int) -> pd.DataFrame:
    """Create a test DataFrame that matches the generalised_messages schema.

    Args:
        n_rows: Number of rows to generate in the test DataFrame

    Returns:
        pd.DataFrame: DataFrame with test data matching the generalised_messages schema
    """
    deduped_general_messages_df = pd.DataFrame(
        {
            "gather_id": range(1, n_rows + 1),  # Unique gather IDs
            "gather_batch_id": range(1, n_rows + 1),  # Unique batch IDs
            "gathered_at": [datetime.datetime.now(datetime.UTC)] * n_rows,
            "phoenix_processed_at": [datetime.datetime.now(datetime.UTC)] * n_rows,
            "gather_type": ["apify_facebook_posts"] * n_rows,
            "platform": ["facebook"] * n_rows,
            "data_type": ["posts"] * n_rows,
            "pi_platform_message_id": [f"orig_{i}" for i in range(n_rows)],  # Already unique
            "pi_platform_message_author_id": [
                f"author_{i}" for i in range(n_rows)
            ],  # Already unique
            "pi_platform_message_author_name": [
                f"Author {i}" for i in range(n_rows)
            ],  # Already unique
            "pi_platform_parent_message_id": [None] * n_rows,
            "pi_platform_root_message_id": [None] * n_rows,
            "pi_text": [""] * n_rows,  # This will be overwritten later in the test
            "pi_platform_message_url": [
                f"https://example.com/{i}" for i in range(n_rows)
            ],  # Already unique
            "platform_message_last_updated_at": [datetime.datetime.now(datetime.UTC)] * n_rows,
            "phoenix_platform_message_id": [""]
            * n_rows,  # This will be overwritten later in the test
            "phoenix_platform_message_author_id": [
                f"phoenix_author_{i}" for i in range(n_rows)
            ],  # Already unique
            "phoenix_platform_parent_message_id": [None] * n_rows,
            "phoenix_platform_root_message_id": [None] * n_rows,
            "like_count": range(100, 100 + n_rows),  # Unique like counts for more realistic data
            "share_count": range(50, 50 + n_rows),  # Unique share counts for more realistic data
            "comment_count": range(
                25, 25 + n_rows
            ),  # Unique comment counts for more realistic data
            "tiktok_post_plays": [None] * n_rows,
            "x_post_retweeted_id": [None] * n_rows,
            "x_is_quote": [None] * n_rows,
            "x_is_reply": [None] * n_rows,
        }
    )

    deduped_general_messages_df = coerce_optional_values(deduped_general_messages_df)
    return validate(deduped_general_messages_df)


def coerce_optional_values(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce optional columns to correct types.

    This function ensures that optional columns in the DataFrame are coerced to the correct
    types as defined in the generalised_messages schema. This is particularly important for
    nullable integer columns, which should be of type 'Int64' to properly handle null values.

    Args:
        df (pd.DataFrame): Input DataFrame with potential optional columns.

    Returns:
        pd.DataFrame: DataFrame with optional columns coerced to correct types.
    """
    if "tiktok_post_plays" in df.columns:
        df["tiktok_post_plays"] = df["tiktok_post_plays"].astype("Int64")
    if "x_is_quote" in df.columns:
        df["x_is_quote"] = df["x_is_quote"].astype("bool")
    if "x_is_reply" in df.columns:
        df["x_is_reply"] = df["x_is_reply"].astype("bool")
    return df
