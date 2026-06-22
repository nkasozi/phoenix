"""Analytics module for handling analytics-related operations."""

import http
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Coroutine

import pandas as pd
import prefect
import sqlalchemy as sa

from phiphi import constants, platform_db, utils
from phiphi.api.projects import credit_allocations, user_project_associations
from phiphi.api.projects import crud as projects_crud
from phiphi.api.projects import models as project_models
from phiphi.api.projects.job_runs import models as job_runs_models
from phiphi.api.projects.job_runs import schemas as job_runs_schemas

utils.init_logging()

file_logger = logging.getLogger(__name__)


@prefect.flow(name="export_extended_platform_usage_analytics")
def export_extended_platform_usage_analytics(
    extended_project_analytics_output_path: str,
    base_folder_to_add_timestamped_analytics: str,
    auth0_domain: str | None = None,
    mgmt_api_token: str | None = None,
) -> dict[str, str]:
    """Flow to export comprehensive analytics data including extended platform usage analytics.

    Must have the secrects needed for `export_auth0_users` flow set up in the prefect server. See
    export_auth0_users_flow docstring for details.

    This flow orchestrates the export of platform usage analytics, Auth0 users, and creates
    extended analytics that combines all data sources.

    Args:
        extended_project_analytics_output_path (str): Path where the extended analytics
                                                    CSV will be saved
        base_folder_to_add_timestamped_analytics (str): Base folder where timestamped
                                                       analytics will be stored
        auth0_domain (str, optional): Auth0 domain. If None, reads from secret block
        mgmt_api_token (str, optional): Auth0 management API token. If None, reads from secret
            block.

    Returns:
        dict[str, str]: Dictionary with paths to all exported files:
                       {'analytics': 'path/to/project_analytics.csv',
                        'summary': 'path/to/project_summary_analytics.csv',
                        'associations': 'path/to/user_project_associations.csv',
                        'auth0_users': 'path/to/auth0_users.csv',
                        'auth0_summary': 'path/to/auth0_user_summary.csv',
                        'extended_analytics': 'path/to/extended_analytics.csv'}
    """
    logger = prefect.get_run_logger()

    # Create timestamped subfolder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_folder = _create_timestamped_output_folder(
        base_folder_to_add_timestamped_analytics, timestamp, logger
    )

    logger.info(f"Using timestamped folder: {timestamped_folder}")

    # Run platform usage analytics export
    logger.info("Starting platform usage analytics export")
    project_results = export_platform_usage_analytics_flow(output_folder=timestamped_folder)

    # Run Auth0 users export
    logger.info("Starting Auth0 users export")
    auth0_results = export_auth0_users_flow(
        output_folder=timestamped_folder, auth0_domain=auth0_domain, mgmt_api_token=mgmt_api_token
    )

    # Create extended analytics
    logger.info("Creating extended analytics")
    extended_analytics_path = create_extended_analytics(
        projects_csv_path=project_results["analytics"],
        associations_csv_path=project_results["associations"],
        auth0_users_csv_path=auth0_results["auth0_users"],
        output_path=extended_project_analytics_output_path,
        logger=logger,
    )

    # Combine all results
    all_results = {
        **project_results,
        **auth0_results,
        "extended_analytics": extended_analytics_path,
    }

    logger.info(f"Successfully exported all analytics data to: {all_results}")
    return all_results


def _create_timestamped_output_folder(
    base_folder: str,
    timestamp: str,
    logger: logging.Logger | logging.LoggerAdapter[logging.Logger],
) -> str:
    """Create a timestamped subfolder within the base folder.

    Args:
        base_folder (str): Base folder path
        timestamp (str): Timestamp string to use for subfolder name
        logger (logging.Logger): Logger instance

    Returns:
        str: Path to the created timestamped folder

    Raises:
        ValueError: If base_folder format is invalid
        OSError: If folder creation fails
    """
    if not base_folder or not base_folder.strip():
        raise ValueError("Base folder cannot be empty or whitespace only")

    base_folder = base_folder.strip()

    # Handle GCS folders
    if base_folder.startswith("gs://"):
        if len(base_folder) <= 5:
            raise ValueError("Invalid GCS URI: must include bucket name")
        base_folder = base_folder.rstrip("/")
        timestamped_folder = f"{base_folder}/analytics_{timestamp}"
        logger.info(f"Created GCS timestamped folder path: {timestamped_folder}")
    else:
        # Handle local folders
        base_folder = base_folder.rstrip("/\\")
        timestamped_folder = os.path.join(base_folder, f"analytics_{timestamp}")

        # Create the directory if it doesn't exist (for local paths)
        try:
            os.makedirs(timestamped_folder, exist_ok=True)
            logger.info(f"Created local timestamped folder: {timestamped_folder}")
        except OSError as e:
            logger.error(f"Failed to create timestamped folder {timestamped_folder}: {str(e)}")
            raise

    return timestamped_folder


