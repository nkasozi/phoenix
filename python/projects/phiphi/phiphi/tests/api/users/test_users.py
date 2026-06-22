"""Test Users."""

import pytest
import sqlalchemy
from fastapi.testclient import TestClient

from phiphi.api.users import crud, models


def test_user(session: sqlalchemy.orm.Session, recreate_tables) -> None:
    """Test that there are no users."""
    response = session.execute(sqlalchemy.select(sqlalchemy.func.count()).select_from(models.User))
    count = response.one()
    assert count
    assert count[0] == 0


def test_user_seeded(session: sqlalchemy.orm.Session, reseed_tables) -> None:
    """Test that the database is seeded."""
    response = session.execute(sqlalchemy.select(sqlalchemy.func.count()).select_from(models.User))
    count = response.one()
    assert count
    assert count[0] == 3


def test_get_user_by_email(session: sqlalchemy.orm.Session, reseed_tables) -> None:
    """Test getting a user by email."""
    user = crud.get_user_by_email(session, "test1@phiphi.com")
    assert user


CREATED_TIME = "2024-01-01T12:00:01"
UPDATE_TIME = "2024-01-01T12:00:02"


@pytest.mark.freeze_time(CREATED_TIME)
def test_create_read_user(reseed_tables, client_admin: TestClient, patch_settings) -> None:
    """Test creating a user."""
    data = {"email": "test@test.com", "display_name": "test"}
    response = client_admin.post("/users/", json=data)
    assert response.status_code == 200
    user = response.json()
    assert user["email"] == data["email"]
    assert user["display_name"] == data["display_name"]
    assert user["created_at"] == CREATED_TIME
    # Default
    assert user["app_role"] == "user"

    response = client_admin.get(f"/users/{user['id']}")
    assert response.status_code == 200

    user = response.json()

    assert user["email"] == data["email"]
    assert user["display_name"] == data["display_name"]
    assert user["created_at"] == CREATED_TIME

    response = client_admin.post("/users/", json=data)
    assert response.status_code == 400


def test_create_user_none_admin(client_user_1: TestClient, reseed_tables) -> None:
    """Test creating a user by a non admin."""
    data = {"email": "test@test.com", "display_name": "test"}
    response = client_user_1.post("/users/", json=data)
    assert response.status_code == 403


def test_read_user_non_admin_user_match(client_user_1: TestClient, reseed_tables) -> None:
    """Test reading a user that is the same as the current user."""
    user_id = 2
    response = client_user_1.get(f"/users/{user_id}")
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == user_id


def test_read_user_non_admin_user_not_match(client_user_1: TestClient, reseed_tables) -> None:
    """Test reading a user that is the not the same as the current user and not admin."""
    response = client_user_1.get("/users/3")
    assert response.status_code == 403


def test_read_user_not_found(client_admin: TestClient, reseed_tables) -> None:
    """Test reading a user that does not exist."""
    response = client_admin.get("/users/10000")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_read_users(client_admin: TestClient, reseed_tables) -> None:
    """Test reading users."""
    response = client_admin.get("/users/")
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 3


def test_read_users_no_access(client_user_1: TestClient, reseed_tables) -> None:
    """Test reading users."""
    response = client_user_1.get("/users/")
    assert response.status_code == 403


def test_read_users_pagination(client_admin: TestClient, reseed_tables) -> None:
    """Test reading users with pagination."""
    response = client_admin.get("/users/?start=1&end=1")
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 1
    assert users[0]["id"] == 2


@pytest.mark.freeze_time(UPDATE_TIME)
def test_update_user_admin(
    client_admin: TestClient, reseed_tables, session: sqlalchemy.orm.Session
) -> None:
    """Test updating a user."""
    data = {"display_name": "new name"}
    user_id = 1
    response = client_admin.put(f"/users/{user_id}", json=data)
    assert response.status_code == 200
    user = response.json()
    assert user["display_name"] == data["display_name"]
    orm_user = session.get(models.User, user_id)
    assert orm_user
    assert orm_user.display_name == data["display_name"]
    assert orm_user.updated_at.isoformat() == UPDATE_TIME


@pytest.mark.freeze_time(UPDATE_TIME)
def test_update_user_non_admin(
    client_user_1: TestClient, reseed_tables, session: sqlalchemy.orm.Session
) -> None:
    """Test updating a user non admin."""
    data = {"display_name": "new name"}
    user_id = 2
    response = client_user_1.put(f"/users/{user_id}", json=data)
    assert response.status_code == 200
    user = response.json()
    assert user["display_name"] == data["display_name"]
    orm_user = session.get(models.User, user_id)
    assert orm_user
    assert orm_user.display_name == data["display_name"]
    assert orm_user.updated_at.isoformat() == UPDATE_TIME


def test_update_user_not_found(client_admin: TestClient, reseed_tables) -> None:
    """Test updating a user that does not exist."""
    data = {"display_name": "new name"}
    response = client_admin.put("/users/100000", json=data)
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_app_role_post(client_admin: TestClient, reseed_tables) -> None:
    """Test if app_role is set in users on creation."""
    data = {"email": "test@phoenix.com", "display_name": "test", "app_role": "admin"}
    response = client_admin.post("/users/", json=data)
    assert response.status_code == 200
    user = response.json()
    assert user["email"] == data["email"]
    assert user["display_name"] == data["display_name"]
    assert user["app_role"] == data["app_role"]


def test_app_role_put_admin(
    client_admin: TestClient, reseed_tables, session: sqlalchemy.orm.Session
) -> None:
    """Test update of display_name and app_role by admin."""
    data = {"display_name": "new name", "app_role": "admin"}
    user_id = 2
    response = client_admin.put(f"/users/{user_id}", json=data)
    assert response.status_code == 200
    user = response.json()
    assert user["app_role"] == data["app_role"]
    assert user["display_name"] == data["display_name"]
    orm_user = session.get(models.User, user_id)
    assert orm_user
    assert orm_user.app_role == data["app_role"]


def test_display_name_put_user_no_access(
    client_user_1: TestClient, reseed_tables, session: sqlalchemy.orm.Session
) -> None:
    """Test update display_name of a different user by non admin."""
    data = {"display_name": "new name"}
    user_id = 1
    response = client_user_1.put(f"/users/{user_id}", json=data)
    assert response.status_code == 403


def test_app_role_put_user(
    client_user_1: TestClient, reseed_tables, session: sqlalchemy.orm.Session
) -> None:
    """Test update app_role by non admin."""
    data = {"app_role": "admin"}
    user_id = 2
    response = client_user_1.put(f"/users/{user_id}", json=data)
    assert response.status_code == 403
    orm_user = session.get(models.User, user_id)
    assert orm_user
    assert orm_user.app_role != "admin"
