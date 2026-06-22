"""Test gathers manual_upload.create_file_url."""

import uuid
from unittest.mock import patch

import pytest

from phiphi.api.projects.gathers import manual_upload

EXAMPLE_STORAGE_URL = "file:///tmp"


@pytest.mark.patch_settings(
    {
        "MANUAL_UPLOAD_STORAGE_URL": EXAMPLE_STORAGE_URL,
    }
)
def test_create_file_url_with_project_id(patch_settings):
    """Test creating file URL with just project ID."""
    project_id = 123

    # Mock UUID to ensure predictable output
    with patch(
        "uuid_extensions.uuid7str", return_value=uuid.UUID("12345678-1234-1234-1234-123456789abc")
    ):
        url = manual_upload.file_processing.create_file_url(project_id)

    expected_uuid = "12345678-1234-1234-1234-123456789abc"
    expected_url = f"{EXAMPLE_STORAGE_URL}/{project_id}/manual_uploads/{expected_uuid}.csv"
    assert url == expected_url


@pytest.mark.patch_settings(
    {
        "MANUAL_UPLOAD_STORAGE_URL": EXAMPLE_STORAGE_URL,
    }
)
def test_create_file_url_with_custom_filename(patch_settings):
    """Test creating file URL with a custom filename."""
    project_id = 456
    custom_filename = "my_custom_file.csv"

    url = manual_upload.file_processing.create_file_url(project_id, file_name=custom_filename)

    expected_url = f"{EXAMPLE_STORAGE_URL}/{project_id}/manual_uploads/{custom_filename}"
    assert url == expected_url


def test_create_file_url_with_custom_storage_url():
    """Test creating file URL with a custom storage URL."""
    project_id = 789
    custom_storage_url = "https://custom-storage.com/bucket/"

    # Mock UUID to ensure predictable output
    with patch(
        "uuid_extensions.uuid7str", return_value=uuid.UUID("87654321-4321-4321-4321-210987654def")
    ):
        url = manual_upload.file_processing.create_file_url(
            project_id, storage_url=custom_storage_url
        )

    expected_uuid = "87654321-4321-4321-4321-210987654def"
    expected_url = f"{custom_storage_url}{project_id}/manual_uploads/{expected_uuid}.csv"
    assert url == expected_url


def test_create_file_url_without_trailing_slash():
    """Test that storage URL is correctly modified if it doesn't end with a slash."""
    project_id = 101
    storage_url = "https://storage.example.com"

    # Mock UUID to ensure predictable output
    with patch(
        "uuid_extensions.uuid7str", return_value=uuid.UUID("11111111-2222-3333-4444-555555555555")
    ):
        url = manual_upload.file_processing.create_file_url(project_id, storage_url=storage_url)

    expected_uuid = "11111111-2222-3333-4444-555555555555"
    expected_url = f"{storage_url}/{project_id}/manual_uploads/{expected_uuid}.csv"
    assert url == expected_url


def test_create_file_url_empty_storage_url():
    """Test that an error is raised when storage URL is empty."""
    project_id = 202

    with pytest.raises(
        RuntimeError, match=manual_upload.file_processing.ERROR_STORAGE_URL_NOT_SET
    ):
        manual_upload.file_processing.create_file_url(project_id, storage_url="")


@pytest.mark.patch_settings(
    {
        "MANUAL_UPLOAD_STORAGE_URL": EXAMPLE_STORAGE_URL,
    }
)
def test_uuid_generation(patch_settings):
    """Verify that the UUID generation works as expected."""
    project_id = 303

    url = manual_upload.file_processing.create_file_url(project_id)

    # Extract the filename from the URL
    filename = url.split("/")[-1]

    # Check that the filename ends with .csv
    assert filename.endswith(".csv")

    # Try to parse the filename (minus .csv) as a UUID
    try:
        parsed_uuid = uuid.UUID(filename[:-4])
        assert parsed_uuid.version == 7  # Ensure it's a time-based UUID
    except ValueError:
        pytest.fail("Generated filename is not a valid UUID")