@prefect.flow(name="export_platform_usage_analytics_flow")
def export_platform_usage_analytics_flow(
    output_folder: str,
) -> dict[str, str]:
    """Flow to export platform usage analytics data to CSV files.

    Args:
        output_folder (str, optional): Base folder path. Can be:
                                     - Local directory: '/path/to/base/folder'
                                     - GCS folder: 'gs://bucket-name/path/to/folder'

    Returns:
        dict[str, str]: dictionary with paths to exported files:
                       {'analytics': 'path/to/project_analytics.csv',
                        'summary': 'path/to/project_summary_analytics.csv',
                        'associations': 'path
    """
    logger = prefect.get_run_logger()
    return export_platform_usage_analytics(
        output_folder=output_folder,
        logger=logger,
    )


@prefect.flow(name="export_auth0_users")
def export_auth0_users_flow(
    output_folder: str,
    auth0_domain: str | None = None,
    mgmt_api_token: str | None = None,
) -> dict[str, str]:
    """Flow to export Auth0 users data to CSV files.

    This flow uses prefect secrets to retrieve Auth0 credentials.
    Set these secrets as blocks in the prefect server.

    Args:
        output_folder (str): Base folder path. Can be:
                           - Local directory: '/path/to/base/folder'
                           - GCS folder: 'gs://bucket-name/path/to/folder'
        auth0_domain (str, optional): Auth0 domain. If None, reads from secret block
        mgmt_api_token (str, optional): Auth0 management API token. If None, reads from
                                      secret block.

    Returns:
        dict[str, str]: dictionary with paths to exported files:
                       {'auth0_users': 'path/to/auth0_users.csv',
                        'auth0_summary': 'path/to/auth0_user_summary.csv'}
    """
    logger = prefect.get_run_logger()

    if not auth0_domain:
        auth0_domain = prefect.blocks.system.Secret.load("export-auth0-users-auth0-domain").get()  # type: ignore[union-attr]

    if not mgmt_api_token:
        mgmt_api_token = prefect.blocks.system.Secret.load(  # type: ignore[union-attr]
            "export-auth0-users-mgmt-api-token"
        ).get()
    return export_auth0_users(
        output_folder=output_folder,
        auth0_domain=auth0_domain,
        mgmt_api_token=mgmt_api_token,
        logger=logger,
    )


def export_platform_usage_analytics(
    output_folder: str | None = None,
    logger: logging.Logger | logging.LoggerAdapter[logging.Logger] = file_logger,
) -> dict[str, str]:
    """Export platform usage analytics data to CSV files a folder.

    Args:
        output_folder (str, optional): Base folder path. Can be:
                                     - Local directory: '/path/to/base/folder'
                                     - GCS folder: 'gs://bucket-name/path/to/folder'
        If None, uses current directory.
        logger (logging.Logger): Logger instance for logging messages.

    Returns:
        dict[str, str]: dictionary with paths to exported files:
                       {'analytics': 'path/to/project_analytics.csv',
                        'summary': 'path/to/project_summary_analytics.csv',
                        'associations': 'path/to/user_project_associations.csv'}

    Raises:
        ValueError: If output_folder format is invalid
        Exception: If there are issues with database connection or file export
    """
    # Normalize output folder and create timestamped subfolder
    logger.info("Normalizing output folder and creating timestamped subfolder")
    analytics_uri, summary_uri, associations_uri = _normalize_output_folders(output_folder)
    logger.info(f"Export paths: {analytics_uri}, {summary_uri}, {associations_uri}")

    try:
        with platform_db.get_session_context() as session:
            # Get projects analytics DataFrame
            logger.info("Loading platform usage analytics data")
            projects_df = projects_analytics(session)
            logger.info(f"Loaded {len(projects_df)} projects for analytics")
            # Get user-project associations DataFrame
            associations_df = _load_user_project_associations_dataframe(session)
            logger.info(f"Loaded {len(associations_df)} user-project associations")

        # Export main analytics data
        projects_df.to_csv(analytics_uri, index=False)
        logger.info(f"Successfully exported {len(projects_df)} projects to {analytics_uri}")

        # Export summary analytics
        summary_data = _create_summary_dataframe(projects_df)
        summary_data.to_csv(summary_uri, index=False)
        logger.info(f"Successfully exported summary analytics to {summary_uri}")

        # Export user-project associations
        associations_df.to_csv(associations_uri, index=False)
        logger.info(
            f"Successfully exported {len(associations_df)} "
            f"user-project associations to {associations_uri}"
        )

        return {
            "analytics": analytics_uri,
            "summary": summary_uri,
            "associations": associations_uri,
        }

    except Exception as e:
        logger.error(f"Failed to export platform usage analytics: {str(e)}")
        raise


