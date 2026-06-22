"""Dataframe Writer module.

This module contains the interface and implementations for writing dataframes in different ways.
These different ways, or strategies, can be used to write data in optimal ways to bigquery or
switching out the writer for testing purposes.
"""

import dataclasses
import logging
from typing import Protocol

import pandas as pd
import pandas_gbq
from prefect.concurrency.sync import rate_limit

from phiphi import utils
from phiphi.pipeline_jobs import constants

logger = logging.getLogger(__name__)

# Timeout in seconds for acquiring a rate limit slot.
# If a slot cannot be acquired within this time, the write will proceed anyway.
# This prevents jobs from hanging indefinitely if there's an issue with concurrency limits.
RATE_LIMIT_TIMEOUT_SECS = 600  # 10 minutes

# Conversion factor from megabytes to bytes
MB_TO_BYTES = 2**20

# Use deep=True to get accurate memory usage including string data, not just pointers
# Without deep=True, string columns are severely underestimated (only 8 bytes per pointer counted)
MEMORY_USAGE_DEEP = True


@dataclasses.dataclass
class WriteResults:
    """A dataclass representing a completed write."""

    total_rows_processed: int = 0


class IDataFrameWriter(Protocol):
    """Interface for the data frame writer.

    Protocol is used so no inheritance is required but the typing checks that the given class has
    the required methods.

    The writer should be able to add a batch of items to the collection and flush the writing. In
    general code that uses the writer should not call write directly but should call the methods
    `add` to add a batch of items and `flush` that can be used to force or complete the writing.
    """

    def add(self, df: pd.DataFrame) -> None:
        """Add a batch of items to the collection."""
        pass

    def flush(self) -> WriteResults:
        """Flush the collection and write the items."""
        pass


@dataclasses.dataclass
class DummyWriteResults(WriteResults):
    """A dataclass representing a completed dummy writer."""

    dataframe: pd.DataFrame = dataclasses.field(default_factory=pd.DataFrame)


class DummyWriter:
    """A writer that collects data in an in-memory list.

    This can be used for testing and dummying out other writers that persist data.
    """

    def __init__(self) -> None:
        """Initialise the collector."""
        self.dataframe = pd.DataFrame()

    def add(self, df: pd.DataFrame) -> None:
        """Add a dataframe of items to the collection."""
        self.dataframe = pd.concat([self.dataframe, df])

    def flush(self) -> DummyWriteResults:
        """Flush the collection and write the items."""
        # No need to flush as we are writing to memory
        return DummyWriteResults(
            total_rows_processed=self.dataframe.shape[0], dataframe=self.dataframe
        )


class BigQueryDataFrameWriter:
    """Write dataframes to BigQuery table with batching and memory management.

    Buffers dataframes in memory and writes to BigQuery when the buffer would exceed
    max_inmemory_mb. This balances two competing goals:
    (a) Minimizing writes to BigQuery (due to rate limits: max writes per day and per 10 seconds)
    (b) Keeping process memory footprint below a threshold

    Memory behavior: Dataframes exceeding max_inmemory_mb are written immediately without
    buffering to prevent memory spikes. For smaller dataframes, memory can temporarily exceed
    the limit when both the buffer and an incoming dataframe are in memory simultaneously
    during concatenation.
    """

    def __init__(
        self,
        dataset: str,
        table: str,
        max_inmemory_mb: int = constants.DEFAULT_WRITER_MAX_INMEMORY_MB,
    ):
        """Initialise the writer.

        Args:
            dataset: BigQuery dataset name.
            table: BigQuery table name.
            max_inmemory_mb: Soft memory limit in megabytes for the buffer. Dataframes exceeding
                this limit are written immediately without buffering. For smaller dataframes, the
                buffer is flushed when buffer plus incoming dataframe would exceed this limit.
        """
        self.dataset = dataset
        self.table = table
        # Convert to bytes for memory usage
        self.max_inmemory_bytes = max_inmemory_mb * MB_TO_BYTES
        self.total_rows_processed = 0
        self.dataframe = pd.DataFrame()

    def add(self, df: pd.DataFrame) -> None:
        """Add a dataframe to the buffer, writing immediately if it exceeds the memory limit.

        Dataframes exceeding max_inmemory_bytes are written directly to BigQuery without
        buffering to prevent memory spikes. For smaller dataframes, if the buffer and incoming
        dataframe together exceed the limit, the buffer is flushed first before adding the new
        dataframe. This keeps memory bounded while batching writes to minimize BigQuery API calls.

        Args:
            df: Dataframe to add to the buffer.
        """
        self.total_rows_processed += df.shape[0]
        df_memory_bytes = df.memory_usage(deep=MEMORY_USAGE_DEEP).sum()
        buffer_memory_bytes = self.dataframe.memory_usage(deep=MEMORY_USAGE_DEEP).sum()

        logger.info(
            f"Buffer: {buffer_memory_bytes / MB_TO_BYTES:.2f}MB ({self.dataframe.shape[0]} rows), "
            f"Incoming: {df_memory_bytes / MB_TO_BYTES:.2f}MB ({df.shape[0]} rows), "
            f"Limit: {self.max_inmemory_bytes / MB_TO_BYTES:.2f}MB"
        )

        # Check if combined memory would exceed limit
        if buffer_memory_bytes + df_memory_bytes > self.max_inmemory_bytes:
            self.flush()

        self.dataframe = pd.concat([self.dataframe, df])

        # If incoming dataframe alone exceeds limit, flush immediately
        if df_memory_bytes > self.max_inmemory_bytes:
            logger.info(
                f"Incoming dataframe of {df_memory_bytes / MB_TO_BYTES:.2f}MB exceeds limit, "
                "writing directly to BigQuery."
            )
            self.flush()

    def flush(self) -> WriteResults:
        """Write the buffered dataframe to BigQuery and clear the buffer.

        Returns:
            WriteResults with total_rows_processed count across all add() calls.
        """
        if self.dataframe.shape[0] > 0:
            logger.info(f"Flushing {self.dataframe.shape[0]} rows to {self.dataset}.{self.table}")
            rate_limit_name = utils.form_bq_rate_limit_write_id(self.dataset, self.table)
            # Timeout added to prevent jobs hanging indefinitely if there's an issue with the
            # Prefect concurrency limit (e.g. stuck slots, server issues). If timeout is reached,
            # we proceed with the write anyway to avoid blocking the entire job.
            try:
                rate_limit(rate_limit_name, timeout_seconds=RATE_LIMIT_TIMEOUT_SECS)
                logger.info(f"Acquired rate limit slot for {rate_limit_name}")
            except TimeoutError:
                logger.warning(
                    f"Rate limit timeout after {RATE_LIMIT_TIMEOUT_SECS}s for {rate_limit_name}, "
                    "proceeding with write anyway"
                )
            pandas_gbq.to_gbq(
                self.dataframe,
                f"{self.dataset}.{self.table}",
                if_exists="append",
            )
            logger.info(f"Successfully wrote {self.dataframe.shape[0]} rows to BigQuery")
            self.dataframe = pd.DataFrame()

        return WriteResults(total_rows_processed=self.total_rows_processed)
