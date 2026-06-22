"""Test credit_allocations."""

import sqlalchemy as sa
from fastapi.testclient import TestClient


def test_credit_allocations_create(
    reseed_tables: sa.orm.Session, client_admin: TestClient
) -> None:
    """Test creating a credit allocation."""
    data = {"amount": 100, "description": "Test"}
    response = client_admin.post("/projects/1/credit_allocations", json=data)
    assert response.status_code == 200
    credit_allocation = response.json()
    # This is the id of the test admin user configured in the client
    assert credit_allocation["user_id"] == 1
    assert credit_allocation["project_id"] == 1
    assert credit_allocation["amount"] == 100
    assert credit_allocation["description"] == "Test"


def test_credit_allocations_create_unauthorisaed(
    reseed_tables: sa.orm.Session, client_user_1: TestClient
) -> None:
    """Test creating a credit allocation for unauthorized user."""
    data = {"amount": 100, "description": "Test"}
    response = client_user_1.post("/projects/1/credit_allocations", json=data)
    assert response.status_code == 403


def test_credit_allocations_get(reseed_tables: sa.orm.Session, client_admin: TestClient) -> None:
    """Test get credit allocations."""
    response = client_admin.get("/projects/1/credit_allocations/")
    assert response.status_code == 200
    credit_allocations = response.json()
    assert len(credit_allocations) == 3
    assert credit_allocations[0]["amount"] == 20.1
    assert credit_allocations[0]["description"] == "Test 3"
    assert credit_allocations[0]["user_id"] == 1
    assert credit_allocations[1]["amount"] == -10
    assert credit_allocations[1]["description"] == "Test 2"
    assert credit_allocations[2]["amount"] == 2000
    assert credit_allocations[2]["description"] == "Test"