def export_auth0_users(
    output_folder: str | None = None,
    auth0_domain: str | None = None,
    mgmt_api_token: str | None = None,
    logger: logging.Logger | logging.LoggerAdapter[logging.Logger] = file_logger,
) -> dict[str, str]:
    """Export Auth0 users data to CSV files.

    Information on how to get the Auth0 management API token can be found here:
    https://auth0.com/docs/secure/tokens/access-tokens/management-api-access-tokens

    Args:
        output_folder (str, optional): Base folder path. Can be:
                                     - Local directory: '/path/to/base/folder'
                                     - GCS folder: 'gs://bucket-name/path/to/folder'
        If None, uses current directory.
        auth0_domain (str, optional): Auth0 domain. If None, reads from AUTH0_DOMAIN env var.
        mgmt_api_token (str, optional): Auth0 management API token. If None, reads from
                                      AUTH0_MGMT_API_TOKEN env var.
        logger (logging.Logger): Logger instance for logging messages.

    Returns:
        dict[str, str]: dictionary with paths to exported files:
                       {'auth0_users': 'path/to/auth0_users.csv',
                        'auth0_summary': 'path/to/auth0_user_summary.csv'}

    Raises:
        ValueError: If Auth0 credentials are missing or output_folder format is invalid
        Exception: If there are issues with Auth0 API connection or file export
    """
    # Get Auth0 credentials
    # Not using config sessions here as this is a standalone function
    domain = auth0_domain or os.getenv("AUTH0_DOMAIN")
    token = mgmt_api_token or os.getenv("AUTH0_MGMT_API_TOKEN")

    if not domain or not token:
        raise ValueError(
            "AUTH0_DOMAIN and AUTH0_MGMT_API_TOKEN must be provided as parameters "
            "or set in environment variables"
        )

    # Normalize output folder paths
    logger.info("Normalizing output folder for Auth0 export")
    users_uri, summary_uri = _normalize_auth0_output_folders(output_folder)
    logger.info(f"Auth0 export paths: {users_uri}, {summary_uri}")

    try:
        # Fetch Auth0 users
        logger.info("Fetching Auth0 users from API")
        users_data = _fetch_auth0_users(domain, token, logger)
        logger.info(f"Fetched {len(users_data)} users from Auth0")

        # Convert to DataFrame
        users_df = _create_auth0_users_dataframe(users_data)
        logger.info(f"Created DataFrame with {len(users_df)} users")

        # Export users data
        users_df.to_csv(users_uri, index=False)
        logger.info(f"Successfully exported {len(users_df)} Auth0 users to {users_uri}")

        # Create and export summary
        summary_df = _create_auth0_summary_dataframe(users_df)
        summary_df.to_csv(summary_uri, index=False)
        logger.info(f"Successfully exported Auth0 user summary to {summary_uri}")

        return {
            "auth0_users": users_uri,
            "auth0_summary": summary_uri,
        }

    except Exception as e:
        logger.error(f"Failed to export Auth0 users: {str(e)}")
        raise


