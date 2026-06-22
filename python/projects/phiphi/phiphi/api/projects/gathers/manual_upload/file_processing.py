"""Manual upload file processing."""

import dataclasses
import datetime
import math
from typing import Any, BinaryIO, Optional

import fastapi
import fsspec  # type: ignore[import-untyped]
import pandas as pd
import pandera.pandas as pa

# Not typed and waiting for issue:
# https://github.com/stevesimmons/uuid7/issues/5
import uuid_extensions  # type: ignore[import-untyped]

from phiphi import config
from phiphi.pipeline_jobs.gathers import manual_upload

ERROR_STORAGE_URL_NOT_SET = (
    "MANUAL_UPLOAD_STORAGE_URL must be set. "
    "Please set the MANUAL_UPLOAD_STORAGE_URL environment variable."
)


@dataclasses.dataclass
class UploadedFileMetadata:
    """Uploaded file metadata."""

    file_name_submited: str
    file_url: str
    file_size: int
    file_row_count: int


class InvalidManualUpload(fastapi.HTTPException):
    """Custom exception for invalid manual upload."""

    def __init__(
        self,
        error_message_i18n_key: str,
        error_message: str,
        status_code: int = 422,
    ) -> None:
        """Constructor for custom exception from a SchemaError."""
        detail = {
            # i18n: Error message key for invalid manual upload schema
            # used by console to display internationalised error message.
            "error_message_i18n_key": error_message_i18n_key,
            "error_message": error_message,
        }
        super().__init__(status_code=status_code, detail=detail)


class InvalidManualUploadSchemaError(InvalidManualUpload):
    """Custom exception for 422 invalid data status code."""

    def __init__(
        self,
        schema_error: pa.errors.SchemaError,
    ) -> None:
        """Constructor for custom exception from a SchemaError."""
        super().__init__(
            error_message_i18n_key=schema_error.reason_code.value,
            error_message=str(schema_error),
        )


def create_file_url(
    project_id: int,
    storage_url: Optional[str] = None,
    file_name: Optional[str] = None,
) -> str:
    """Create file URL.

    Creates a file URL for a manual upload.

    Args:
        project_id: Project ID.
        storage_url: Storage URL, defaults to MANUAL_UPLOAD_STORAGE_URL environment variable
        file_name: File name, defaults to None. If none is given a UUID version 1 will be
            generated.

    Returns:
        File URL.
    """
    if not file_name:
        # Generate UUID
        # V7 allows for ordered file name generation and unique identifier.
        uuid_str = uuid_extensions.uuid7str()
        file_name = f"{uuid_str}.csv"

    # This is not a default argument so it can be mocked in the tests
    if not storage_url:
        storage_url = config.settings.MANUAL_UPLOAD_STORAGE_URL

    if not storage_url:
        raise RuntimeError(ERROR_STORAGE_URL_NOT_SET)

    if not storage_url.endswith("/"):
        storage_url += "/"
    return f"{storage_url}{project_id}/manual_uploads/{file_name}"


def process_datetime(value: Any) -> datetime.datetime:
    """Process datetime value.

    This will handle a number of cases:
    - allow for isoformat strings
    - make all datetimes that are not timezone aware UTC

    Args:
        value: Value to process.

    Returns:
        Processed datetime.
    """
    # Convert to datetime
    dt = datetime.datetime.fromisoformat(str(value))

    # If no timezone, attach UTC without modifying the time
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    return dt


def validate_manual_upload_csv_stream(csv_stream: BinaryIO) -> pd.DataFrame:
    """Validate manual upload CSV stream.

    Args:
        csv_stream: CSV stream.

    Returns:
        DataFrame containing the manual upload data.
    """
    try:
        # Read the CSV stream into a DataFrame
        manual_upload_df = pd.read_csv(csv_stream)
    except pd.errors.ParserError as p:
        parse_error = str(p)
        raise InvalidManualUpload(
            error_message_i18n_key="invalid_csv",
            error_message=f"Unable to parse CSV please check CSV format.\n {parse_error}",
        )
    # if `tiktok_post_plays` is added and it is all empty then we need to convert it
    try:
        if "tiktok_post_plays" in manual_upload_df.columns:
            manual_upload_df["tiktok_post_plays"] = manual_upload_df["tiktok_post_plays"].astype(
                "Int64"
            )
    except ValueError:
        raise InvalidManualUpload(
            error_message_i18n_key=pa.errors.SchemaErrorReason.DATAFRAME_CHECK.value,
            error_message="Invalid data in 'tiktok_post_plays' column.",
        )

    try:
        if "message_datetime" in manual_upload_df.columns:
            manual_upload_df["message_datetime"] = manual_upload_df["message_datetime"].apply(
                process_datetime
            )
    except ValueError as e:
        raise InvalidManualUpload(
            error_message_i18n_key=pa.errors.SchemaErrorReason.DATAFRAME_CHECK.value,
            error_message=f"Invalid data in 'message_datetime' column. {e}",
        )
    try:
        validated_manual_upload_df = manual_upload.manual_upload_schema.validate(manual_upload_df)
    except pa.errors.SchemaError as e:
        raise InvalidManualUploadSchemaError(
            schema_error=e,
        )
    return validated_manual_upload_df


