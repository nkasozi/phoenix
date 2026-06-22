"""Test job runs routes."""

import datetime
import json

from fastapi.testclient import TestClient

from phiphi.api.projects.job_runs import crud, schemas
from phiphi.seed import job_runs as seed_job_runs

CREATED_TIME = "2024-04-01T12:00:01"
UPDATE_TIME = "2024-04-01T12:00:02"
STARTED_PROCESSING_TIME = "2024-04-01T12:00:03"
COMPLETED_TIME = "2024-04-01T12:00:04"


def test_get_job_runs(client_admin: TestClient, reseed_tables) -> None:
    """Test getting job runs."""
    response = client_admin.get("/projects/1/job_runs/?start=0&end=10")
    assert response.status_code == 200
    job_runs = response.json()
    length = 10
    assert len(job_runs) == length
    # Assert desc id
    assert job_runs[length - 1]["id"] < job_runs[0]["id"]

    response = client_admin.get("/projects/2/job_runs/")
    assert response.status_code == 200
    job_runs = response.json()
    assert len(job_runs) == 1
    assert job_runs[0]["id"] == 6


def test_get_job_runs_user_access(client_user_1: TestClient, reseed_tables) -> None:
    """Test getting job runs."""
    response = client_user_1.get("/projects/1/job_runs/?start=0&end=10")
    assert response.status_code == 200


def test_get_job_runs_no_user_access(client_user_1: TestClient, reseed_tables) -> None:
    """Test getting job runs."""
    response = client_user_1.get("/projects/2/job_runs/?start=0&end=10")
    assert response.status_code == 403


def test_get_job_runs_no_access(client: TestClient, reseed_tables) -> None:
    """Test getting job runs."""
    response = client.get("/projects/2/job_runs/?start=0&end=10")
    assert response.status_code == 401


def test_get_job_runs_by_type(client_admin: TestClient, reseed_tables) -> None:
    """Test getting job runs."""
    response = client_admin.get("/projects/1/job_runs/?foreign_job_type=gather")
    assert response.status_code == 200
    job_runs = response.json()
    assert len(job_runs) == 1
    assert job_runs[0]["id"] == 2
    assert job_runs[0]["foreign_job_type"] == "gather"

    response = client_admin.get("/projects/1/job_runs/?foreign_job_type=gather_classify_tabulate")
    assert response.status_code == 200
    job_runs = response.json()
    assert len(job_runs) == 6
    # Assert desc id
    assert job_runs[-2]["id"] == 4
    assert job_runs[-2]["foreign_job_type"] == "gather_classify_tabulate"
    assert job_runs[-1]["id"] == 1
    assert job_runs[-1]["foreign_job_type"] == "gather_classify_tabulate"


def test_get_job_runs_pagination(client_admin: TestClient, reseed_tables) -> None:
    """Test getting job runs with pagination."""
    response = client_admin.get("/projects/1/job_runs/?start=0&end=1")
    assert response.status_code == 200
    job_runs = response.json()
    assert len(job_runs) == 1


def test_get_job_run(client_admin: TestClient, reseed_tables) -> None:
    """Test getting job runs."""
    job_run_response = seed_job_runs.SEEDED_JOB_RUNS[0]
    response = client_admin.get(
        f"/projects/{job_run_response.project_id}/job_runs/{job_run_response.id}"
    )
    assert response.status_code == 200
    job_run = response.json()
    assert job_run == json.loads(job_run_response.model_dump_json())


def test_get_job_run_user_access(client_user_1: TestClient, reseed_tables) -> None:
    """Test getting job runs."""
    job_run_response = seed_job_runs.SEEDED_JOB_RUNS[0]
    response = client_user_1.get(
        f"/projects/{job_run_response.project_id}/job_runs/{job_run_response.id}"
    )
    assert response.status_code == 200


def test_get_job_run_no_user_access(client_user_1: TestClient, reseed_tables) -> None:
    """Test getting job runs."""
    job_run_response = seed_job_runs.SEEDED_JOB_RUNS[5]
    response = client_user_1.get(
        f"/projects/{job_run_response.project_id}/job_runs/{job_run_response.id}"
    )
    assert response.status_code == 403