def create_extended_analytics(
    projects_csv_path: str,
    associations_csv_path: str,
    auth0_users_csv_path: str,
    output_path: str,
    logger: logging.Logger | logging.LoggerAdapter[logging.Logger] = file_logger,
) -> str:
    """Create extended platform usage analytics CSV with last user login information.

    This function combines platform usage analytics, user-project associations, and Auth0 user data
    to create an extended analytics file that includes the last login date for each project.

    Args:
        projects_csv_path (str): Path to the project_analytics.csv file
        associations_csv_path (str): Path to the user_project_associations.csv file
        auth0_users_csv_path (str): Path to the auth0_users.csv file
        output_path (str): Path where the extended analytics CSV will be saved
        logger (logging.Logger): Logger instance for logging messages

    Returns:
        str: Path to the created extended analytics file
    """
    logger.info("Loading CSV files for extended analytics")

    # Load the CSV files
    logger.info(f"Loading projects analytics from {projects_csv_path}")
    projects_df = pd.read_csv(projects_csv_path)
    logger.info(f"Loaded {len(projects_df)} projects")

    logger.info(f"Loading user-project associations from {associations_csv_path}")
    associations_df = pd.read_csv(associations_csv_path)
    logger.info(f"Loaded {len(associations_df)} associations")

    logger.info(f"Loading Auth0 users from {auth0_users_csv_path}")
    auth0_df = pd.read_csv(auth0_users_csv_path)
    logger.info(f"Loaded {len(auth0_df)} Auth0 users")

    # Prepare Auth0 data - convert last_login to datetime and handle missing values
    if "last_login" in auth0_df.columns:
        auth0_df["last_login_dt"] = pd.to_datetime(auth0_df["last_login"], errors="coerce")
    else:
        logger.warning("'last_login' column not found in Auth0 data")
        auth0_df["last_login_dt"] = pd.NaT

    # Join associations with Auth0 data to get login info for each user-project pair
    logger.info("Joining associations with Auth0 user data")
    associations_with_login = associations_df.merge(
        auth0_df[["email", "last_login_dt"]], on="email", how="left"
    )

    # For each project, find the most recent login among all associated users
    logger.info("Calculating last user login for each project")
    project_last_login = (
        associations_with_login.groupby("project_id")["last_login_dt"]
        .max()
        .reset_index()
        .rename(columns={"last_login_dt": "last_user_login"})
    )

    # Join with projects data
    logger.info("Creating extended analytics DataFrame")
    extended_df = projects_df.merge(project_last_login, on="project_id", how="left")

    # Convert datetime back to string for CSV export (keeping ISO format)
    extended_df["last_user_login"] = extended_df["last_user_login"].dt.strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    # Replace NaT with None/empty string for projects with no associated users or no login data
    extended_df["last_user_login"] = extended_df["last_user_login"].fillna("")

    # Add metadata about when this extended file was created
    extended_df["extended_analytics_created_at"] = datetime.now().isoformat()

    # Save the extended analytics file
    logger.info(f"Saving extended analytics to {output_path}")
    extended_df.to_csv(output_path, index=False)

    logger.info(f"Successfully created extended analytics with {len(extended_df)} projects")
    logger.info(f"Projects with login data: {(extended_df['last_user_login'] != '').sum()}")

    return output_path


def _normalize_output_folders(output_folder: str | None = None) -> tuple[str, str, str]:
    """Normalize the output folder and create timestamped subfolder paths.

    Args:
        output_folder (str, optional): The base output folder

    Returns:
        tuple[str, str, str]: Paths for (analytics_file, summary_file, associations_file)

    Raises:
        ValueError: If the folder format is invalid
    """
    if output_folder is None:
        base_folder = "."
    else:
        if not output_folder or not output_folder.strip():
            raise ValueError("Output folder cannot be empty or whitespace only")
        base_folder = output_folder.strip()

    # Handle GCS folders
    if base_folder.startswith("gs://"):
        if len(base_folder) <= 5:
            raise ValueError("Invalid GCS URI: must include bucket name")
        base_folder = base_folder.rstrip("/")
        analytics_path = f"{base_folder}/project_analytics.csv"
        summary_path = f"{base_folder}/project_summary_analytics.csv"
        associations_path = f"{base_folder}/user_project_associations.csv"
    else:
        base_folder = base_folder.rstrip("/\\")
        os.makedirs(base_folder, exist_ok=True)
        analytics_path = os.path.join(base_folder, "project_analytics.csv")
        summary_path = os.path.join(base_folder, "project_summary_analytics.csv")
        associations_path = os.path.join(base_folder, "user_project_associations.csv")

    return analytics_path, summary_path, associations_path


