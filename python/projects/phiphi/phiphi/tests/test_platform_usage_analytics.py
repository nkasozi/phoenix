"""Unit tests for the platform_usage_analytics module."""

import os

import freezegun
import pandas as pd

from phiphi import platform_usage_analytics


@freezegun.freeze_time("2025-01-01T00:00:00")
def test_export_platform_usage_analytics_creates_csv_files(tmpdir, session_context, reseed_tables):
    """Test that export_platform_usage_analytics writes CSV files correctly."""
    # Prepare sample DataFrames
    expected_summary = pd.DataFrame(
        {
            "metric": [
                "total_projects",
                "active_projects",
                "deleted_projects",
                "unlimited_credit_projects",
                "projects_total_costs",
                "projects_should_have_pi_data_deleted",
                "projects_should_be_deleted",
                "projects_usage_weekly",
                "projects_usage_monthly",
            ],
            "value": [7, 6, 1, 1, 150.0, 0, 1, 6, 1],
            "timestamp": ["2025-01-01T00:00:00"] * 9,
        }
    )

    # Create a temporary output directory
    base_dir = tmpdir.mkdir("output")

    # Execute the export
    result = platform_usage_analytics.export_platform_usage_analytics(str(base_dir))

    # Verify that the result contains the expected keys
    assert set(result.keys()) == {"analytics", "summary", "associations"}

    analytics_path = result["analytics"]
    summary_path = result["summary"]
    associations_path = result["associations"]

    # Check that both files were created
    assert os.path.isfile(analytics_path)
    assert os.path.isfile(summary_path)
    assert os.path.isfile(associations_path)

    # Read back the CSVs and compare to the sample DataFrames
    df_exported = pd.read_csv(analytics_path)
    assert not df_exported.empty, "Analytics DataFrame should not be empty"
    assert len(df_exported) == 7, "Expected 7 rows in the analytics DataFrame"
    assert df_exported["exported_at"].loc[0] == "2025-01-01T00:00:00"
    first_row = df_exported.iloc[0]
    assert first_row["project_id"] == 1, "First project ID should be 1"
    assert first_row["project_name"] == "Phoenix Project 1", "First project name should match"
    assert pd.isna(first_row["deleted_at"]), "First project should not be deleted"
    assert first_row["expected_usage"] == "weekly", "First project expected usage should be weekly"
    assert first_row["gather_classify_tabulate_count"] == 6
    assert first_row["gather_classify_tabulate_sum_gather_result_count"] == 5
    assert first_row["gather_classify_tabulate_sum_gather_normalise_error_count"] == 0
    assert first_row["gather_classify_tabulate_sum_total_cost"] == 0.0
    assert first_row["user_emails"] == "['test1@phiphi.com']"
    # The freezegun does not work for the reseed_tables
    assert "date_to_delete_pi_data" in first_row
    assert "date_to_delete" in first_row
    assert bool(first_row["should_be_deleted"]) is False

    third_row = df_exported.iloc[2]
    assert third_row["project_id"] == 3, "Third project ID should be 3"
    assert third_row["total_costs"] == 100.0, "Third project total costs should be 100.0"
    assert third_row["total_allocated_credits"] == 100.0

    df_summary_exported = pd.read_csv(summary_path)
    pd.testing.assert_frame_equal(df_summary_exported, expected_summary)

    df_associations_export = pd.read_csv(associations_path)
    assert not df_associations_export.empty, "Associations DataFrame should not be empty"
    assert len(df_associations_export) == 2
    assert df_associations_export["exported_at"].loc[0] == "2025-01-01T00:00:00"
    assert "email" in df_associations_export.columns
    assert "project_id" in df_associations_export.columns


@freezegun.freeze_time("2025-01-01T00:00:00")
def test_export_auth0_users_creates_csv_files(tmpdir, monkeypatch):
    """Test that export_auth0_users writes CSV files correctly."""
    # Sample Auth0 users data to mock the API response
    mock_users_data = [
        {
            "user_id": "auth0|12345",
            "email": "user1@example.com",
            "name": "User One",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-06-01T00:00:00",
            "last_login": "2024-12-31T00:00:00",
            "logins_count": 10,
            "email_verified": True,
        },
        {
            "user_id": "auth0|67890",
            "email": "user2@example.com",
            "name": "User Two",
            "created_at": "2024-02-01T00:00:00",
            "updated_at": "2024-07-01T00:00:00",
            "last_login": "2024-11-30T00:00:00",
            "logins_count": 5,
            "email_verified": False,
        },
    ]

    # Mock the _fetch_auth0_users function to return our test data
    def mock_fetch_auth0_users(domain, token, logger):
        return mock_users_data

    monkeypatch.setattr(platform_usage_analytics, "_fetch_auth0_users", mock_fetch_auth0_users)

    # Expected summary data
    expected_summary = pd.DataFrame(
        {
            "metric": [
                "total_auth0_users",
                "verified_auth0_users",
                "auth0_users_recent_login_30d",
                "avg_auth0_user_logins",
            ],
            "value": [2, 1, 1, 7.5],
            "timestamp": ["2025-01-01T00:00:00"] * 4,
        }
    )

    # Create a temporary output directory
    base_dir = tmpdir.mkdir("auth0_output")

    # Execute the export with test credentials
    result = platform_usage_analytics.export_auth0_users(
        output_folder=str(base_dir),
        auth0_domain="test-domain.auth0.com",
        mgmt_api_token="test-token",
    )

    # Verify that the result contains the expected keys
    assert set(result.keys()) == {"auth0_users", "auth0_summary"}

    users_path = result["auth0_users"]
    summary_path = result["auth0_summary"]

    # Check that both files were created
    assert os.path.isfile(users_path)
    assert os.path.isfile(summary_path)

    # Read back the CSVs and verify contents
    df_users_exported = pd.read_csv(users_path)
    assert not df_users_exported.empty, "Users DataFrame should not be empty"
    assert len(df_users_exported) == 2, "Expected 2 users in the export"
    assert df_users_exported["exported_at"].loc[0] == "2025-01-01T00:00:00"

    # Verify first user's data
    first_user = df_users_exported.iloc[0]
    assert first_user["user_id"] == "auth0|12345"
    assert first_user["email"] == "user1@example.com"
    assert first_user["name"] == "User One"
    assert bool(first_user["email_verified"]) is True
    assert first_user["logins_count"] == 10

    # Verify second user's data
    second_user = df_users_exported.iloc[1]
    assert second_user["user_id"] == "auth0|67890"
    assert second_user["email"] == "user2@example.com"
    assert bool(second_user["email_verified"]) is False
    assert second_user["logins_count"] == 5

    # Verify summary data
    df_summary_exported = pd.read_csv(summary_path)
    pd.testing.assert_frame_equal(df_summary_exported, expected_summary, check_dtype=False)


