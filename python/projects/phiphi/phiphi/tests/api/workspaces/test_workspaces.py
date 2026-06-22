"""Test Workspaces."""

import pytest
import sqlalchemy
from fastapi.testclient import TestClient

from phiphi.api.workspaces import models

CREATED_TIME = "2024-04-01T12:00:01"
UPDATE_TIME = "2024-04-01T12:00:02"


@pytest.mark.freeze_time(CREATED_TIME)
def test_create_get_workspace(recreate_tables, client: TestClient) -> None:
    """Test creating and get of an workspace."""
    data = {"description": "My workspace", "name": "test", "slug": "test-workspace"}
    response = client.post("/workspaces/", json=data)
    assert response.status_code == 200
    workspace = response.json()
    assert workspace["description"] == data["description"]
    assert workspace["name"] == data["name"]
    assert workspace["slug"] == data["slug"]
    assert workspace["created_at"] == CREATED_TIME

    response = client.get(f"/workspaces/{workspace['slug']}")
    assert response.status_code == 200

    workspace = response.json()

    assert workspace["description"] == data["description"]
    assert workspace["name"] == data["name"]
    assert workspace["slug"] == data["slug"]
    assert workspace["created_at"] == CREATED_TIME


def test_get_workspace_not_found(client: TestClient, recreate_tables) -> None:
    """Test getting an workspace that does not exist."""
    response = client.get("/workspaces/boys")
    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_get_workspaces(client: TestClient, reseed_tables) -> None:
    """Test getting workspaces."""
    response = client.get("/workspaces/")
    assert response.status_code == 200
    workspaces = response.json()
    assert len(workspaces) == 3


@pytest.mark.freeze_time(UPDATE_TIME)
def test_update_workspace(
    client: TestClient, reseed_tables, session: sqlalchemy.orm.Session
) -> None:
    """Test updating an workspace."""
    data = {"description": "new_workspace"}
    workspace_id = 1
    response = client.put(f"/workspaces/{workspace_id}", json=data)
    assert response.status_code == 200
    workspace = response.json()
    assert workspace["description"] == data["description"]
    orm_workspace = session.get(models.Workspace, workspace_id)
    assert orm_workspace
    assert orm_workspace.description == data["description"]
    assert orm_workspace.updated_at.isoformat() == UPDATE_TIME


def test_update_workspace_not_found(client: TestClient, recreate_tables) -> None:
    """Test updating an workspace that does not exist."""
    data = {"description": "new_workspace"}
    response = client.put("/workspaces/1", json=data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Workspace not found"}


def test_slug_already_exists(recreate_tables, client: TestClient) -> None:
    """Test that slug already exists."""
    data = {"description": "test workspace", "name": "test", "slug": "test"}
    response = client.post("/workspaces/", json=data)
    assert response.status_code == 200
    workspace_1 = response.json()
    assert workspace_1["description"] == data["description"]
    assert workspace_1["name"] == data["name"]
    assert workspace_1["slug"] == data["slug"]

    data_2 = {"description": "test workspace 2", "name": "test", "slug": "test"}
    response = client.post("/workspaces/", json=data_2)
    assert response.status_code == 400

    ##check if slug changes with an already existing slug
    response = client.get("/workspaces/slug/?workspace_name=test")
    assert response.status_code == 200
    slug = response.json()
    assert slug["slug"] != "test"


def test_slug_with_name(recreate_tables, client: TestClient) -> None:
    """Test that slug can be gotten from given name."""
    response = client.get("/workspaces/slug/?workspace_name=my slug")
    assert response.status_code == 200
    slug = response.json()
    assert slug["slug"] == "my-slug"


def test_slug_get_with_name_exsists(reseed_tables, client: TestClient) -> None:
    """Test that slug can be gotten from given name and generates a new slug."""
    response = client.get("/workspaces/slug/?workspace_name=phoenix")
    assert response.status_code == 200
    slug = response.json()
    assert slug["slug"] != "phoenix"
    slug_parts = slug["slug"].split("-")
    assert slug_parts[0] == "phoenix"
    assert len(slug_parts[1]) == 4
