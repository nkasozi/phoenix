"""Superset role operations."""

import logging
import urllib.parse
from typing import Any

import requests

from phiphi.superset import client, exceptions

logger = logging.getLogger(__name__)


def get_roles(
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """List all Superset roles.

    Args:
        base_url: Superset base URL.
        session: Authenticated session.

    Returns:
        List of role dicts.
    """
    url = base_url or client.get_base_url()
    sess = session or client.get_authenticated_session(base_url=url)

    try:
        response = sess.get(f"{url}/api/v1/security/roles/", timeout=30)
    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")

    result = client.handle_response(response, "Get roles")
    return list(result.get("result", []))


def get_role_by_name(
    name: str,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> dict[str, Any] | None:
    """Find a role by its exact name using a server-side name filter.

    Using a server-side filter avoids the pagination problem where
    GET /security/roles/ only returns the first page of results.
    Without filtering, get_role_by_name would return None for any role
    beyond the first page, causing create_role to attempt a duplicate POST
    and receive a 422 UNPROCESSABLE ENTITY from FAB.

    Args:
        name: Role name.
        base_url: Superset base URL.
        session: Authenticated session.

    Returns:
        Role dict if found, None otherwise.
    """
    url = base_url or client.get_base_url()
    sess = session or client.get_authenticated_session(base_url=url)

    # FAB REST endpoints accept a Rison-encoded `q` parameter for server-side filtering.
    # Role names produced by get_dashboard_title contain only word chars, spaces, hyphens,
    # and parentheses (single quotes are stripped), so this format string is safe.
    rison_filter = f"(filters:!((col:name,opr:eq,value:'{name}')))"
    query_string = urllib.parse.urlencode({"q": rison_filter})

    try:
        response = sess.get(f"{url}/api/v1/security/roles/?{query_string}", timeout=30)
    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")

    result = client.handle_response(response, "Get role by name")
    found: list[dict[str, Any]] = result.get("result", [])
    if not found:
        return None
    return found[0]


def create_role(
    name: str,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Create a new role (idempotent).

    Args:
        name: Role name.
        base_url: Superset base URL.
        session: Authenticated session.

    Returns:
        Role dict (existing or newly created).
    """
    url = base_url or client.get_base_url()
    sess = session or client.get_authenticated_session(base_url=url)

    existing_role = get_role_by_name(name, base_url=url, session=sess)
    if existing_role:
        logger.info(f"Role '{name}' already exists.")
        return existing_role

    try:
        response = sess.post(
            f"{url}/api/v1/security/roles/",
            json={"name": name},
            timeout=30,
        )
    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")

    result = client.handle_response(response, "Create role")
    # Result usually contains "id" and "result"
    role_id = result.get("id")
    return {"id": role_id, "name": name}


# GOTCHA: This method is not idempotent, as it will overwrite existing permissions.
def add_permissions_to_role(
    role_id: int,
    permission_view_ids: list[int],
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> None:
    """Add multiple permission-resource pairs to a role.

    Args:
        role_id: ID of the role.
        permission_view_ids: List of permission-resource mapping IDs.
        base_url: Superset base URL.
        session: Authenticated session.
    """
    url = base_url or client.get_base_url()
    sess = session or client.get_authenticated_session(base_url=url)

    try:
        response = sess.post(
            f"{url}/api/v1/security/roles/{role_id}/permissions",
            json={"permission_view_menu_ids": permission_view_ids},
            timeout=30,
        )
        client.handle_response(response, "Update role permissions")
    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")


def get_role_permissions(
    role_id: int,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Get permissions for a role.

    Args:
        role_id: ID of the role.
        base_url: Superset base URL.
        session: Authenticated session.

    Returns:
        List of permissions associated with the role.
    """
    url = base_url or client.get_base_url()
    sess = session or client.get_authenticated_session(base_url=url)

    try:
        response = sess.get(f"{url}/api/v1/security/roles/{role_id}/permissions/", timeout=30)
    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")

    result = client.handle_response(response, "Get role permissions")
    return list(result.get("result", []))
