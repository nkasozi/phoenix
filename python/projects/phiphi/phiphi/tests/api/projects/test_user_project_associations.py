"""Test user project associations."""

import sqlalchemy as sa
from fastapi.testclient import TestClient

from phiphi.seed import users as seed_users


def test_user_project_associations_create(
    reseed_tables: sa.orm.Session, client_admin: TestClient
) -> None:
    """Test creating a user project association."""
    data = {"role": "user"}
    response = client_admin.post("/projects/1/users/3", json=data)
    assert response.status_code == 200
    association = response.json()
    assert association["user_id"] == 3
    assert association["project_id"] == 1
    assert association["role"] == "user"


def test_user_project_associations_create_duplicate(
    reseed_tables: sa.orm.Session, client_admin: TestClient
) -> None:
    """Test creating a user project association that is duplicate."""
    data = {"role": "user"}
    response = client_admin.post("/projects/1/users/2", json=data)
    assert response.status_code == 400
    json = response.json()
    assert json == {"detail": "User project association already exists"}


def test_user_project_associations_delete(
    reseed_tables: sa.orm.Session, client_admin: TestClient
) -> None:
    """Test deleting a user project association."""
    response = client_admin.delete("/projects/1/users/2")
    assert response.status_code == 200


def test_user_project_associations_delete_not_found(
    reseed_tables: sa.orm.Session, client_admin: TestClient
) -> None:
    """Test deleting a user project association."""
    response = client_admin.delete("/projects/1/users/3")
    assert response.status_code == 404
    json = response.json()
    assert json == {"detail": "User project association not found"}


def test_user_project_associations_get(
    reseed_tables: sa.orm.Session, client_admin: TestClient
) -> None:
    """Test getting user project associations."""
    response = client_admin.get("/projects/1/users/")
    assert response.status_code == 200
    associations = response.json()
    assert len(associations) == 1
    assert associations[0]["user_id"] == 2
    assert associations[0]["project_id"] == 1
    assert associations[0]["email"] == seed_users.TEST_USER_1_CREATE.email
    assert associations[0]["display_name"] == seed_users.TEST_USER_1_CREATE.display_name
    assert associations[0]["role"] == "user"


def test_user_project_associations_403(
    reseed_tables: sa.orm.Session, client_user_1: TestClient
) -> None:
    """Test getting user project associations no permission."""
    response = client_user_1.get("/projects/1/users/")
    assert response.status_code == 403
