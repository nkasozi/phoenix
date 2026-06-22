"""Test generalised authors."""

import pandas as pd
import pytest

from phiphi.pipeline_jobs import generalised_authors


@pytest.mark.patch_settings({"USE_MOCK_BQ": True})
def test_get_post_authors_with_mock_bq(
    patch_settings, pipeline_jobs_sample_generalised_post_authors
):
    """Test get_post_authors when USE_MOCK_BQ is enabled."""
    result_df = generalised_authors.get_post_authors(
        project_namespace="test_project", offset=0, limit=2
    )
    expected_df = pipeline_jobs_sample_generalised_post_authors[:2]
    pd.testing.assert_frame_equal(result_df, expected_df)


@pytest.mark.patch_settings({"USE_MOCK_BQ": True})
def test_get_author_with_mock_bq(patch_settings, pipeline_jobs_sample_generalised_post_authors):
    """Test get_author when USE_MOCK_BQ is enabled."""
    expected_series = pipeline_jobs_sample_generalised_post_authors.iloc[0]
    author_id = expected_series["phoenix_platform_message_author_id"]
    result_series = generalised_authors.get_author(
        project_namespace="test_project", phoenix_platform_message_author_id=author_id
    )
    assert result_series is not None
    pd.testing.assert_series_equal(result_series, expected_series)


@pytest.mark.patch_settings({"USE_MOCK_BQ": True})
def test_get_author_not_found_with_mock_bq(
    patch_settings, pipeline_jobs_sample_generalised_post_authors
):
    """Test get_author when USE_MOCK_BQ is enabled and not found."""
    result_df = generalised_authors.get_author(
        project_namespace="test_project", phoenix_platform_message_author_id="not_found"
    )
    assert result_df is None


@pytest.mark.patch_settings({"USE_MOCK_BQ": True})
def test_get_author_nulls_with_mock_bq(
    monkeypatch, patch_settings, pipeline_jobs_sample_generalised_post_authors
):
    """Test get_author when USE_MOCK_BQ is enabled and has null values."""
    # Temporarily change the SAMPLE_AUTHORS_FILE to use the null values version
    monkeypatch.setattr(
        generalised_authors, "SAMPLE_AUTHORS_FILE", "generalised_post_authors_with_nulls.json"
    )
    result_df = generalised_authors.get_post_authors(
        project_namespace="test_project", offset=0, limit=2
    )
    assert result_df is not None
    assert result_df.shape[0] == 2
    assert result_df.iloc[1] is not None
    assert result_df.iloc[1]["pi_platform_message_author_id"] is None
    assert result_df.iloc[1]["pi_platform_message_author_name"] is None
