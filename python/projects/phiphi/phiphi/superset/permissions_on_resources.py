"""Superset permissions on resource endpoint operations.

api/vi/security/permissions-resources.
"""

import logging
from typing import Any

import requests

from phiphi.superset import client, exceptions

logger = logging.getLogger(__name__)


def get_permissions_related_to_view_menu(
    view_menu_id: int | None,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> list[dict[str, Any]] | None:
    """Get permissions related to a view menu.

    Args:
        view_menu_id: The ID of the view menu whose permissions are to be retrieved.
        base_url: Superset base URL.
        session: Authenticated session.

    Returns:
        A dictionary containing the permissions data related to the specified view menu.
    """
    url = base_url or client.get_base_url()
    sess = session or client.get_authenticated_session(base_url=url)

    try:
        if view_menu_id is None:
            logger.warning("View menu ID is None, cannot retrieve permissions")
            return None
        response = sess.get(
            f"{url}/api/v1/security/permissions-resources/",
            params={"q": f"(filters:!((col:view_menu,opr:rel_o_m,value:{view_menu_id})))"},
            timeout=30,
        )
    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")
    except requests.exceptions.Timeout as e:
        raise exceptions.SupersetTimeoutError(f"Request to Superset timed out: {e}")

    result = client.handle_response(response, "Get permissions related to view menu")
    permissions = result.get("result", [])
    return permissions if permissions else None