@freezegun.freeze_time("2025-01-01T00:00:00")
def test_create_extended_analytics_creates_csv_with_login_data(
    tmpdir, session_context, reseed_tables, monkeypatch
):
    """Test that create_extended_analytics combines project and Auth0 data correctly."""
    # Sample Auth0 users data to mock the API response
    mock_users_data = [
        {
            "user_id": "auth0|12345",
            "email": "test1@phiphi.com",
            "name": "Test User One",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-06-01T00:00:00",
            "last_login": "2024-12-31T10:30:45.123000Z",
            "logins_count": 15,
            "email_verified": True,
        },
        {
            "user_id": "auth0|67890",
            "email": "test2@phiphi.com",
            "name": "Test User Two",
            "created_at": "2024-02-01T00:00:00",
            "updated_at": "2024-07-01T00:00:00",
            "last_login": "2024-11-15T14:20:30.456000Z",
            "logins_count": 8,
            "email_verified": False,
        },
        {
            "user_id": "auth0|11111",
            "email": "noproject@phiphi.com",
            "name": "User No Project",
            "created_at": "2024-03-01T00:00:00",
            "updated_at": "2024-08-01T00:00:00",
            "last_login": "2024-12-01T09:15:00.789000Z",
            "logins_count": 3,
            "email_verified": True,
        },
    ]

    # Mock the _fetch_auth0_users function to return our test data
    def mock_fetch_auth0_users(domain, token, logger):
        return mock_users_data

    monkeypatch.setattr(platform_usage_analytics, "_fetch_auth0_users", mock_fetch_auth0_users)

    # Create a temporary output directory
    base_dir = tmpdir.mkdir("extended_analytics_output")

    # First, export project analytics and Auth0 users
    project_result = platform_usage_analytics.export_platform_usage_analytics(str(base_dir))
    auth0_result = platform_usage_analytics.export_auth0_users(
        output_folder=str(base_dir),
        auth0_domain="test-domain.auth0.com",
        mgmt_api_token="test-token",
    )

    # Define the output path for extended analytics
    extended_output_path = os.path.join(str(base_dir), "extended_project_analytics.csv")

    # Execute create_extended_analytics
    result_path = platform_usage_analytics.create_extended_analytics(
        projects_csv_path=project_result["analytics"],
        associations_csv_path=project_result["associations"],
        auth0_users_csv_path=auth0_result["auth0_users"],
        output_path=extended_output_path,
    )

    # Verify that the result path matches what we expected
    assert result_path == extended_output_path

    # Check that the extended analytics file was created
    assert os.path.isfile(extended_output_path)
    assert os.path.isfile(project_result["analytics"]), "Project analytics file should exist"

    # Read back the extended analytics CSV and verify contents
    df_extended = pd.read_csv(extended_output_path)
    assert not df_extended.empty, "Extended analytics DataFrame should not be empty"
    assert len(df_extended) == 7, "Expected 7 projects in the extended analytics"

    # Verify that the new columns were added
    assert "last_user_login" in df_extended.columns
    assert "extended_analytics_created_at" in df_extended.columns

    # Verify the extended_analytics_created_at timestamp
    assert df_extended["extended_analytics_created_at"].iloc[0] == "2025-01-01T00:00:00"

    # Test project 1 (associated with test1@phiphi.com)
    project_1 = df_extended[df_extended["project_id"] == 1].iloc[0]
    assert project_1["last_user_login"] == "2024-12-31T10:30:45.123000Z"
    assert project_1["project_name"] == "Phoenix Project 1"

    # Test project 2 (associated with test1@phiphi.com)
    project_2 = df_extended[df_extended["project_id"] == 4].iloc[0]
    assert project_2["last_user_login"] == "2024-12-31T10:30:45.123000Z"
    assert project_2["project_name"] == "Phoenix Project 4"

    # Test projects without associated users (should have empty last_user_login)
    projects_without_users = df_extended[~df_extended["project_id"].isin([1, 4])]
    for _, project in projects_without_users.iterrows():
        assert pd.isna(project["last_user_login"]), (
            f"Project {project['project_id']} should have empty last_user_login"
        )

    project_analytics_df = pd.read_csv(project_result["analytics"])
    assert not project_analytics_df.empty, "Project analytics DataFrame should not be empty"
    assert len(project_analytics_df) == len(df_extended)

    # Assert the correct columns are different between the two DataFrames
    different_columns = set(df_extended.columns) - set(project_analytics_df.columns)
    expected_different_columns = {
        "last_user_login",
        "extended_analytics_created_at",
    }
    assert different_columns == expected_different_columns, (
        f"Expected different columns: {expected_different_columns}, but got: {different_columns}"
    )
