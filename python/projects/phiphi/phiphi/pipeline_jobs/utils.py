"""Utility functions for data processing and uploading."""

import os
import re
import warnings

import pandas as pd
import pandas_gbq
import pandera.pandas as pa
from prefect import deployments, task
from prefect.concurrency.sync import rate_limit

from phiphi import config, utils
from phiphi.api.projects import job_runs


@task
async def run_flow_deployment_as_subflow(
    deployment_name: str,
    flow_params: dict,
    project_id: int,
    job_type: job_runs.schemas.ForeignJobType,
    job_source_id: int,
    job_run_id: int,
) -> None:
    """Run a Prefect flow as a subflow."""
    await deployments.run_deployment(
        name=deployment_name,
        parameters=flow_params,
        as_subflow=True,
        tags=[
            f"project_id:{project_id}",
            f"job_type:{job_type}",
            f"job_source_id:{job_source_id}",
            f"job_run_id:{job_run_id}",
        ],
    )


def write_data(
    df: pd.DataFrame,
    dataset: str,
    table: str,
    with_rate_limit: bool = True,
) -> None:
    """Upload DataFrame to BigQuery, or attempt to use BQ emulation.

    Warning: Not all BQ queries used in the pipelines are supported in the mock/emulated BQ
    environment. Use with caution.

    Future intention is to implement https://github.com/goccy/bigquery-emulator as a local emulator
    for testing, as well as a platform version that doesn't rely on GCP. Not currently implemented.


    Args:
        df (pd.DataFrame): DataFrame to be uploaded or saved.
        dataset (str): BigQuery dataset name.
        table (str): BigQuery table name.
        with_rate_limit (bool): Whether to apply rate limiting to the write operation.
    """
    if config.settings.USE_MOCK_BQ:
        warnings.warn(
            "Not all BQ queries used in the pipelines are supported in the mock/emulated BQ "
            " environment. Use with caution."
        )
        parquet_file_path = os.path.join(
            config.settings.MOCK_BQ_ROOT_DIR, dataset, table + ".parquet"
        )
        os.makedirs(os.path.dirname(parquet_file_path), exist_ok=True)

        if os.path.exists(parquet_file_path):
            existing_df = pd.read_parquet(parquet_file_path)
            df = pd.concat([existing_df, df])  # noqa: PD901

        df.to_parquet(parquet_file_path, index=False)
    else:
        if with_rate_limit:
            # Apply rate limiting to the write operation
            # This will limit the number of writes per second to avoid exceeding BigQuery quotas
            rate_limit(utils.form_bq_rate_limit_write_id(dataset, table))
        pandas_gbq.to_gbq(df, destination_table=f"{dataset}.{table}", if_exists="append")


def read_data(query: str, dataset: str, table: str) -> pd.DataFrame:
    """Read data from BigQuery or a local Parquet file based on configuration.

    Args:
        query (str): The SQL query to run when reading from BigQuery.
        dataset (str): BigQuery dataset name.
        table (str): BigQuery table name.

    Returns:
        pd.DataFrame: The resulting DataFrame from the query.
    """
    if config.settings.USE_MOCK_BQ:
        base_path = config.settings.MOCK_BQ_ROOT_DIR
        parquet_file_path = os.path.normpath(os.path.join(base_path, dataset, table + ".parquet"))
        if not parquet_file_path.startswith(base_path):
            raise Exception("Access to the specified path is not allowed.")
        if os.path.exists(parquet_file_path):
            full_table_df = pd.read_parquet(parquet_file_path)
            # Simulate SQL query using pandas query
            pd_query = translate_bq_to_pandas_query(query)
            return full_table_df.query(pd_query)
        else:
            raise FileNotFoundError(f"Parquet file not found at {parquet_file_path}")
    else:
        return pandas_gbq.read_gbq(query)  # type: ignore[no-any-return]


def translate_bq_to_pandas_query(bq_query: str) -> str:
    """Translate a simple BigQuery query to a Pandas DataFrame query."""
    # Extract the WHERE clause
    match = re.search(r"WHERE (.+)", bq_query, re.IGNORECASE)
    if not match:
        raise ValueError("Only simple WHERE clauses are supported.")
    where_clause = match.group(1)

    # Validate and sanitize the WHERE clause
    allowed_chars = re.compile(r"^[a-zA-Z0-9_ ='<>()]+$")
    if not allowed_chars.match(where_clause):
        raise ValueError("Invalid characters in WHERE clause.")

    # Replace BigQuery operators with Pandas equivalents
    pandas_query = where_clause.replace(" AND ", " and ").replace(" OR ", " or ")
    # Change "=" to "=="
    pandas_query = re.sub(r"(?<!=)=(?!=)", "==", pandas_query)

    # Ensure no dangerous functions or keywords are present
    dangerous_keywords = ["exec", "eval", "import", "os.", "sys.", "__"]
    if any(keyword in pandas_query for keyword in dangerous_keywords):
        raise ValueError("Dangerous keyword detected in query.")

    return pandas_query


def utc_datetime_column(nullable: bool) -> pa.Column:
    """Return a Pandera column for a UTC datetime which coerces.

    Should be used for columns that are expected to be UTC datetimes, and dfs should be passed
    through validation to ensure columns are coerced.

    This matches/will create a column with data type TIMESTAMP in BigQuery.
    """
    return pa.Column(
        pa.engines.pandas_engine.DateTime(  # type: ignore[call-arg]
            unit="ms",
            tz="UTC",
        ),
        coerce=True,
        nullable=nullable,
    )


def col_to_utc_ms(col: pd.Series) -> pd.Series:
    """Return a tz-aware UTC datetime column with millisecond resolution.

    Args:
        col: Datetime-like series (tz-aware or naive).

    Returns:
        Series with dtype datetime64[ms, UTC].
    """
    s = pd.to_datetime(col, utc=True)
    # If your pandas supports direct astype to ms+tz, this is the simplest:
    try:
        # Dropping the localisation for the mypy
        s_naive = s.dt.tz_localize(None)
        s_ms = s_naive.astype("datetime64[ms]")
        s_utc = s_ms.dt.tz_localize("UTC")
        return s_utc
    except TypeError:
        # Fallback that works broadly: truncate to ms via integer ns → ms math.
        # ns since epoch → drop to ms → back to datetime (UTC).
        ns: pd.Series = s.view("int64")
        ms_ns: pd.Series = (ns // 1_000_000) * 1_000_000
        return pd.to_datetime(ms_ns, utc=True)
