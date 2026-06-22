"""Superset dataset operations."""

from typing import Any

import requests

from phiphi.superset import client, exceptions


# GOTCHA: There is a gotcha with this function.
# If for some reason the dataset appears twice in Superset
# e.g., Say we have two datasets 1 and 2 with the following details
# dataset 1 - schema: project_id123, table_name: tabulated_messages, id: 1, database: {name: dev}
# dataset 2 - schema: project_id123, table_name: tabulated_messages, id: 2, database: {name: prod}
# This function will return the first dataset returned in the list
# Problems being that:
#  - You wouldn't know if the correct dataset was returned.
#  - This is a non-idempotent operation.
#
# Right now, our envs have one connection and unique schema.table_name combinations.
def get_dataset_by_schema_table(
    schema: str,
    table_name: str,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> dict[str, Any] | None:
    """Find dataset by schema and table name.

    Args:
        schema: Dataset schema (e.g., "project_id123").
        table_name: Table name (e.g., "tabulated_messages").
        base_url: Superset base URL.
        session: Authenticated session (created if not provided).

    Returns:
        Dataset dict if found, None otherwise.

    Raises:
        SupersetConnectionError: If Superset is unavailable.
        SupersetAPIError: If API request fails.
    """
    url = base_url or client.get_base_url()
    sess = session or client.get_authenticated_session(base_url=url)

    try:
        response = sess.get(
            f"{url}/api/v1/dataset/",
            # Superset's API expects valid Rison query syntax.
            params={
                "q": (
                    f"(filters:!((col:schema,opr:eq,value:'{schema}'),"
                    f"(col:table_name,opr:eq,value:'{table_name}')))"
                )
            },
            timeout=30,
        )
    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")

    result = client.handle_response(response, "Get dataset")
    datasets = result.get("result", [])
    return datasets[0] if datasets else None


def delete_dataset(
    dataset_id: int,
    base_url: str | None = None,
    session: requests.Session | None = None,
) -> None:
    """Delete dataset by ID (idempotent).

    Args:
        dataset_id: ID of the dataset to delete.
        base_url: Superset base URL.
        session: Authenticated session (created if not provided).

    Raises:
        SupersetConnectionError: If Superset is unavailable.
        SupersetAPIError: If delete fails (except 404).
    """
    url = base_url or client.get_base_url()
    sess = session or client.get_authenticated_session(base_url=url)

    try:
        response = sess.delete(f"{url}/api/v1/dataset/{dataset_id}", timeout=30)
    except requests.exceptions.ConnectionError as e:
        raise exceptions.SupersetConnectionError(f"Cannot connect to Superset: {e}")

    if response.status_code != 404:
        client.handle_response(response, "Delete dataset")
