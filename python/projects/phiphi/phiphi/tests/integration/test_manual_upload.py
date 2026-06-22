"""Test manual upload of data to BigQuery."""

import datetime

import pandas_gbq

from phiphi.api.projects.gathers import manual_upload
from phiphi.api.projects.gathers import schemas as gathers_schemas
from phiphi.pipeline_jobs import constants
from phiphi.pipeline_jobs.gathers import flow as gather_flow
from phiphi.tests.pipeline_jobs.gathers.manual_upload import conftest


def test_manual_upload(tmp_bq_project, tmpdir, prefect_test_fixture):
    """Test the manual upload of data to BigQuery."""
    test_project_namespace = tmp_bq_project
    input_df = conftest.create_mock_manual_upload_df(22)
    # A `gs://` url will be used in the real world but pd says they can just read gs URLs
    # so we are just using a local file path and expect the pipeline to upload the file to GCS
    file_path = str(tmpdir.join("manual_upload_data_1.csv"))
    input_df.to_csv(file_path, index=False)
    gather = manual_upload.schemas.ManualUploadGatherResponse(
        id=1,
        name="test_manual_upload",
        project_id=10,
        file_url=file_path,
        file_size=1000,
        uploaded_file_name="manual_upload_data_1.csv",
        file_row_count=22,
        child_type=gathers_schemas.ChildTypeName.manual_upload,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )

    max_mb_batch_size = 5
    batch_of_batches_size = 2

    pipeline_result = gather_flow.gather_flow(
        gather_dict=gather.dict(),
        gather_child_type=gathers_schemas.ChildTypeName.manual_upload,
        job_run_id=1,
        project_namespace=test_project_namespace,
        max_mb_batch_size=max_mb_batch_size,
        batch_of_batches_size=batch_of_batches_size,
    )

    assert pipeline_result.cost == 0
    assert pipeline_result.result_count == 22

    # Check the data is in the table
    messages_df = pandas_gbq.read_gbq(
        f"SELECT * FROM {test_project_namespace}.{constants.GENERALISED_MESSAGES_TABLE_NAME} "
        "ORDER BY gather_batch_id, like_count",
    )
    assert messages_df.shape[0] == 22
    assert messages_df["like_count"].to_list() == list(range(10, 32))
