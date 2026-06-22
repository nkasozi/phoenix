"""Test manual upload routes."""

import io
from unittest import mock

import pandas as pd
import pytest
from fastapi import testclient
from prefect.client.schemas import objects

from phiphi import config
from phiphi.tests.api.gathers.manual_upload import conftest


@pytest.fixture
def mock_manual_upload_storage(tmp_path):
    """Fixture to temporarily mock the manual upload storage URL using a temporary directory."""
    original_url = config.settings.MANUAL_UPLOAD_STORAGE_URL
    mock_url = f"file://{tmp_path}"
    config.settings.MANUAL_UPLOAD_STORAGE_URL = mock_url

    yield mock_url

    # Teardown: restore original URL
    config.settings.MANUAL_UPLOAD_STORAGE_URL = original_url


def create_manual_upload_csv_stream(num_rows=1) -> tuple[io.BytesIO, pd.DataFrame]:
    """Create a CSV stream with mock data."""
    test_df = conftest.create_valid_manual_upload_df(num_rows)

    # Create an in-memory CSV file
    csv_buffer = io.BytesIO()
    test_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return csv_buffer, test_df


@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_post(
    m_run_deployment,
    mock_manual_upload_storage,
    client_admin: testclient.TestClient,
    reseed_tables,
):
    """Test batched CSV processing endpoint."""
    mock_flow_run = mock.MagicMock(spec=objects.FlowRun)
    mock_flow_run.id = "mock_uuid"
    mock_flow_run.name = "mock_flow_run"
    m_run_deployment.return_value = mock_flow_run

    csv_stream, test_df = create_manual_upload_csv_stream(2)
    name = "Manual Upload 1"
    uploaded_file_name = "large_test.csv"

    # Send request with batch processing
    response = client_admin.post(
        "/projects/1/gathers/manual_upload/",
        files={"file": (uploaded_file_name, csv_stream, "text/csv")},
        data={
            "name": name,
        },
    )

    # Assert response
    assert response.status_code == 200

    # Check response structure
    manual_upload_response = response.json()

    assert manual_upload_response["name"] == name
    assert manual_upload_response["uploaded_file_name"] == uploaded_file_name
    assert manual_upload_response["file_row_count"] == len(test_df)
    assert manual_upload_response["file_url"].startswith(mock_manual_upload_storage)

    written_df = pd.read_csv(manual_upload_response["file_url"])
    expected_df = test_df.copy()
    # UTC is added to the datetime column
    expected_df["message_datetime"] = pd.Series(
        [
            "2023-01-01 00:00:00+00:00",
            "2023-01-01 00:00:01+00:00",
        ]
    )
    pd.testing.assert_frame_equal(
        written_df,
        expected_df,
        check_dtype=False,
    )
    m_run_deployment.assert_called_once()


@pytest.mark.patch_settings(
    {
        "MAX_MANUAL_UPLOAD_FILE_SIZE": 1,
    }
)
@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_post_file_too_large(
    m_run_deployment,
    mock_manual_upload_storage,
    client_admin: testclient.TestClient,
    reseed_tables,
    patch_settings,
):
    """Test batched CSV processing endpoint too large."""
    csv_stream, test_df = create_manual_upload_csv_stream(2)
    name = "Manual Upload 1"
    uploaded_file_name = "large_test.csv"

    # Send request with batch processing
    response = client_admin.post(
        "/projects/1/gathers/manual_upload/",
        files={"file": (uploaded_file_name, csv_stream, "text/csv")},
        data={
            "name": name,
        },
    )

    # Assert response
    assert response.status_code == 400
    # Check response structure
    manual_upload_response = response.json()

    assert manual_upload_response["detail"]["error_message_i18n_key"] == "invalid_file_too_large"
    m_run_deployment.assert_not_called()


@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_post_file_empty_string(
    m_run_deployment,
    mock_manual_upload_storage,
    client_admin: testclient.TestClient,
    reseed_tables,
):
    """Test batched CSV processing endpoint with empty string as file."""
    name = "Manual Upload 1"
    uploaded_file_name = "large_test.csv"

    # Send request with batch processing
    response = client_admin.post(
        "/projects/1/gathers/manual_upload/",
        files={"file": (uploaded_file_name, "", "text/csv")},
        data={
            "name": name,
        },
    )

    # Assert response
    assert response.status_code == 400

    # Check response structure
    manual_upload_response = response.json()
    assert manual_upload_response["detail"]["error_message_i18n_key"] == "invalid_file"
    m_run_deployment.assert_not_called()


@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_post_file_empty_name(
    m_run_deployment,
    mock_manual_upload_storage,
    client_admin: testclient.TestClient,
    reseed_tables,
):
    """Test batched CSV processing endpoint with no name."""
    csv_stream, test_df = create_manual_upload_csv_stream(2)
    uploaded_file_name = "large_test.csv"

    # Send request with batch processing
    response = client_admin.post(
        "/projects/1/gathers/manual_upload/",
        files={"file": (uploaded_file_name, csv_stream, "text/csv")},
    )

    # Assert response
    assert response.status_code == 422
    json_response = response.json()
    assert json_response["detail"][0]["msg"] == "Field required"
    assert "name" in json_response["detail"][0]["loc"]
    m_run_deployment.assert_not_called()


@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_post_no_access(
    m_run_deployment,
    mock_manual_upload_storage,
    client: testclient.TestClient,
    reseed_tables,
):
    """Test batched CSV processing endpoint."""
    mock_flow_run = mock.MagicMock(spec=objects.FlowRun)
    mock_flow_run.id = "mock_uuid"
    mock_flow_run.name = "mock_flow_run"
    m_run_deployment.return_value = mock_flow_run

    csv_stream, test_df = create_manual_upload_csv_stream(2)
    name = "Manual Upload 1"
    uploaded_file_name = "large_test.csv"

    # Send request with batch processing
    response = client.post(
        "/projects/1/gathers/manual_upload/",
        files={"file": (uploaded_file_name, csv_stream, "text/csv")},
        data={
            "name": name,
        },
    )
    assert response.status_code == 401
