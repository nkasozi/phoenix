"""Superset dashboard operations."""

from typing import Any

import requests

from phiphi.superset import client, exceptions


def import_dashboard(
    zip_file: bytes,
    overwrite: bool = False,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Import dashboard from ZIP file.

    Args:
        zip_file: Dashboard export ZIP as bytes.
        overwrite: Whether to overwrite existing dashboard.
        base_url: Superset base URL.
        session: Authenticated session (created if not provided).

    Returns:
        Import result dict.

    Raises:
        SupersetConnectionError: If Superset is unavailable.
        SupersetAPIError: If import fails.
    """
    url = base_url or client.get_base_url()
    sess = session or client.get_authenticated_session(base_url=url)

    try:
        response = sess.post(
            f"{url}/api/v1/dashboard/import/",
            files={"formData": ("dashboard.zip", zip_file, "application/zip")},
            data={"overwrite": str(overwrite).lower()},
            timeout=60,
        )
    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")

    return client.handle_response(response, "Dashboard import")


def get_dashboard_by_title(
    title: str,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> dict[str, Any] | None:
    """Find dashboard by title.

    Args:
        title: Dashboard title to search for.
        base_url: Superset base URL.
        session: Authenticated session (created if not provided).

    Returns:
        Dashboard dict if found, None otherwise.

    Raises:
        SupersetConnectionError: If Superset is unavailable.
        SupersetAPIError: If API request fails.
    """
    url = base_url or client.get_base_url()
    sess = session or client.get_authenticated_session(base_url=url)

    try:
        response = sess.get(
            f"{url}/api/v1/dashboard/",
            # Superset's API expects valid Rison query syntax.
            # And that dictates that a string literal is denoted with single quotes.
            # Double quotes are just double quotes in Rison and will be read as such.
            params={"q": f"(filters:!((col:dashboard_title,opr:eq,value:'{title}')))"},
            timeout=30,
        )
    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")

    result = client.handle_response(response, "Get dashboard")
    dashboards = result.get("result", [])
    return dashboards[0] if dashboards else None


def set_dashboard_roles(
    dashboard_id: int,
    role_ids: list[int],
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> None:
    """Assign roles to a dashboard's access control section.

    Args:
        dashboard_id: ID of the dashboard.
        role_ids: List of role IDs to assign.
        base_url: Superset base URL.
        session: Authenticated session (created if not provided).

    Raises:
        SupersetConnectionError: If Superset is unavailable.
        SupersetAPIError: If the request fails.
    """
    url = base_url or client.get_base_url()
    sess = session or client.get_authenticated_session(base_url=url)

    try:
        response = sess.put(
            f"{url}/api/v1/dashboard/{dashboard_id}",
            json={"roles": role_ids},
            timeout=30,
        )
    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")

    client.handle_response(response, "Set dashboard roles")


def delete_dashboard(
    dashboard_id: int,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> None:
    """Delete dashboard by ID (idempotent).

    Args:
        dashboard_id: ID of the dashboard to delete.
        base_url: Superset base URL.
        session: Authenticated session (created if not provided).

    Raises:
        SupersetConnectionError: If Superset is unavailable.
        SupersetAPIError: If delete fails (except 404).
    """
    url = base_url or client.get_base_url()
    sess = session or client.get_authenticated_session(base_url=url)

    try:
        response = sess.delete(f"{url}/api/v1/dashboard/{dashboard_id}", timeout=30)
    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")

    if response.status_code != 404:
        client.handle_response(response, "Delete dashboard")