def _normalize_auth0_output_folders(output_folder: str | None = None) -> tuple[str, str]:
    """Normalize the output folder for Auth0 export files.

    Args:
        output_folder (str, optional): The base output folder

    Returns:
        tuple[str, str]: Paths for (users_file, summary_file)

    Raises:
        ValueError: If the folder format is invalid
    """
    if output_folder is None:
        base_folder = "."
    else:
        if not output_folder or not output_folder.strip():
            raise ValueError("Output folder cannot be empty or whitespace only")
        base_folder = output_folder.strip()

    # Handle GCS folders
    if base_folder.startswith("gs://"):
        if len(base_folder) <= 5:
            raise ValueError("Invalid GCS URI: must include bucket name")
        base_folder = base_folder.rstrip("/")
        users_path = f"{base_folder}/auth0_users.csv"
        summary_path = f"{base_folder}/auth0_user_summary.csv"
    else:
        base_folder = base_folder.rstrip("/\\")
        os.makedirs(base_folder, exist_ok=True)
        users_path = os.path.join(base_folder, "auth0_users.csv")
        summary_path = os.path.join(base_folder, "auth0_user_summary.csv")

    return users_path, summary_path


def _fetch_auth0_users(
    domain: str, token: str, logger: logging.Logger | logging.LoggerAdapter[logging.Logger]
) -> list[dict]:
    """Fetch all users from Auth0 with pagination.

    Args:
        domain (str): Auth0 domain
        token (str): Auth0 management API token
        logger (logging.Logger): Logger instance

    Returns:
        list[dict]: List of user data dictionaries

    Raises:
        Exception: If there are issues with Auth0 API connection
    """
    # Set up connection
    conn = http.client.HTTPSConnection(domain)
    headers = {"authorization": f"Bearer {token}"}

    # Initialize pagination variables
    page = 0
    per_page = 100
    has_more = True
    all_users = []

    logger.info("Starting Auth0 user fetch with pagination")

    # Fetch all pages of users
    while has_more:
        # Create query parameters for pagination
        params = f"/api/v2/users?page={page}&per_page={per_page}&include_totals=true"

        try:
            conn.request("GET", params, headers=headers)
            res = conn.getresponse()

            if res.status != 200:
                error_msg = f"Auth0 API returned status code {res.status}"
                response_text = res.read().decode("utf-8")
                logger.error(f"{error_msg}: {response_text}")
                raise Exception(f"{error_msg}: {response_text}")

            data = json.loads(res.read().decode("utf-8"))

            # Extract users and metadata
            users = data.get("users", [])
            all_users.extend(users)

            # Check if there are more pages
            total = data.get("total", 0)
            start = data.get("start", 0)
            limit = data.get("limit", per_page)

            logger.info(
                f"Retrieved {len(users)} users (page {page + 1}, total so far: {len(all_users)})"
            )

            # Determine if we need to fetch more pages
            has_more = (start + limit) < total
            page += 1

            # Rate limiting consideration
            if has_more:
                time.sleep(0.5)  # Brief pause to respect rate limits

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from Auth0: {str(e)}")
            raise Exception(f"Invalid JSON response from Auth0: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching users from Auth0: {str(e)}")
            raise

    conn.close()
    logger.info(f"Successfully fetched {len(all_users)} users from Auth0")
    return all_users


def _create_auth0_users_dataframe(users_data: list[dict]) -> pd.DataFrame:
    """Create a pandas DataFrame from Auth0 users data.

    Args:
        users_data (list[dict]): List of user data dictionaries from Auth0

    Returns:
        pd.DataFrame: DataFrame with Auth0 users data
    """
    if not users_data:
        # Return empty DataFrame with expected columns
        return pd.DataFrame(
            columns=[
                "user_id",
                "email",
                "name",
                "nickname",
                "created_at",
                "updated_at",
                "last_login",
                "logins_count",
                "email_verified",
                "exported_at",
            ]
        )

    # Get all possible field names from all users
    all_fields: set[str] = set()
    for user in users_data:
        all_fields.update(user.keys())

    # Prioritize common fields to appear first
    priority_fields = [
        "user_id",
        "email",
        "name",
        "nickname",
        "created_at",
        "updated_at",
        "last_login",
        "logins_count",
        "email_verified",
    ]

    # Sort fields with priority fields first
    fieldnames = [f for f in priority_fields if f in all_fields]
    remaining_fields = [f for f in all_fields if f not in priority_fields]
    fieldnames.extend(sorted(remaining_fields))

    # Process users data
    processed_users = []
    for user in users_data:
        processed_user = {}
        for key, value in user.items():
            # Handle nested objects by converting to JSON strings
            if isinstance(value, (dict, list)):
                processed_user[key] = json.dumps(value)
            else:
                processed_user[key] = value
        processed_users.append(processed_user)

    # Create DataFrame with ordered columns
    users_df = pd.DataFrame(processed_users, columns=fieldnames)
    users_df["exported_at"] = datetime.now().isoformat()

    return users_df


