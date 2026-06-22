"""Test validate_manual_upload_csv_stream."""

import io

import pandas as pd
import pytest

from phiphi.api.projects.gathers import manual_upload
from phiphi.tests.api.gathers.manual_upload import conftest


def test_validate_manual_upload_csv_stream_success():
    """Test successful CSV validation with all correct columns and data types."""
    # Prepare test data with all required columns
    test_df = conftest.create_valid_manual_upload_df(2)
    test_df["platform"] = pd.Series(["tiktok", "facebook"])
    test_df["data_type"] = pd.Series(["posts", "comments"])

    # Convert DataFrame to CSV stream
    csv_stream = io.BytesIO()
    test_df.to_csv(csv_stream, index=False)
    csv_stream.seek(0)

    # Call the function
    result = manual_upload.file_processing.validate_manual_upload_csv_stream(csv_stream)

    # Assert results
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert result["platform"].tolist() == ["tiktok", "facebook"]
    assert result["data_type"].tolist() == ["posts", "comments"]
    assert result["message_datetime"].dt.tz is not None
    assert result["like_count"].tolist() == [10, 11]
    assert result["share_count"].tolist() == [5, 6]
    assert result["comment_count"].tolist() == [3, 4]
    assert result["tiktok_post_plays"].tolist() == [2, 3]


def test_validate_manual_upload_csv_stream_missing_columns():
    """Test that the function raises a ValueError when columns are missing."""
    # Prepare test data with missing columns
    test_df = conftest.create_valid_manual_upload_df(1)
    test_df = test_df.drop(columns=["platform"])

    # Convert DataFrame to CSV stream
    csv_stream = io.BytesIO()
    test_df.to_csv(csv_stream, index=False)
    csv_stream.seek(0)

    with pytest.raises(
        manual_upload.file_processing.InvalidManualUploadSchemaError, match="'platform'"
    ) as e:
        manual_upload.file_processing.validate_manual_upload_csv_stream(csv_stream)

    assert e.value.detail["error_message_i18n_key"] == "column_not_in_dataframe"  # type: ignore[index]


def test_validate_manual_upload_csv_stream_additional_columns():
    """Test that the function raises a ValueError when additional columns are present."""
    # Prepare test data with additional columns
    test_df = conftest.create_valid_manual_upload_df(1)
    test_df["extra_column"] = "extra_value"

    # Convert DataFrame to CSV stream
    csv_stream = io.BytesIO()
    test_df.to_csv(csv_stream, index=False)
    csv_stream.seek(0)

    with pytest.raises(
        manual_upload.file_processing.InvalidManualUploadSchemaError, match="'extra_column'"
    ) as e:
        manual_upload.file_processing.validate_manual_upload_csv_stream(csv_stream)

    assert e.value.detail["error_message_i18n_key"] == "column_not_in_schema"  # type: ignore[index]


def test_validate_manual_upload_csv_stream_invalid_platform():
    """Test validation of platform column with invalid values."""
    test_df = conftest.create_valid_manual_upload_df(3)
    test_df["platform"] = pd.Series(["tiktok", "facebook", "invalid"])

    # Convert DataFrame to CSV stream
    csv_stream = io.BytesIO()
    test_df.to_csv(csv_stream, index=False)
    csv_stream.seek(0)

    with pytest.raises(
        manual_upload.file_processing.InvalidManualUploadSchemaError, match="'platform'"
    ) as e:
        manual_upload.file_processing.validate_manual_upload_csv_stream(csv_stream)

    # dataframe_check is what Pandera decided the error is
    assert e.value.detail["error_message_i18n_key"] == "dataframe_check"  # type: ignore[index]


def test_validate_manual_upload_csv_stream_datetime_handling():
    """Test datetime parsing and UTC conversion."""
    test_df = conftest.create_valid_manual_upload_df(3)
    test_df["message_datetime"] = pd.Series(
        [
            "2023-01-01 10:00:01.4325+01:00",
            "20230101 11:00",
            "2023-01-01T10:00:00Z",
        ]
    )
    # Convert DataFrame to CSV stream
    csv_stream = io.BytesIO()
    test_df.to_csv(csv_stream, index=False)
    csv_stream.seek(0)

    result_df = manual_upload.file_processing.validate_manual_upload_csv_stream(csv_stream)
    assert result_df["message_datetime"].tolist() == [
        # Minus 1 on the hour
        # The milliseconds are rounded to 3 decimal places
        pd.Timestamp("2023-01-01 09:00:01.432000", tz="UTC"),
        # Makes any datetime without a timezone UTC
        pd.Timestamp("2023-01-01 11:00:00", tz="UTC"),
        pd.Timestamp("2023-01-01 10:00:00", tz="UTC"),
    ]


