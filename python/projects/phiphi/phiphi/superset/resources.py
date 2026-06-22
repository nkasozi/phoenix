"""Superset permissions on resource endpoint operations.

Route: api/vi/security/resources.

In Superset Terminology these resources are "View Menus".
See: https://superset.apache.org/developer-docs/api/security-resources-view-menus
"""

import logging

import requests

from phiphi.superset import client, exceptions

logger = logging.getLogger(__name__)


def get_view_menu_id_by_resource_name(
    name: str,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> int | None:
    """Get a view menu id by resource name.

    Apart from the defaults Superset automatically creates "view_menu" resources
    based on events.
    An example event is on the addition of a new dataset based on a database connection.
    Say dataset_name="tabulated_messages"
        dataset_id=123
        database_name="Some OLAP Prod"
        - Superset creates a view_menu called:
          [Some OLAP Prod].[tabulated_messages](id:123)
    This function finds the view_menu resource by name.

    Args:
        name: The view menu name to search for.
        base_url: The base URL of the Superset instance.
        session: An optional requests session to use for the request.

    Returns:
        The view_menu id if found, otherwise None.
    """
    url = base_url or client.get_base_url()
    sess = session or client.get_authenticated_session(base_url=url)

    try:
        response = sess.get(
            f"{url}/api/v1/security/resources/",
            params={"q": f"(filters:!((col:name,opr:eq,value:'{name}')))"},
            timeout=30,
        )
    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")
    except requests.exceptions.Timeout as e:
        raise exceptions.SupersetTimeoutError(f"Request to Superset timed out: {e}")

    # Ideally searching on name against the `ab_view_menu`
    # should return count=1, so we validate that here.
    result = client.handle_response(response, "Get resource")
    if result["count"] != 1:
        raise exceptions.SupersetError(
            f"Expected 1 resource for name '{name}', got {result['count']}"
        )

    view_menu_resource = result.get("result", [])
    return view_menu_resource[0]["id"] if view_menu_resource else None
