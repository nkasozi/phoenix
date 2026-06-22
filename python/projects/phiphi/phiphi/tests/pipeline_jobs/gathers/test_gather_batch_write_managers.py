"""Tests for gather_batch_write_managers.py."""

import json

from phiphi.api.projects.gathers import schemas
from phiphi.pipeline_jobs import dataframe_writers
from phiphi.pipeline_jobs.gathers import gather_batch_write_managers


def test_gather_batch_write_manager_basic():
    """Test basic functionality of GatherBatchWriteManager with memory-based batching."""
    dummy_writer = dataframe_writers.DummyWriter()
    writer_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=1,
            job_run_id=1,
            gather_type=schemas.ChildTypeName.apify_facebook_posts,
        ),
        df_writer=dummy_writer,
        max_mb_batch_size=0.001,  # Very small to trigger batching
    )

    # Add some items
    for i in range(5):
        writer_manager.add({"id": i, "data": f"test_data_{i}" * 100})

    # Complete the write
    results = writer_manager.complete_write()

    # Assertions
    assert results.total_items_processed == 5
    assert results.total_batches_processed >= 2  # Should create multiple batches due to small size
    assert results.error_count == 0

    # Verify the dataframe structure
    assert len(dummy_writer.dataframe) == results.total_batches_processed
    assert "batch_id" in dummy_writer.dataframe.columns
    assert "gather_id" in dummy_writer.dataframe.columns
    assert "json_data" in dummy_writer.dataframe.columns

    # Verify all items are present across all batches
    total_items = 0
    for _, row in dummy_writer.dataframe.iterrows():
        batch_data = json.loads(row["json_data"])
        total_items += len(batch_data)

    assert total_items == 5


def test_gather_batch_write_manager_large_batch():
    """Test GatherBatchWriteManager with large batch size keeps items in one batch."""
    dummy_writer = dataframe_writers.DummyWriter()
    writer_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=2,
            job_run_id=2,
            gather_type=schemas.ChildTypeName.apify_facebook_comments,
        ),
        df_writer=dummy_writer,
        max_mb_batch_size=1000,  # Very large batch size
    )

    # Add some items
    for i in range(10):
        writer_manager.add({"id": i, "message": f"comment_{i}"})

    # Complete the write
    results = writer_manager.complete_write()

    # Assertions
    assert results.total_items_processed == 10
    assert results.total_batches_processed == 1  # Should be in one batch
    assert results.error_count == 0

    # Verify the dataframe structure
    assert len(dummy_writer.dataframe) == 1
    assert dummy_writer.dataframe.iloc[0]["gather_id"] == 2
    assert dummy_writer.dataframe.iloc[0]["job_run_id"] == 2

    # Verify all items are in the single batch
    batch_data = json.loads(dummy_writer.dataframe.iloc[0]["json_data"])
    assert len(batch_data) == 10
    assert batch_data[0]["id"] == 0
    assert batch_data[9]["id"] == 9
