"""Test dataframe writers."""

from unittest import mock

import numpy as np
import pandas as pd

from phiphi.pipeline_jobs import dataframe_writers


@mock.patch("phiphi.pipeline_jobs.dataframe_writers.pandas_gbq")
def test_max_inmemory_mb_triggers_flush(mock_pandas_gbq):
    """Test that the writer flushes buffer when adding a dataframe would exceed limit.

    This test verifies the batching behavior where small dataframes are buffered
    until the combined size would exceed the limit, at which point the buffer is flushed.
    """
    # Create a BigQueryDataFrameWriter with a small max_inmemory_mb
    # Setting it to 1MB for testing purposes
    writer = dataframe_writers.BigQueryDataFrameWriter(
        dataset="test_dataset", table="test_table", max_inmemory_mb=1
    )

    # Create a dataframe that should be under the limit
    small_df_1 = pd.DataFrame(
        {"col1": np.random.randint(0, 100, size=1000), "col2": ["test"] * 1000}
    )

    # Add the small dataframe - this should not trigger a flush
    writer.add(small_df_1)

    # Verify that to_gbq was not called
    mock_pandas_gbq.to_gbq.assert_not_called()

    # Create another dataframe that when combined with the buffer would exceed the limit
    # but is itself small enough to not trigger direct write
    small_df_2 = pd.DataFrame(
        {
            "col1": np.random.randint(0, 100, size=10000),
            "col2": ["test_string_to_increase_memory_usage"] * 10000,
        }
    )

    # Add the second dataframe - this should trigger a buffer flush before adding
    writer.add(small_df_2)
    mock_pandas_gbq.to_gbq.assert_called_once()

    # Verify the first call was the buffer flush (small_df_1)
    first_call_args = mock_pandas_gbq.to_gbq.call_args_list[0]
    pd.testing.assert_frame_equal(first_call_args.args[0], small_df_1)
    assert first_call_args.args[1] == "test_dataset.test_table"
    assert first_call_args.kwargs["if_exists"] == "append"

    # Do a final flush after the last add
    writer.flush()
    # Verify that to_gbq was called exactly twice (buffer flush + final flush)
    assert mock_pandas_gbq.to_gbq.call_count == 2

    # Verify the second call was the final flush (small_df_2)
    second_call_args = mock_pandas_gbq.to_gbq.call_args_list[1]
    pd.testing.assert_frame_equal(second_call_args.args[0], small_df_2)
    assert second_call_args.args[1] == "test_dataset.test_table"
    assert second_call_args.kwargs["if_exists"] == "append"

    # Verify that the dataframe was reset after flushing
    assert writer.dataframe.empty

    # Verify the total rows processed
    assert writer.total_rows_processed == small_df_1.shape[0] + small_df_2.shape[0]


@mock.patch("phiphi.pipeline_jobs.dataframe_writers.pandas_gbq")
def test_manual_flush(mock_pandas_gbq):
    """Test that manual flush works correctly regardless of memory usage."""
    writer = dataframe_writers.BigQueryDataFrameWriter(
        dataset="test_dataset",
        table="test_table",
        max_inmemory_mb=10,  # Set a high limit to prevent auto-flush
    )

    # Create a small dataframe
    small_df = pd.DataFrame({"col1": np.random.randint(0, 100, size=100), "col2": ["test"] * 100})

    # Add the dataframe
    writer.add(small_df)

    # Verify that to_gbq was not called yet
    mock_pandas_gbq.to_gbq.assert_not_called()

    # Manually flush
    result = writer.flush()

    # Verify that to_gbq was called
    mock_pandas_gbq.to_gbq.assert_called_once()

    # Check that the result contains the correct number of processed rows
    assert result.total_rows_processed == 100

    # Verify that the dataframe was reset after flushing
    assert writer.dataframe.empty


@mock.patch("phiphi.pipeline_jobs.dataframe_writers.pandas_gbq")
def test_empty_flush(mock_pandas_gbq):
    """Test that flushing an empty dataframe doesn't call to_gbq."""
    writer = dataframe_writers.BigQueryDataFrameWriter(dataset="test_dataset", table="test_table")

    # Flush without adding any data
    result = writer.flush()

    # Verify that to_gbq was not called
    mock_pandas_gbq.to_gbq.assert_not_called()

    # Check that the result contains zero processed rows
    assert result.total_rows_processed == 0


@mock.patch("phiphi.pipeline_jobs.dataframe_writers.pandas_gbq")
def test_large_dataframe_writes_directly(mock_pandas_gbq):
    """Test that dataframes exceeding max_inmemory_mb are written immediately without buffering."""
    # Create a writer with 1MB limit
    writer = dataframe_writers.BigQueryDataFrameWriter(
        dataset="test_dataset", table="test_table", max_inmemory_mb=1
    )

    # Create a large dataframe that exceeds the 1MB limit
    large_df = pd.DataFrame(
        {
            "col1": np.random.randint(0, 100, size=100000),
            "col2": ["test_large_string_to_increase_memory_usage"] * 100000,
        }
    )

    # Verify the dataframe is larger than the limit
    assert large_df.memory_usage().sum() > writer.max_inmemory_bytes

    # Add the large dataframe
    writer.add(large_df)

    # Verify that to_gbq was called immediately (direct write)
    mock_pandas_gbq.to_gbq.assert_called_once()

    # Verify the buffer is still empty after the direct write
    assert writer.dataframe.empty

    # Verify the dataframe was written correctly
    call_args = mock_pandas_gbq.to_gbq.call_args
    pd.testing.assert_frame_equal(call_args.args[0], large_df)
    assert call_args.args[1] == "test_dataset.test_table"
    assert call_args.kwargs["if_exists"] == "append"

    # Verify total rows processed is correct
    assert writer.total_rows_processed == large_df.shape[0]


@mock.patch("phiphi.pipeline_jobs.dataframe_writers.pandas_gbq")
def test_large_dataframe_flushes_buffer_first(mock_pandas_gbq):
    """Test that existing buffer is flushed before writing a large dataframe directly."""
    writer = dataframe_writers.BigQueryDataFrameWriter(
        dataset="test_dataset", table="test_table", max_inmemory_mb=1
    )

    # Add a small dataframe to the buffer
    small_df = pd.DataFrame({"col1": np.random.randint(0, 100, size=100), "col2": ["test"] * 100})
    writer.add(small_df)

    # Verify no writes yet
    mock_pandas_gbq.to_gbq.assert_not_called()

    # Add a large dataframe that exceeds the limit
    large_df = pd.DataFrame(
        {
            "col1": np.random.randint(0, 100, size=100000),
            "col2": ["test_large_string_to_increase_memory_usage"] * 100000,
        }
    )

    # Verify the large dataframe exceeds the limit
    assert large_df.memory_usage().sum() > writer.max_inmemory_bytes

    # Add the large dataframe
    writer.add(large_df)

    # Verify that to_gbq was called twice: once for buffer flush, once for large df
    assert mock_pandas_gbq.to_gbq.call_count == 2

    # Verify the first call was the small dataframe (buffer flush)
    first_call_args = mock_pandas_gbq.to_gbq.call_args_list[0]
    pd.testing.assert_frame_equal(first_call_args.args[0], small_df)

    # Verify the second call was the large dataframe (direct write)
    second_call_args = mock_pandas_gbq.to_gbq.call_args_list[1]
    pd.testing.assert_frame_equal(second_call_args.args[0], large_df)

    # Verify buffer is empty after both writes
    assert writer.dataframe.empty

    # Verify total rows processed
    assert writer.total_rows_processed == small_df.shape[0] + large_df.shape[0]
