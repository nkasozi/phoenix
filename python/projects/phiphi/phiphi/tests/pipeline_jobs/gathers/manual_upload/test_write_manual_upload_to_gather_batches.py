"""Tests for write_manual_upload_to_gather_batches manual upload gathers."""

import datetime
import json
from unittest import mock

from prefect.logging import disable_run_logger as disable_prefect_run_logger

from phiphi import utils
from phiphi.api.projects.gathers import schemas as gathers_schemas
from phiphi.api.projects.gathers.manual_upload import schemas as manual_upload_schemas
from phiphi.pipeline_jobs import dataframe_writers
from phiphi.pipeline_jobs.gathers import gather_batch_write_managers, manual_upload
from phiphi.tests.pipeline_jobs.gathers.manual_upload import conftest

utils.init_logging()


@mock.patch("phiphi.pipeline_jobs.dataframe_writers.pandas_gbq.to_gbq")
@mock.patch("phiphi.pipeline_jobs.dataframe_writers.rate_limit")
def test_write_manual_upload_to_gather_batches(
    rate_limit_mock,
    to_gbq_mock,
    tmpdir,
    patch_settings,
):
    """Test write_manual_upload_to_gather_batches function with GatherBatchWriteManager."""
    input_df = conftest.create_mock_manual_upload_df(13)
    max_mb_batch_size = 2
    file_path = str(tmpdir.join("manual_upload_data_1.csv"))
    input_df.to_csv(file_path, index=False)

    # Prepare the manual upload gather response
    manual_upload_gather = manual_upload_schemas.ManualUploadGatherResponse(
        id=42,
        name="Manual Upload",
        file_url=file_path,
        file_size=1000,
        uploaded_file_name="manual_upload_data_1.csv",
        file_row_count=13,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=1,
        child_type=gathers_schemas.ChildTypeName.manual_upload,
    )

    # Create the write manager
    write_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=manual_upload_gather.id,
            job_run_id=1,
            gather_type=gathers_schemas.ChildTypeName.manual_upload,
        ),
        df_writer=dataframe_writers.BigQueryDataFrameWriter(
            dataset="test_dataset",
            table="test_table",
        ),
        max_mb_batch_size=max_mb_batch_size,
    )

    # Disable Prefect logging
    with disable_prefect_run_logger():
        # Call the function
        scrape_response = manual_upload.write_manual_upload_to_gather_batches(
            manual_upload_gather=manual_upload_gather,
            write_manager=write_manager,
        )

    # Assertions - with memory-based batching via GatherBatchWriteManager
    assert scrape_response.total_items == input_df.shape[0]
    assert scrape_response.total_batches >= 1  # At least one batch created
    assert scrape_response.total_cost == 0

    # Verify to_gbq was called at least once
    assert to_gbq_mock.call_count >= 1

    # Check the first call to verify structure
    first_call_df = to_gbq_mock.call_args_list[0][0][0]
    assert len(first_call_df) >= 1
    assert "batch_id" in first_call_df.columns
    assert "gather_id" in first_call_df.columns
    assert "json_data" in first_call_df.columns
    assert all(first_call_df["gather_id"] == 42)

    # Validate JSON data structure in the first batch
    first_batch_json_data = json.loads(first_call_df["json_data"].iloc[0])
    assert isinstance(first_batch_json_data, list)
    assert len(first_batch_json_data) >= 1

    # Verify the data structure matches expectations
    first_item = first_batch_json_data[0]
    assert isinstance(first_item, dict)
    assert "message_datetime" in first_item
    assert "message_id_pi" in first_item
    assert "platform" in first_item

    # Verify all rows were processed by checking total items across all batches
    total_items_in_batches = 0
    for call in to_gbq_mock.call_args_list:
        call_df = call[0][0]
        for _, row in call_df.iterrows():
            batch_data = json.loads(row["json_data"])
            total_items_in_batches += len(batch_data)

    assert total_items_in_batches == input_df.shape[0]
