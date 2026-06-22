"""Gather batch write manager.

This module contains the gather batch write manager that is used to write the gather batches to the
data store.
"""

import dataclasses
import datetime
import json
import logging
from typing import Any

import pandas as pd

from phiphi.api.projects.gathers import schemas
from phiphi.pipeline_jobs import constants, dataframe_writers, gather_batches

logger = logging.getLogger(__name__)

# Conversion factor from megabytes to bytes
MB_TO_BYTES = 2**20

# Use deep=True to get accurate memory usage including string data, not just pointers
# Without deep=True, string columns are severely underestimated (only 8 bytes per pointer counted)
MEMORY_USAGE_DEEP = True


@dataclasses.dataclass
class GatherBatchCompletedWriteResults:
    """Results of the completed write."""

    writer_results: dataframe_writers.WriteResults
    total_items_processed: int
    total_batches_processed: int
    error_count: int = 0


@dataclasses.dataclass
class GatherBatchStaticData:
    """A dataclass with the static data for the gather batch."""

    gather_id: int
    job_run_id: int
    gather_type: schemas.ChildTypeName
    gathered_at: datetime.datetime = dataclasses.field(default_factory=datetime.datetime.now)


class GatherBatchWriteManager:
    """Manager for the writing of gather batches.

    This manager will collect each scraped dict and batch them in to one gather batch record. This
    record is then written to the data store.

    It is important that we batch the data as there is a limit to the amount of data we can store
    in one record for bigquery. This also allows the read of each gather batch to be more efficient
    and predictable in memory usage.

    This manager should be initialised with the static data for the gather batch and the writer to
    use to write the data. Different writers can be used to write the data in different ways.

    It is important to call `complete_write` after the addition of all items to ensure that all
    data is written to the data store.

    Memory behavior: Items are buffered until the batch would exceed max_mb_batch_size. This
    keeps batch sizes predictable and prevents excessive memory usage during JSON serialization.

    Usage:
    ```
    gather_batch_manager = GatherBatchWriteManager(static_data, df_writer)
    gather_batch_manager.add(item)
    gather_batch_manager.add_error(error)
    gather_batch_manager.complete_write()
    ```
    """

    def __init__(
        self,
        static_data: GatherBatchStaticData,
        df_writer: dataframe_writers.IDataFrameWriter,
        max_mb_batch_size: float | int = constants.DEFAULT_MAX_MB_BATCH_SIZE,
    ):
        """Initialise the collector.

        Args:
            static_data: The static data for the gather batch.
            df_writer: The writer to use to write the data.
            max_mb_batch_size: Maximum memory size in megabytes for the batch buffer before
                flushing. When the buffer plus a new item would exceed this limit, the buffer
                is flushed first.
        """
        self.item_count: int = 0
        self.batch_count: int = 0
        self.error_count: int = 0

        self.df_writer = df_writer
        self.max_batch_memory_bytes = max_mb_batch_size * MB_TO_BYTES
        self._batch_buffer: list[Any] = []
        self._empty_gather_batch = pd.DataFrame(
            [
                {
                    "gather_id": static_data.gather_id,
                    "job_run_id": static_data.job_run_id,
                    "gather_type": static_data.gather_type,
                    "batch_id": self.batch_count,
                    "gathered_at": static_data.gathered_at,
                    "json_data": "",
                    "last_processed_at": pd.NaT,
                }
            ]
        )
        # Need to convert the last_processed_at to a datetime so that insert type for bigquery is
        # correct
        self._empty_gather_batch["last_processed_at"] = self._empty_gather_batch[
            "last_processed_at"
        ].dt.tz_localize("UTC")
        gather_batches.gather_batches_schema.validate(self._empty_gather_batch)

    def add(self, item: dict) -> None:
        """Add an item to the batch buffer, flushing if memory limit would be exceeded.

        The item is serialized to JSON to estimate its memory footprint. If the buffer plus
        the new item would exceed max_batch_memory_bytes, the buffer is flushed first before
        adding the item. This keeps batch sizes predictable and prevents excessive memory usage.

        Args:
            item: Dictionary item to add to the batch.
        """
        self.item_count += 1

        # Estimate memory usage of the item by converting to JSON
        item_json = json.dumps(item)
        item_memory_bytes = len(item_json.encode("utf-8"))

        # Estimate current buffer memory by converting to JSON
        if self._batch_buffer:
            buffer_json = json.dumps(self._batch_buffer)
            buffer_memory_bytes = len(buffer_json.encode("utf-8"))
        else:
            buffer_memory_bytes = 0

        logger.debug(
            f"Buffer: {buffer_memory_bytes / MB_TO_BYTES:.2f}MB"
            f"({len(self._batch_buffer)} items), "
            f"Incoming: {item_memory_bytes / MB_TO_BYTES:.2f}MB, "
            f"Limit: {self.max_batch_memory_bytes / MB_TO_BYTES:.2f}MB"
        )

        # Check if combined memory would exceed limit
        if buffer_memory_bytes + item_memory_bytes > self.max_batch_memory_bytes:
            logger.debug("Buffer + incoming would exceed limit, flushing buffer first")
            self.flush()

        self._batch_buffer.append(item)

    def add_error(self, error: dict) -> None:
        """Add an error to the collection."""
        self.error_count += 1
        # Errors are added the general batch data and will be processed by the normaliser This is
        # to simplify and reduce the amount of work for error processing of gather batches
        self.add({"error": error})

    def flush(self) -> None:
        """Flush the buffer to the writer."""
        if len(self._batch_buffer) > 0:
            df_to_write = self._empty_gather_batch.copy()
            df_to_write.loc[0, "json_data"] = json.dumps(self._batch_buffer)
            df_to_write.loc[0, "batch_id"] = self.batch_count
            df_to_write.loc[0, "gathered_at"] = pd.Timestamp.now()
            gather_batches.gather_batches_schema.validate(df_to_write)
            self.df_writer.add(df_to_write)
            self.batch_count += 1
            self._batch_buffer = []

    def complete_write(self) -> GatherBatchCompletedWriteResults:
        """Complete the write process and return the collected data."""
        self.flush()
        writer_results = self.df_writer.flush()
        return GatherBatchCompletedWriteResults(
            writer_results=writer_results,
            total_items_processed=self.item_count,
            total_batches_processed=self.batch_count,
            error_count=self.error_count,
        )