def test_get_job_run_no_access(client: TestClient, reseed_tables) -> None:
    """Test getting job runs."""
    job_run_response = seed_job_runs.SEEDED_JOB_RUNS[0]
    response = client.get(
        f"/projects/{job_run_response.project_id}/job_runs/{job_run_response.id}"
    )
    assert response.status_code == 401


def test_crud_update_completed_job_run(reseed_tables) -> None:
    """Test updating a job run."""
    # 5 has not been completed
    job_run_response = seed_job_runs.SEEDED_JOB_RUNS[5]
    completed = schemas.JobRunUpdateCompleted(
        id=job_run_response.id,
        completed_at=datetime.datetime.fromisoformat(UPDATE_TIME),
        status=schemas.Status.completed_successfully,
        total_cost=2.0,
        gather_result_count=1,
    )
    job_run_completed = crud.update_job_run(reseed_tables, completed)
    assert job_run_completed.id == job_run_response.id
    assert job_run_completed.completed_at is not None
    assert job_run_completed.completed_at.isoformat() == UPDATE_TIME
    assert job_run_completed.status == schemas.Status.completed_successfully
    assert job_run_completed.total_cost == 2.0
    assert job_run_completed.gather_result_count == 1


def test_crud_update_completed_job_run_no_cost(reseed_tables) -> None:
    """Test updating a job run."""
    # 5 has not been completed
    job_run_response = seed_job_runs.SEEDED_JOB_RUNS[5]
    completed = schemas.JobRunUpdateCompleted(
        id=job_run_response.id,
        completed_at=datetime.datetime.fromisoformat(UPDATE_TIME),
        status=schemas.Status.completed_successfully,
    )
    job_run_completed = crud.update_job_run(reseed_tables, completed)
    assert job_run_completed.id == job_run_response.id
    assert job_run_completed.completed_at is not None
    assert job_run_completed.completed_at.isoformat() == UPDATE_TIME
    assert job_run_completed.status == schemas.Status.completed_successfully
    assert job_run_completed.total_cost is None
    assert job_run_completed.gather_result_count is None


def test_update_job_run(client_admin: TestClient, reseed_tables) -> None:
    """Test updating a job run with all fields in the update schema."""
    # Prepare an update payload with all possible fields from JobRunUpdateRoute.
    update_data = {
        "status": schemas.Status.failed,
        "flow_run_id": "new_flow_run_id",
        "flow_run_name": "new_flow_run_name",
        "started_processing_at": STARTED_PROCESSING_TIME,
        "completed_at": COMPLETED_TIME,
        "total_cost": 1000,
        "is_total_cost_estimated": True,
        "gather_result_count": 99,
        "gather_normalise_error_count": 9,
    }
    # Get a seeded job run and ensure the update data is different.
    seeded_job_run = seed_job_runs.SEEDED_JOB_RUNS[0]
    for key, value in update_data.items():
        # Note: seeded_job_run is a dict so we can compare its stored values.
        seed_value = getattr(seeded_job_run, key)
        # For datetime fields, convert to ISO string for comparison
        if key in {"started_processing_at", "completed_at"} and seed_value is not None:
            seed_value = seed_value.isoformat()
        assert seed_value != value, f"Seed value for {key} should differ from update value"
    project_id = seeded_job_run.project_id
    # Use the update endpoint defined in routes.py (PATCH method)
    response = client_admin.patch(
        f"/projects/{project_id}/job_runs/{seeded_job_run.id}", json=update_data
    )
    assert response.status_code == 200

    # Parse the response into a JobRunResponse instance.
    returned_job_run = schemas.JobRunResponse.model_validate(response.json())

    # Check the updated field.
    for field, expected_value in update_data.items():
        actual_value = getattr(returned_job_run, field)
        # If the field is expected to be a datetime, compare the ISO formatted string.
        if field in {"started_processing_at", "completed_at"} and actual_value is not None:
            actual_value = actual_value.isoformat()
        assert actual_value == expected_value, f"Field {field} did not update correctly."


