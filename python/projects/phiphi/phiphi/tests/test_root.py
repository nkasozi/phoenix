"""Test root functionality.

This module tests the most basic root functionality of the app.
"""

import sqlalchemy
from fastapi.testclient import TestClient

from phiphi import config


def test_get_root(client: TestClient) -> None:
    """Get the root hello world."""
    resp = client.get("/")
    content = resp.json()
    assert resp.status_code == 200
    assert content["title"] == config.settings.TITLE


def test_get_health(client: TestClient) -> None:
    """Get the explicit health endpoint used by load balancers."""
    resp = client.get("/health")
    content = resp.json()
    assert resp.status_code == 200
    assert content["title"] == config.settings.TITLE


def test_db(session: sqlalchemy.orm.Session, recreate_tables) -> None:
    """Check the db connection."""
    select_query = sqlalchemy.select(1)
    response = session.execute(select_query)
    result = response.first()
    assert result
    assert result[0] == 1