def test_validate_manual_upload_csv_stream_invalid_datetime_handling():
    """Test datetime parsing and UTC conversion."""
    test_df = conftest.create_valid_manual_upload_df(3)
    test_df["message_datetime"] = pd.Series(
        [
            "2023-01-01 10:00:01.4325+01:00",
            "invalid",
            "2023-01-01T10:00:00Z",
        ]
    )
    # Convert DataFrame to CSV stream
    csv_stream = io.BytesIO()
    test_df.to_csv(csv_stream, index=False)
    csv_stream.seek(0)

    with pytest.raises(
        manual_upload.file_processing.InvalidManualUpload,
        match="'message_datetime'",
    ) as e:
        manual_upload.file_processing.validate_manual_upload_csv_stream(csv_stream)

    assert e.value.detail["error_message_i18n_key"] == "dataframe_check"  # type: ignore[index]


def test_validate_manual_upload_csv_stream_empty_count_columns():
    """Test handling of empty count columns."""
    # Prepare test data with various count scenarios
    test_df = conftest.create_valid_manual_upload_df(1)
    test_df["like_count"] = pd.Series([None])
    test_df["share_count"] = pd.Series([None])
    test_df["comment_count"] = pd.Series([None])
    test_df["tiktok_post_plays"] = pd.Series([None])

    # Convert DataFrame to CSV stream
    csv_stream = io.BytesIO()
    test_df.to_csv(csv_stream, index=False)
    csv_stream.seek(0)

    # Call the function
    result = manual_upload.file_processing.validate_manual_upload_csv_stream(csv_stream)

    # Assert that count columns are set to 0
    assert result["like_count"].tolist() == [0]
    assert result["share_count"].tolist() == [0]
    assert result["comment_count"].tolist() == [0]
    assert result["tiktok_post_plays"].tolist() == [pd.NA]


def test_validate_manual_upload_csv_stream_invalid_tiktok_plays_count():
    """Test handling of invalid tiktok_post_plays."""
    # Prepare test data with various count scenarios
    test_df = conftest.create_valid_manual_upload_df(1)
    test_df["tiktok_post_plays"] = pd.Series(["invalid"])

    # Convert DataFrame to CSV stream
    csv_stream = io.BytesIO()
    test_df.to_csv(csv_stream, index=False)
    csv_stream.seek(0)

    with pytest.raises(
        manual_upload.file_processing.InvalidManualUpload, match="'tiktok_post_plays'"
    ) as e:
        manual_upload.file_processing.validate_manual_upload_csv_stream(csv_stream)

    assert e.value.detail["error_message_i18n_key"] == "dataframe_check"  # type: ignore[index]


def test_validate_manual_upload_csv_stream_invalid_csv():
    """Test handling of invalid CSV file with one row with an extra column."""
    invalid_csv_content = (
        b"id,name,age\n"
        b"1,Alice,30\n"  # Valid line
        b"7,Gina,28,??,??\n"  # Multiple extra columns
    )

    # Wrap the invalid CSV content in a BytesIO stream
    csv_stream = io.BytesIO(invalid_csv_content)
    csv_stream.seek(0)

    # Verify that the validation raises the expected exception
    with pytest.raises(
        manual_upload.file_processing.InvalidManualUpload,
        match="Unable to parse CSV please check CSV format.",
    ) as e:
        manual_upload.file_processing.validate_manual_upload_csv_stream(csv_stream)

    # Check the specific error message key
    assert e.value.detail["error_message_i18n_key"] == "invalid_csv"  # type: ignore[index]


def test_validate_manual_upload_csv_stream_int_id_columns():
    """Test handling of integer ID columns."""
    # Prepare test data with various count scenarios
    test_df = conftest.create_valid_manual_upload_df(3)
    test_df["message_id_pi"] = pd.Series([1, 2, 3])

    # Convert DataFrame to CSV stream
    csv_stream = io.BytesIO()
    test_df.to_csv(csv_stream, index=False)
    csv_stream.seek(0)

    # Call the function
    result = manual_upload.file_processing.validate_manual_upload_csv_stream(csv_stream)

    # assert that the int is cast to a string
    assert result["message_id_pi"].tolist() == ["1", "2", "3"]