def test_update_job_run_not_found(client_admin: TestClient, reseed_tables) -> None:
    """Test updating a job run that does not exist returns a 404 error."""
    update_data = {"total_cost": 500}
    project_id = 1  # Assuming project 1 exists.
    response = client_admin.patch(f"/projects/{project_id}/job_runs/99999", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Job Run not found"


def test_update_job_run_unauthorised(client: TestClient, reseed_tables) -> None:
    """Test updating a job run with an unauthorised user returns a 401 error."""
    seeded_job_run = seed_job_runs.SEEDED_JOB_RUNS[0]
    update_data = {"total_cost": 500}
    project_id = seeded_job_run.project_id
    response = client.patch(
        f"/projects/{project_id}/job_runs/{seeded_job_run.id}", json=update_data
    )
    assert response.status_code == 401


def test_update_job_run_total_cost_only(client_admin: TestClient, reseed_tables) -> None:
    """Test updating only total_cost for a job run so that other values remain unchanged."""
    seeded_job_run = seed_job_runs.SEEDED_JOB_RUNS[0]
    project_id = seeded_job_run.project_id

    # Parse the seeded job run into a JobRunResponse instance for easier attribute access.
    original_job_run = schemas.JobRunResponse.model_validate(seeded_job_run)

    # Prepare update data with just the total_cost.
    update_data = {"total_cost": 1500}
    response = client_admin.patch(
        f"/projects/{project_id}/job_runs/{seeded_job_run.id}", json=update_data
    )
    assert response.status_code == 200

    # Parse the response into a JobRunResponse instance.
    returned_job_run = schemas.JobRunResponse.model_validate(response.json())

    # Check the updated field.
    for field, expected_value in update_data.items():
        actual_value = getattr(returned_job_run, field)
        assert actual_value == expected_value, f"Field {field} did not update correctly."

    # Define fields that should not change.
    unchanged_fields = [
        "status",
        "flow_run_id",
        "flow_run_name",
        "is_total_cost_estimated",
        "gather_result_count",
        "gather_normalise_error_count",
    ]
    for field in unchanged_fields:
        original_value = getattr(original_job_run, field)
        updated_value = getattr(returned_job_run, field)
        # For datetime fields, compare the ISO formats if not None.
        if field in {"started_processing_at", "completed_at"} and original_value is not None:
            original_value = original_value.isoformat()
        if field in {"started_processing_at", "completed_at"} and updated_value is not None:
            updated_value = updated_value.isoformat()
        assert updated_value == original_value, f"Field {field} changed unexpectedly."


def test_replace_job_run(client_admin: TestClient, reseed_tables) -> None:
    """Test replacing a job run with all fields in the replace schema (PUT)."""
    # Prepare a replacement payload with all fields from JobRunReplaceRoute.
    replace_data = {
        "status": "failed",
        "flow_run_id": "new_flow_run_id",
        "flow_run_name": "new_flow_run_name",
        "started_processing_at": STARTED_PROCESSING_TIME,
        "completed_at": COMPLETED_TIME,
        "total_cost": 2000,
        "is_total_cost_estimated": True,
        "gather_result_count": 150,
        "gather_normalise_error_count": 15,
    }
    # Get a seeded job run.
    seeded_job_run = seed_job_runs.SEEDED_JOB_RUNS[0]
    project_id = seeded_job_run.project_id

    # Use the replace endpoint defined in routes.py (PUT method)
    response = client_admin.put(
        f"/projects/{project_id}/job_runs/{seeded_job_run.id}", json=replace_data
    )
    assert response.status_code == 200

    # Parse the response into a JobRunResponse instance.
    returned_job_run = schemas.JobRunResponse.model_validate(response.json())

    # Check all fields were replaced.
    for field, expected_value in replace_data.items():
        actual_value = getattr(returned_job_run, field)
        # If the field is expected to be a datetime, compare the ISO formatted string.
        if field in {"started_processing_at", "completed_at"} and actual_value is not None:
            actual_value = actual_value.isoformat()
        # If the field is expected to be an enum, compare string values.
        if field == "status":
            actual_value = actual_value.value if hasattr(actual_value, "value") else actual_value
        assert actual_value == expected_value, f"Field {field} did not replace correctly."


def test_replace_job_run_not_found(client_admin: TestClient, reseed_tables) -> None:
    """Test replacing a job run that does not exist returns a 404 error."""
    replace_data = {
        "status": "failed",
        "total_cost": 500,
        "is_total_cost_estimated": False,
    }
    project_id = 1  # Assuming project 1 exists.
    response = client_admin.put(f"/projects/{project_id}/job_runs/99999", json=replace_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Job Run not found"


def test_replace_job_run_unauthorised(client: TestClient, reseed_tables) -> None:
    """Test replacing a job run with an unauthorised user returns a 401 error."""
    seeded_job_run = seed_job_runs.SEEDED_JOB_RUNS[0]
    replace_data = {
        "status": "failed",
        "total_cost": 500,
        "is_total_cost_estimated": False,
    }
    project_id = seeded_job_run.project_id
    response = client.put(
        f"/projects/{project_id}/job_runs/{seeded_job_run.id}", json=replace_data
    )
    assert response.status_code == 401


def test_replace_job_run_requires_status(client_admin: TestClient, reseed_tables) -> None:
    """Test that PUT requires the status field (mandatory for full replacement)."""
    seeded_job_run = seed_job_runs.SEEDED_JOB_RUNS[0]
    project_id = seeded_job_run.project_id

    # Prepare replace data without status field (should fail validation).
    replace_data = {
        "total_cost": 1500,
        "is_total_cost_estimated": True,
    }
    response = client_admin.put(
        f"/projects/{project_id}/job_runs/{seeded_job_run.id}", json=replace_data
    )
    # Should return 422 Unprocessable Entity due to missing required field.
    assert response.status_code == 422


def test_patch_vs_put_behavior(client_admin: TestClient, reseed_tables) -> None:
    """Test that PATCH preserves unspecified fields while PUT replaces them."""
    seeded_job_run = seed_job_runs.SEEDED_JOB_RUNS[0]
    project_id = seeded_job_run.project_id

    # Get the original job run.
    original_response = client_admin.get(f"/projects/{project_id}/job_runs/{seeded_job_run.id}")
    original_job_run = schemas.JobRunResponse.model_validate(original_response.json())

    # Test PATCH - only update total_cost, other fields should remain.
    patch_data = {"total_cost": 999}
    patch_response = client_admin.patch(
        f"/projects/{project_id}/job_runs/{seeded_job_run.id}", json=patch_data
    )
    assert patch_response.status_code == 200
    patched_job_run = schemas.JobRunResponse.model_validate(patch_response.json())

    # Verify total_cost changed but status remained the same.
    assert patched_job_run.total_cost == 999
    assert patched_job_run.status == original_job_run.status
    assert patched_job_run.flow_run_id == original_job_run.flow_run_id

    # Test PUT - replace with minimal required fields.
    put_data = {
        "status": "completed_successfully",
        "total_cost": 1111,
        "is_total_cost_estimated": False,
    }
    put_response = client_admin.put(
        f"/projects/{project_id}/job_runs/{seeded_job_run.id}", json=put_data
    )
    assert put_response.status_code == 200
    replaced_job_run = schemas.JobRunResponse.model_validate(put_response.json())

    # Verify all specified fields were replaced.
    assert replaced_job_run.status.value == "completed_successfully"
    assert replaced_job_run.total_cost == 1111
    assert replaced_job_run.is_total_cost_estimated is False
    # Unspecified optional fields should be reset to None or defaults.
    assert replaced_job_run.flow_run_id is None
    assert replaced_job_run.flow_run_name is None
    assert replaced_job_run.gather_result_count is None