def upload_manual_upload_df(
    file_url: str,
    validated_manual_upload_df: pd.DataFrame,
    storage_options: Optional[dict] = None,
) -> None:
    """Upload manual upload DataFrame.

    This also creates folders if needed.

    Args:
        file_url: File URL.
        validated_manual_upload_df: Validated manual upload DataFrame.
        storage_options: Storage options, defaults to None.
    """
    # Use fsspec to handle different file systems
    # fsspec will create a folder if it does not exist
    with fsspec.open(file_url, mode="wb", **(storage_options or {})) as file:
        # Convert DataFrame to CSV and write
        validated_manual_upload_df.to_csv(file, index=False)


_suffixes = ["bytes", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]


def human_readable_file_size(size: int) -> str:
    """Convert file size to human readable format.

    Taken from:
    https://stackoverflow.com/a/25613067/4874363
    """
    # Determine binary order in steps of size 10
    # (coerce to int, // still returns a float)
    order = int(math.log2(size) / 10) if size else 0

    # Format file size
    # (.4g results in rounded numbers for exact matches
    # and maximum 3 decimals, and should never resort
    # to exponent values)
    return "{:.4g} {}".format(size / (1 << (order * 10)), _suffixes[order])


def validated_uploaded_file(
    file: fastapi.UploadFile,
) -> tuple[str, int]:
    """Validate uploaded file.

    Args:
        file: Uploaded file from route.

    Returns:
        Tuple of file name, file size

    Raises:
        InvalidManualUpload with 400 status code: If the file is invalid.
    """
    if file.content_type != "text/csv":
        raise InvalidManualUpload(
            error_message_i18n_key="invalid_file",
            error_message="Uploaded file must be a CSV.",
            status_code=400,
        )
    if file.filename is None or file.filename == "" or not file.filename.endswith(".csv"):
        raise InvalidManualUpload(
            error_message_i18n_key="invalid_file",
            error_message="Uploaded file must have a name that ends with `.csv`.",
            status_code=400,
        )

    if file.size is None or file.size == 0:
        raise InvalidManualUpload(
            error_message_i18n_key="invalid_file",
            error_message="Uploaded file must have a size greater than 0.",
            status_code=400,
        )
    if file.size > config.settings.MAX_MANUAL_UPLOAD_FILE_SIZE:
        human_readable_size = human_readable_file_size(file.size)
        max_human_readable_size = human_readable_file_size(
            config.settings.MAX_MANUAL_UPLOAD_FILE_SIZE
        )
        raise InvalidManualUpload(
            error_message_i18n_key="invalid_file_too_large",
            error_message=(
                "Uploaded file is too large."
                # Not making this human readable as it requires
                f" Maximum size is {max_human_readable_size} bytes."
                f" Uploaded file size is {human_readable_size}."
            ),
            status_code=400,
        )
    return file.filename, file.size


def process_manual_upload_file(file: fastapi.UploadFile, project_id: int) -> UploadedFileMetadata:
    """Process manual upload CSV stream.

    Args:
        file: Uploaded file from route
        project_id: Project ID.

    Returns:
        Uploaded file metadata (UploadedFileMetadata).
    """
    file_name, file_size = validated_uploaded_file(file)
    validated_manual_upload_df = validate_manual_upload_csv_stream(file.file)
    file_url = create_file_url(project_id)
    upload_manual_upload_df(file_url, validated_manual_upload_df)
    return UploadedFileMetadata(
        file_name_submited=file_name,
        file_url=file_url,
        file_size=file_size,
        file_row_count=validated_manual_upload_df.shape[0],
    )