def _create_auth0_summary_dataframe(users_df: pd.DataFrame) -> pd.DataFrame:
    """Create a summary analytics DataFrame from Auth0 users data.

    Args:
        users_df (pd.DataFrame): Main Auth0 users DataFrame

    Returns:
        pd.DataFrame: Summary analytics DataFrame
    """
    if users_df.empty:
        return pd.DataFrame(columns=["metric", "value", "timestamp"])

    # Calculate summary statistics
    total_users = len(users_df)
    verified_users = (
        users_df.get("email_verified", pd.Series()).sum()
        if "email_verified" in users_df.columns
        else 0
    )

    # Count users with recent logins (last 30 days)
    recent_login_users = 0
    if "last_login" in users_df.columns:
        # Convert last_login to datetime and count recent logins
        last_login_series = pd.to_datetime(users_df["last_login"], errors="coerce", utc=True)
        now_utc = datetime.utcnow()
        thirty_days_ago = pd.to_datetime(now_utc - timedelta(days=30), utc=True)
        recent_login_users = (last_login_series > thirty_days_ago).sum()

    # Calculate average logins if logins_count exists
    avg_logins = 0.0
    if "logins_count" in users_df.columns:
        avg_logins = users_df["logins_count"].mean()
        if pd.isna(avg_logins):
            avg_logins = 0

    # Create summary data
    summary_data = [
        {
            "metric": "total_auth0_users",
            "value": total_users,
            "timestamp": datetime.now().isoformat(),
        },
        {
            "metric": "verified_auth0_users",
            "value": int(verified_users),
            "timestamp": datetime.now().isoformat(),
        },
        {
            "metric": "auth0_users_recent_login_30d",
            "value": int(recent_login_users),
            "timestamp": datetime.now().isoformat(),
        },
        {
            "metric": "avg_auth0_user_logins",
            "value": float(avg_logins),
            "timestamp": datetime.now().isoformat(),
        },
    ]

    return pd.DataFrame(summary_data)


def _create_summary_dataframe(projects_df: pd.DataFrame) -> pd.DataFrame:
    """Create a summary analytics DataFrame from the main project data.

    Args:
        projects_df (pd.DataFrame): Main platform usage analytics DataFrame

    Returns:
        pd.DataFrame: Summary analytics DataFrame
    """
    if projects_df.empty:
        return pd.DataFrame(columns=["metric", "value", "timestamp"])

    # Calculate summary statistics
    total_projects = len(projects_df)
    deleted_projects = projects_df["deleted_at"].notna().sum()
    unlimited_credit_projects = projects_df["has_unlimited_credits"].sum()
    active_projects = total_projects - deleted_projects

    # Count projects by expected usage
    usage_counts = projects_df["expected_usage"].value_counts().to_dict()

    # Create summary data
    summary_data = [
        {
            "metric": "total_projects",
            "value": total_projects,
            "timestamp": datetime.now().isoformat(),
        },
        {
            "metric": "active_projects",
            "value": active_projects,
            "timestamp": datetime.now().isoformat(),
        },
        {
            "metric": "deleted_projects",
            "value": int(deleted_projects),
            "timestamp": datetime.now().isoformat(),
        },
        {
            "metric": "unlimited_credit_projects",
            "value": int(unlimited_credit_projects),
            "timestamp": datetime.now().isoformat(),
        },
        {
            "metric": "projects_total_costs",
            "value": projects_df["total_costs"].sum(),
            "timestamp": datetime.now().isoformat(),
        },
        {
            "metric": "projects_should_have_pi_data_deleted",
            "value": projects_df["should_have_pi_data_deleted"].sum(),
            "timestamp": datetime.now().isoformat(),
        },
        {
            "metric": "projects_should_be_deleted",
            "value": projects_df["should_be_deleted"].sum(),
            "timestamp": datetime.now().isoformat(),
        },
    ]

    for usage_type, count in usage_counts.items():
        if pd.notna(usage_type):
            summary_data.append(
                {
                    "metric": f"projects_usage_{str(usage_type).lower().replace(' ', '_')}",
                    "value": count,
                    "timestamp": datetime.now().isoformat(),
                }
            )

    return pd.DataFrame(summary_data)


