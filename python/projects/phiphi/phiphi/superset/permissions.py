"""Superset permission operations."""

import logging

import requests

from phiphi.superset import dataset
from phiphi.superset.permissions_on_resources import get_permissions_related_to_view_menu
from phiphi.superset.resources import get_view_menu_id_by_resource_name

logger = logging.getLogger(__name__)


def get_permission_id_on_view_menu_and_permission_type(
    view_menu_name: str,
    permission_type: str,
    logger: logging.Logger,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> int | None:
    """Get the permission ID for a specific permission type on a view menu.

    Looks up the permission-resource mapping ID for a given permission type
    (e.g., 'datasource_access') on a specified view menu resource.

    Args:
        view_menu_name: Name of the view menu resource.
        permission_type: Type of permission to look up (e.g., 'datasource_access').
        base_url: Superset base URL.
        session: Authenticated session.
        logger: Logger instance for logging operations.

    Returns:
        Permission ID if found, None otherwise.
    """
    logger.info(
        f"Looking up permission-resource mapping ID "
        f"for {permission_type} permission for {view_menu_name}"
    )

    view_menu_id = get_view_menu_id_by_resource_name(
        name=view_menu_name, base_url=base_url, session=session
    )
    related_permissions = get_permissions_related_to_view_menu(
        view_menu_id=view_menu_id, base_url=base_url, session=session
    )
    if not related_permissions:
        logger.warning(f"Could not find permissions related to view menu {view_menu_name}")
        return None

    for permission in related_permissions:
        if permission["permission"]["name"] == permission_type:
            return int(permission["id"])

    logger.warning(f"Could not find {permission_type} permission for {view_menu_name}")
    return None


def collect_datasource_access_permission_ids(
    db_name: str,
    project_namespace: str,
    table_names: list[str],
    logger: logging.Logger = logger,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> list[int]:
    """Collect datasource_access permission IDs for project tables.

    For each table, looks up the dataset and resolves its
    datasource_access permission-resource mapping ID.

    Args:
        db_name: Superset database name.
        project_namespace: Project namespace (schema).
        table_names: List of table names to look up.
        logger: Logger instance.
        base_url: Superset base URL.
        session: Authenticated session.

    Returns:
        List of resolved permission-resource mapping IDs.
    """
    permission_view_ids = []
    for table_name in table_names:
        ds = dataset.get_dataset_by_schema_table(
            schema=project_namespace,
            table_name=table_name,
            base_url=base_url,
            session=session,
        )
        if ds:
            ds_id = ds["id"]
            view_menu_name = f"[{db_name}].[{table_name}](id:{ds_id})"
            permission_id = get_permission_id_on_view_menu_and_permission_type(
                view_menu_name=view_menu_name,
                permission_type="datasource_access",
                logger=logger,
                base_url=base_url,
                session=session,
            )
            if permission_id:
                permission_view_ids.append(permission_id)
            else:
                logger.warning(f"Could not find permission view for {view_menu_name}")
        else:
            logger.warning(f"Could not find dataset for {project_namespace}.{table_name}")

    return permission_view_ids
