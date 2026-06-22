"""Script to update BigQuery database credentials in Superset.

Usage:
    1. Copy this script and your service account JSON to the Superset pod
    2. Run: superset shell
    3. In the shell: exec(open('/path/to/update_superset_bq_credentials.py').read())
    4. Then call the functions:
       - list_databases()
       - show_credentials("your_db_name")
       - update_credentials("your_db_name", "/path/to/service_account.json")
"""

import json

from superset import db  # type: ignore[import-untyped]
from superset.models.core import Database  # type: ignore[import-untyped]


def list_databases() -> None:
    """List all database connections."""
    print("\nAvailable databases:")
    print("-" * 60)
    for d in db.session.query(Database).all():
        print(f"ID: {d.id:4d} | Name: {d.database_name}")
    print("-" * 60)


def get_database(db_name: str | None = None, db_id: int | None = None) -> Database | None:  # type: ignore[no-any-unimported]
    """Get a database by name or ID."""
    if db_id:
        database = db.session.query(Database).filter_by(id=db_id).first()
    elif db_name:
        database = db.session.query(Database).filter_by(database_name=db_name).first()
    else:
        print("Error: provide db_name or db_id")
        return None
    if not database:
        print("Database not found")
        list_databases()
        return None
    return database


def show_credentials(db_name: str | None = None, db_id: int | None = None) -> None:
    """Show current credentials for a database."""
    database = get_database(db_name, db_id)
    if not database:
        return
    print(f"\nCredentials for '{database.database_name}' (ID: {database.id}):")
    if database.encrypted_extra:
        try:
            print(json.dumps(json.loads(database.encrypted_extra), indent=2))
        except json.JSONDecodeError:
            print(database.encrypted_extra)
    else:
        print("(empty)")


def update_credentials(
    db_name: str | None = None,
    db_id: int | None = None,
    credentials_file: str | None = None,
) -> None:
    """Update database credentials from a service account JSON file.

    Example:
        update_credentials(db_name="my_bigquery_db", credentials_file="/tmp/service_account.json")
    """
    if not credentials_file:
        print("Error: credentials_file is required")
        return
    database = get_database(db_name, db_id)
    if not database:
        return
    # Load service account JSON
    try:
        with open(credentials_file, "r") as f:
            credentials_info = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {credentials_file}")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        return
    # Update
    new_encrypted_extra = {"credentials_info": credentials_info}
    database.encrypted_extra = json.dumps(new_encrypted_extra)
    db.session.commit()
    print(f"Successfully updated credentials for '{database.database_name}'")


# Print help on load
print(
    """
Superset BigQuery Credentials Updater
=====================================

Available functions:
  list_databases()                                    - List all databases
  show_credentials(db_name="name")                    - Show current credentials
  show_credentials(db_id=123)                         - Show current credentials by ID
  update_credentials(db_name="name", credentials_file="/path/to/sa.json")
  update_credentials(db_id=123, credentials_file="/path/to/sa.json")
"""
)