def _load_base_project_metrics(session: sa.orm.Session) -> pd.DataFrame:
    """Retrieve project analytics data from the database as a pandas DataFrame."""
    projects = session.query(project_models.Project).all()

    data = []
    for project in projects:
        total_costs, estimated_total = projects_crud.get_total_costs_and_esimated_total_costs(
            session, project.id
        )
        total_allocated = credit_allocations.get_total_credit_allocation(session, project.id)
        data.append(
            {
                "project_id": project.id,
                "project_name": project.name,
                "project_description": project.description,
                "created_at": project.created_at.isoformat(),
                "expected_usage": project.expected_usage,
                "deleted_at": project.deleted_at,
                "has_unlimited_credits": project.has_unlimited_credits,
                "total_costs": total_costs,
                "estimated_total_costs": estimated_total,
                "total_allocated_credits": total_allocated,
                "pi_deleted_after_days": project.pi_deleted_after_days,
                "delete_after_days": project.delete_after_days,
                "date_to_delete_pi_data": (
                    project.created_at + pd.Timedelta(days=project.pi_deleted_after_days)
                ),
                "date_to_delete": (
                    project.created_at + pd.Timedelta(days=project.delete_after_days)
                ),
                "should_have_pi_data_deleted": (
                    project.pi_deleted_after_days is not None
                    and project.created_at + pd.Timedelta(days=project.pi_deleted_after_days)
                    < datetime.now()
                ),
                "should_be_deleted": (
                    project.deleted_at is not None
                    or (
                        project.created_at + pd.Timedelta(days=project.delete_after_days)
                        < datetime.now()
                    )
                ),
            }
        )

    projects_df = pd.DataFrame(data)

    column_order = [
        "project_id",
        "project_name",
        "project_description",
        "created_at",
        "expected_usage",
        "deleted_at",
        "has_unlimited_credits",
        "total_costs",
        "estimated_total_costs",
        "total_allocated_credits",
        "pi_deleted_after_days",
        "delete_after_days",
        "date_to_delete_pi_data",
        "date_to_delete",
        "should_have_pi_data_deleted",
        "should_be_deleted",
    ]

    if not projects_df.empty:
        projects_df = projects_df[column_order]
    else:
        projects_df = pd.DataFrame(columns=column_order)

    return projects_df


def _add_job_run_metrics(session: sa.orm.Session, projects_df: pd.DataFrame) -> pd.DataFrame:
    """Retrieve and enrich project DataFrame with job run metrics."""
    q1 = (
        session.query(
            job_runs_models.JobRuns.project_id,
            job_runs_models.JobRuns.foreign_job_type,
            sa.func.count(job_runs_models.JobRuns.id).label("cnt"),
            sa.func.sum(
                sa.case(
                    (job_runs_models.JobRuns.status == job_runs_schemas.Status.failed.value, 1),
                    else_=0,
                )
            ).label("failed_cnt"),
        )
        .group_by(job_runs_models.JobRuns.project_id, job_runs_models.JobRuns.foreign_job_type)
        .all()
    )
    lookup_counts = {
        (pid, jt): {"cnt": cnt, "failed_cnt": failed_cnt} for pid, jt, cnt, failed_cnt in q1
    }

    job_types = [t.value for t in job_runs_schemas.ForeignJobType]
    target_types = {
        job_runs_schemas.ForeignJobType.gather_classify_tabulate.value,
        job_runs_schemas.ForeignJobType.classify_tabulate.value,
    }

    q2 = (
        session.query(
            job_runs_models.JobRuns.project_id,
            job_runs_models.JobRuns.foreign_job_type,
            sa.func.sum(job_runs_models.JobRuns.estimated_total_cost).label(
                "sum_estimated_total_cost"
            ),
            sa.func.sum(job_runs_models.JobRuns.gather_normalise_error_count).label(
                "sum_gather_normalise_error_count"
            ),
            sa.func.sum(job_runs_models.JobRuns.gather_result_count).label(
                "sum_gather_result_count"
            ),
            sa.func.sum(job_runs_models.JobRuns.total_cost).label("sum_total_cost"),
            sa.func.max(job_runs_models.JobRuns.completed_at).label("latest_completed_at"),
        )
        .filter(job_runs_models.JobRuns.foreign_job_type.in_(target_types))
        .group_by(job_runs_models.JobRuns.project_id, job_runs_models.JobRuns.foreign_job_type)
        .all()
    )
    lookup_sums = {
        (pid, jt): {
            "sum_estimated_total_cost": sec or 0,
            "sum_gather_normalise_error_count": sgec or 0,
            "sum_gather_result_count": sgrc or 0,
            "sum_total_cost": stc or 0,
            "latest_completed_at": lca,
        }
        for pid, jt, sec, sgec, sgrc, stc, lca in q2
    }

    def make_metrics(row: pd.Series) -> dict:
        pid = row["project_id"]
        out: dict = {}
        for jt in job_types:
            counts = lookup_counts.get((pid, jt), {"cnt": 0, "failed_cnt": 0})
            out[f"{jt}_count"] = counts["cnt"]
            out[f"{jt}_failed_runs"] = counts["failed_cnt"]
        for jt in target_types:
            sums = lookup_sums.get((pid, jt), {})
            out[f"{jt}_sum_estimated_total_cost"] = sums.get("sum_estimated_total_cost", 0)
            out[f"{jt}_sum_gather_normalise_error_count"] = sums.get(
                "sum_gather_normalise_error_count", 0
            )
            out[f"{jt}_sum_gather_result_count"] = sums.get("sum_gather_result_count", 0)
            out[f"{jt}_sum_total_cost"] = sums.get("sum_total_cost", 0)
            out[f"{jt}_latest_completed_at"] = sums.get("latest_completed_at")
        return out

    metrics_df = projects_df[["project_id"]].copy()
    metrics = metrics_df.apply(make_metrics, axis=1, result_type="expand")
    return projects_df.join(metrics)


