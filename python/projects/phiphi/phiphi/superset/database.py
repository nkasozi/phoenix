"""Superset database operations."""

from typing import Any

import requests

from phiphi.superset import client, exceptions


def get_databases(
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """List all Superset databases.

    Args:
        base_url: Superset base URL.
        session: Authenticated session.

    Returns:
        List of database dicts.
    """
    url = base_url or client.get_base_url()
    sess = session or client.get_authenticated_session(base_url=url)

    try:
        response = sess.get(f"{url}/api/v1/database/", timeout=30)
    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")

    result = client.handle_response(response, "Get databases")
    return list(result.get("result", []))


def get_database_by_uuid(
    uuid: str,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> dict[str, Any] | None:
    """Find a database by its UUID.

    Args:
        uuid: Database UUID.
        base_url: Superset base URL.
        session: Authenticated session.

    Returns:
        Database dict if found, None otherwise.
    """
    databases = get_databases(base_url=base_url, session=session)
    for db in databases:
        if db.get("uuid") == uuid:
            return db
    return None


def get_database_name_by_uuid(
    uuid: str,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> str:
    """Get a database name by its UUID.

    Convenience wrapper around get_database_by_uuid that validates
    the database exists and returns the name directly.

    Args:
        uuid: Database UUID.
        base_url: Superset base URL.
        session: Authenticated session.

    Returns:
        The database name string.

    Raises:
        ValueError: If the database is not found.
    """
    db = get_database_by_uuid(uuid, base_url=base_url, session=session)
    if not db:
        raise ValueError(f"Superset database with UUID {uuid} not found")
    return str(db["database_name"])
