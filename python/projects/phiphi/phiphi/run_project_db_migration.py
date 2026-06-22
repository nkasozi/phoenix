"""Script to run project_db migrations and initialization.

This provides commands to upgrade or downgrade the BigQuery-backed project database
using Alembic, and to initialize a new project database via the Prefect task.
"""

import argparse
import pathlib

from phiphi import project_db
from phiphi.pipeline_jobs import projects


def _run_migration(
    command: str,
    project_namespace: str,
    google_cloud_project: str | None,
    revision: str,
    alembic_ini_path: pathlib.Path | None,
) -> None:
    """Execute an Alembic upgrade or downgrade based on the provided arguments."""
    # Build SQLAlchemy URI
    uri = project_db.form_bigquery_sqlalchmey_uri(
        project_namespace,
        google_cloud_project,
    )
    # Determine Alembic ini path
    ini_path = (
        alembic_ini_path
        if alembic_ini_path is not None
        else project_db.get_default_alembic_ini_path()
    )

    # Run within a DB connection
    with project_db.init_connection(uri) as conn:
        if command == "upgrade":
            applied = project_db.alembic_upgrade(
                conn,
                revision=revision,
                alembic_ini_path=ini_path,
            )
            if applied:
                print(f"Upgraded {project_namespace} to revision {revision or 'head'}.")
            else:
                print("Database already at latest revision; no changes applied.")
        else:
            project_db.alembic_downgrade(
                conn,
                revision=revision,
                alembic_ini_path=ini_path,
            )
            print(f"Downgraded {project_namespace} to revision {revision}.")


def main() -> None:
    """Parse command-line arguments and dispatch to the appropriate action."""
    parser = argparse.ArgumentParser(
        description=("Manage project_db migrations and initialization.")
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Action to perform: upgrade, downgrade, or init_project_db",
    )

    # Upgrade command
    upgrade_parser = subparsers.add_parser(
        "upgrade",
        help="Upgrade database to the latest or specified revision.",
    )
    upgrade_parser.add_argument(
        "--project-namespace",
        required=True,
        help="BigQuery dataset namespace for the project.",
    )
    upgrade_parser.add_argument(
        "--google-cloud-project",
        help="Override default GCP project for BigQuery URI.",
    )
    upgrade_parser.add_argument(
        "--revision",
        default="head",
        help="Target Alembic revision (default: head).",
    )
    upgrade_parser.add_argument(
        "--alembic-ini-path",
        type=pathlib.Path,
        help="Path to Alembic .ini config file (default: from project_db).",
    )

    # Downgrade command
    downgrade_parser = subparsers.add_parser(
        "downgrade",
        help="Downgrade database to a specified revision.",
    )
    downgrade_parser.add_argument(
        "revision",
        help="Target Alembic revision for downgrade.",
    )
    downgrade_parser.add_argument(
        "--project-namespace",
        required=True,
        help="BigQuery dataset namespace for the project.",
    )
    downgrade_parser.add_argument(
        "--google-cloud-project",
        help="Override default GCP project for BigQuery URI.",
    )
    downgrade_parser.add_argument(
        "--alembic-ini-path",
        type=pathlib.Path,
        help="Path to Alembic .ini config file (default: from project_db).",
    )

    # Init DB command
    init_parser = subparsers.add_parser(
        "init_project_db",
        help="Initialize a new project database and run migrations.",
    )
    init_parser.add_argument(
        "--project-namespace",
        required=True,
        help="BigQuery dataset namespace for the new project.",
    )
    init_parser.add_argument(
        "--workspace-slug",
        required=True,
        help="Workspace slug label for the new dataset.",
    )
    init_parser.add_argument(
        "--with-dummy-data",
        action="store_true",
        help="Seed dummy data after migrations.",
    )

    args = parser.parse_args()

    if args.command in ("upgrade", "downgrade"):
        _run_migration(
            command=args.command,
            project_namespace=args.project_namespace,
            google_cloud_project=args.google_cloud_project,
            revision=args.revision,
            alembic_ini_path=args.alembic_ini_path,
        )

    elif args.command == "init_project_db":  # Initialize project database
        result = projects.init_project_db.fn(
            args.project_namespace,
            args.workspace_slug,
            args.with_dummy_data,
        )
        print(f"Initialized project database: {result}")


if __name__ == "__main__":
    main()