def _load_user_project_associations_dataframe(session: sa.orm.Session) -> pd.DataFrame:
    """Retrieve user-project associations as a pandas DataFrame."""
    associations = session.query(user_project_associations.UserProjectAssociations).all()
    data = [
        {
            "user_id": assoc.user_id,
            "project_id": assoc.project_id,
            "role": assoc.role,
            "email": assoc.email,
        }
        for assoc in associations
    ]
    assoc_df = pd.DataFrame(data)
    assoc_df["exported_at"] = datetime.now().isoformat()
    return assoc_df


def projects_analytics(session: sa.orm.Session) -> pd.DataFrame:
    """Retrieve project analytics data with job run metrics and user associations."""
    projects_df = _load_base_project_metrics(session)
    projects_df = _add_job_run_metrics(session, projects_df)

    assoc_df = _load_user_project_associations_dataframe(session)
    if not assoc_df.empty:
        email_series = assoc_df.groupby("project_id")["email"].agg(list)
        projects_df = projects_df.merge(
            email_series.rename("user_emails"), how="left", on="project_id"
        )
    projects_df["user_emails"] = projects_df["user_emails"].apply(
        lambda x: x if isinstance(x, list) else []
    )
    projects_df["exported_at"] = datetime.now().isoformat()

    return projects_df


def create_deployments(
    override_work_pool_name: str | None = None,
    deployment_name_prefix: str = "",
    image: str = constants.DEFAULT_IMAGE,
    tags: list[str] = [],
    build: bool = False,
    push: bool = False,
) -> list[Coroutine]:
    """Create deployments for projects.

    Args:
        override_work_pool_name (str | None): The name of the work pool to use to override the
        default work pool.
        deployment_name_prefix (str, optional): The prefix of the deployment name. Defaults to "".
        image (str, optional): The image to use for the deployments. Defaults to
        constants.DEFAULT_IMAGE.
        tags (list[str], optional): The tags to use for the deployments. Defaults to [].
        build (bool, optional): If True, build the image. Defaults to False.
        push (bool, optional): If True, push the image. Defaults to False.

    Returns:
        list[Coroutine]: List of coroutines that create deployments.
    """
    work_pool_name = str(constants.WorkPool.main)
    if override_work_pool_name:
        work_pool_name = override_work_pool_name
    tasks: list[Coroutine] = []
    flows_to_deploy: list[prefect.flows.Flow] = [
        export_platform_usage_analytics_flow,
        export_auth0_users_flow,
        export_extended_platform_usage_analytics,
    ]
    for flow_to_deploy in flows_to_deploy:
        tasks.append(
            flow_to_deploy.deploy(
                name=deployment_name_prefix + flow_to_deploy.name,
                work_pool_name=work_pool_name,
                image=image,
                build=build,
                push=push,
                tags=tags,
            )
        )

    return tasks
