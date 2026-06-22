"""Unit tests for manual upload helper functions.

Tests cover validation and conversion helper functions used by manual upload.
"""

import pandas as pd
import pandera.pandas as pa
import pytest

from phiphi.pipeline_jobs.gathers import manual_upload
from phiphi.tests.pipeline_jobs.gathers.manual_upload import conftest


def test_validate_manual_upload_df_basic():
    """Test basic validation of manual upload DataFrame."""
    # Generate example data using the schema
    input_df = conftest.create_mock_manual_upload_df(1)

    # Validate the dataframe
    validated_df = manual_upload.validate_manual_upload_df(input_df)

    # Assertions
    assert isinstance(validated_df, pd.DataFrame)
    assert len(validated_df) == 1
    assert list(validated_df.columns) == list(input_df.columns)


def test_validate_manual_upload_df_empty_input():
    """Test validation with an empty DataFrame.

    Note: Pandera allows empty DataFrames by default, so we just verify it doesn't crash.
    """
    input_df = pd.DataFrame(columns=manual_upload.manual_upload_schema.columns.keys())  # type: ignore[call-overload]

    # Validate - should not raise an error for empty DataFrame
    validated_df = manual_upload.validate_manual_upload_df(input_df)
    assert len(validated_df) == 0
    assert list(validated_df.columns) == list(input_df.columns)


def test_validate_manual_upload_df_schema_validation():
    """Test schema validation with invalid data."""
    # Attempt to create a DataFrame that will fail schema validation
    with pytest.raises(pa.errors.SchemaError):
        # Intentionally create an incomplete DataFrame
        incomplete_df = pd.DataFrame(
            [
                {
                    # Intentionally missing many required fields
                    "platform": "twitter",
                }
            ]
        )

        manual_upload.validate_manual_upload_df(incomplete_df)


def test_convert_manual_upload_row_to_dict():
    """Test converting a manual upload row to dictionary."""
    # Generate example data
    input_df = conftest.create_mock_manual_upload_df(1)
    row = input_df.iloc[0]

    # Convert to dict
    row_dict = manual_upload.convert_manual_upload_row_to_dict(row)

    # Assertions
    assert isinstance(row_dict, dict)
    assert "message_datetime" in row_dict
    assert isinstance(row_dict["message_datetime"], str)
    # Check datetime format
    assert "T" in row_dict["message_datetime"]
    assert row_dict["message_datetime"].endswith("Z")


def test_convert_manual_upload_row_to_dict_multiple_rows():
    """Test converting multiple manual upload rows to dictionaries."""
    # Generate example data
    input_df = conftest.create_mock_manual_upload_df(5)

    # Convert each row to dict
    row_dicts = [
        manual_upload.convert_manual_upload_row_to_dict(row) for _, row in input_df.iterrows()
    ]

    # Assertions
    assert len(row_dicts) == 5
    for row_dict in row_dicts:
        assert isinstance(row_dict, dict)
        assert "message_datetime" in row_dict
        assert isinstance(row_dict["message_datetime"], str)


def test_validate_manual_upload_df_with_tiktok_fields():
    """Test validation with TikTok-specific fields."""
    # Generate example data with TikTok fields
    input_df = conftest.create_mock_manual_upload_df(3)

    # Ensure tiktok_post_plays is present
    assert "tiktok_post_plays" in input_df.columns

    # Validate the dataframe
    validated_df = manual_upload.validate_manual_upload_df(input_df)

    # Assertions
    assert isinstance(validated_df, pd.DataFrame)
    assert len(validated_df) == 3
    assert "tiktok_post_plays" in validated_df.columns
    # Check that tiktok_post_plays is Int64 dtype
    assert validated_df["tiktok_post_plays"].dtype == "Int64"
