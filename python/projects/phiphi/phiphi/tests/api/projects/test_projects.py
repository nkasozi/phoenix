"""Test Projects."""

from unittest import mock

import pytest
import sqlalchemy
from fastapi.testclient import TestClient

from phiphi.api.projects import crud, models
from phiphi.seed import job_runs as seed_job_runs
from phiphi.seed import projects as project_seed


def test_project_seeded(session: sqlalchemy.orm.Session, reseed_tables) -> None:
    """Test that the database is seeded."""
    response = session.execute(
        sqlalchemy.select(sqlalchemy.func.count()).select_from(models.Project)
    )
    count = response.one()
    assert count
    # One is deleted
    assert count[0] == 7


def test_get_all_active_project_ids(session: sqlalchemy.orm.Session, reseed_tables) -> None:
    """Test that we can get all active project ids."""
    projects = crud.get_all_active_project_ids(session=session)
    # Brittle to check that the delete projects are not included
    assert len(projects) == 6
    assert projects[0] > projects[1]
    assert isinstance(projects[0], int)

    filtered_projects = crud.get_all_active_project_ids(session=session, offset=1, limit=2)
    assert len(filtered_projects) == 2
    assert filtered_projects[0] == projects[1]
    assert filtered_projects[1] == projects[2]

    filtered_projects = crud.get_all_active_project_ids(session=session, offset=100, limit=0)
    assert len(filtered_projects) == 0


CREATED_TIME = "2024-04-01T12:00:01"
UPDATE_TIME = "2024-04-01T12:00:02"


@pytest.mark.patch_settings(
    {"USE_MOCK_BQ": False, "ADD_BIG_QUERY_RATE_LIMITS_ON_PROJECT_CREATION": True}
)
@mock.patch("phiphi.pipeline_jobs.projects.delete_project_db")
@mock.patch("phiphi.pipeline_jobs.project_resources.run_provision_deployment")
@pytest.mark.freeze_time(CREATED_TIME)
def test_create_get_delete_project(
    mock_run_provision_deployment,
    mock_delete_db,
    reseed_tables,
    client_admin: TestClient,
    patch_settings,
) -> None:
    """Test create and then get of an project."""
    # Setup mock to return a flow run
    mock_flow_run = mock.MagicMock()
    mock_flow_run.id = "test-flow-run-id"
    mock_flow_run.name = "test-flow-run-name"
    mock_run_provision_deployment.return_value = mock_flow_run

    response = client_admin.get("/projects/")
    assert response.status_code == 200
    projects = response.json()
    orginal_projects_count = len(projects)
    assert orginal_projects_count > 0

    data = {
        "name": "first project",
        "description": "Project 1",
        "workspace_slug": "main",
        "pi_deleted_after_days": 90,
        "delete_after_days": 20,
        "expected_usage": "weekly",
        "initial_credit_allocation_amount": 2000,
        "initial_credit_allocation_description": "Test",
    }
    response = client_admin.post("/projects/", json=data)
    assert response.status_code == 200
    project = response.json()
    assert project["name"] == data["name"]
    assert project["description"] == data["description"]
    assert project["workspace_slug"] == data["workspace_slug"]
    assert project["pi_deleted_after_days"] == data["pi_deleted_after_days"]
    assert project["delete_after_days"] == data["delete_after_days"]
    assert project["expected_usage"] == data["expected_usage"]
    assert project["created_at"] == CREATED_TIME
    assert project["checked_problem_statement"] is False
    assert project["checked_sources"] is False
    assert project["checked_gather"] is False
    assert project["checked_classify"] is False
    assert project["checked_visualise"] is False
    assert project["checked_explore"] is False
    assert project["has_unlimited_credits"] is False
    # project_resources_provisioned_at is None because provisioning happens in background
    assert project["project_resources_provisioned_at"] is None
    # Values are only in ProjectDetail
    assert "total_costs" not in project
    assert "total_allocated_credits" not in project
    assert "estimated_total_costs" not in project

    # Verify deployment was triggered with correct parameters
    mock_run_provision_deployment.assert_called_once()
    call_args = mock_run_provision_deployment.call_args[0][0]
    assert call_args["project_id"] == project["id"]
    assert call_args["project_namespace"] == f"project_id{project['id']}"
    assert call_args["workspace_slug"] == "main"
    assert call_args["provision_bigquery"] is True
    assert call_args["provision_rate_limits"] is True

    response = client_admin.get(f"/projects/{project['id']}")
    assert response.status_code == 200

    project = response.json()

    assert project["name"] == data["name"]
    assert project["description"] == data["description"]
    assert project["created_at"] == CREATED_TIME
    assert project["workspace_slug"] == data["workspace_slug"]
    assert project["pi_deleted_after_days"] == data["pi_deleted_after_days"]
    assert project["delete_after_days"] == data["delete_after_days"]
    assert project["last_job_run_completed_at"] is None
    assert project["latest_job_run"] is None
    # We do have total_costs in the get
    assert project["total_costs"] == 0.0
    # No credit
    assert project["total_allocated_credits"] == 2000
    # Will always be greater than or equal to total_costs
    assert project["estimated_total_costs"] >= project["total_costs"]

    response = client_admin.get("/projects/")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == orginal_projects_count + 1

    response = client_admin.delete(f"/projects/{project['id']}")
    assert response.status_code == 200
    mock_delete_db.assert_called_once_with(f"project_id{project['id']}")

    response = client_admin.get(f"/projects/{project['id']}")
    assert response.status_code == 404

    response = client_admin.get("/projects/")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == orginal_projects_count


@pytest.mark.patch_settings(
    {"USE_MOCK_BQ": False, "ADD_BIG_QUERY_RATE_LIMITS_ON_PROJECT_CREATION": True}
)
@mock.patch("phiphi.pipeline_jobs.project_resources.run_provision_deployment")
def test_create_project_error_deployment(
    mock_run_provision_deployment,
    reseed_tables,
    client_admin: TestClient,
    session,
    patch_settings,
) -> None:
    """Test create project if there is an error starting the deployment."""
    project_list = crud.get_all_projects(session=session)
    mock_run_provision_deployment.side_effect = ValueError("Deployment error")
    data = {
        "name": "first project",
        "description": "Project 1",
        "workspace_slug": "main",
        "pi_deleted_after_days": 90,
        "delete_after_days": 20,
        "expected_usage": "weekly",
    }
    with pytest.raises(ValueError):
        client_admin.post("/projects/", json=data)
    mock_run_provision_deployment.assert_called_once()
    # Project should be rolled back since deployment failed
    project_list_after_failed_create = crud.get_all_projects(session=session)
    assert len(project_list) == len(project_list_after_failed_create)


@mock.patch("phiphi.pipeline_jobs.project_resources.run_provision_deployment")
@pytest.mark.patch_settings({"PROVISION_PROJECT_RESOURCES_ON_PROJECT_CREATE": False})
def test_create_project_provisioning_disabled(
    mock_run_provision_deployment,
    reseed_tables,
    client_admin: TestClient,
    session,
    patch_settings,
) -> None:
    """Test create project when provisioning is disabled."""
    project_list = crud.get_all_projects(session=session)
    data = {
        "name": "first project",
        "description": "Project 1",
        "workspace_slug": "main",
        "pi_deleted_after_days": 90,
        "delete_after_days": 20,
        "expected_usage": "weekly",
    }
    response = client_admin.post("/projects/", json=data)
    assert response.status_code == 200
    project = response.json()
    # project_resources_provisioned_at is None when provisioning is disabled
    assert project["project_resources_provisioned_at"] is None
    project_list_after_create = crud.get_all_projects(session=session)
    assert len(project_list_after_create) == len(project_list) + 1
    mock_run_provision_deployment.assert_not_called()


@mock.patch("phiphi.pipeline_jobs.project_resources.run_provision_deployment")
def test_create_project_not_authorised(
    mock_run_provision_deployment,
    reseed_tables,
    client_no_user: TestClient,
) -> None:
    """Test create project with unauthorised user."""
    data = {
        "name": "first project",
        "description": "Project 1",
        "workspace_slug": "main",
        "pi_deleted_after_days": 90,
        "delete_after_days": 20,
        "expected_usage": "weekly",
    }
    response = client_no_user.post("/projects/", json=data)
    mock_run_provision_deployment.assert_not_called()
    assert response.status_code == 401


@mock.patch("phiphi.pipeline_jobs.project_resources.run_provision_deployment")
def test_create_project_invalid_credit_allocation(
    mock_run_provision_deployment,
    reseed_tables,
    client_admin: TestClient,
) -> None:
    """Test create project with invalid credit_allocation."""
    data = {
        "name": "first project",
        "description": "Project 1",
        "workspace_slug": "main",
        "pi_deleted_after_days": 90,
        "delete_after_days": 20,
        "expected_usage": "weekly",
        "has_unlimited_credits": False,
        "initial_credit_allocation_amount": 2000,
        # No initial_credit_allocation_description
    }
    response = client_admin.post("/projects/", json=data)
    mock_run_provision_deployment.assert_not_called()
    assert response.status_code == 422
    assert "required" in str(response.json())

    data = {
        "name": "first project",
        "description": "Project 1",
        "workspace_slug": "main",
        "pi_deleted_after_days": 90,
        "delete_after_days": 20,
        "expected_usage": "weekly",
        "has_unlimited_credits": False,
        # Cannot have a negative initial credit amount
        "initial_credit_allocation_amount": -2000,
    }
    response = client_admin.post("/projects/", json=data)
    mock_run_provision_deployment.assert_not_called()
    assert response.status_code == 422


@pytest.mark.patch_settings({"USE_MOCK_BQ": False})
@mock.patch("phiphi.pipeline_jobs.projects.delete_project_db")
def test_delete_project_error_init(
    mock_project_delete_db,
    reseed_tables,
    client_admin: TestClient,
    session,
    patch_settings,
) -> None:
    """Test delete project if there is an error in delete_project_db."""
    project_list = crud.get_all_projects(session=session)
    mock_project_delete_db.side_effect = ValueError("Error")
    with pytest.raises(ValueError):
        client_admin.delete("/projects/1")
    mock_project_delete_db.assert_called_once()
    project_list_after_failed_delete = crud.get_all_projects(session=session)
    assert len(project_list) == len(project_list_after_failed_delete)


@pytest.mark.patch_settings(
    {"USE_MOCK_BQ": True, "ADD_BIG_QUERY_RATE_LIMITS_ON_PROJECT_CREATION": True}
)
@mock.patch("phiphi.pipeline_jobs.project_resources.run_provision_deployment")
def test_create_project_mock_bq(
    mock_run_provision_deployment,
    reseed_tables,
    client_admin: TestClient,
    patch_settings,
) -> None:
    """Test create project if USE_MOCK_BQ is True."""
    mock_flow_run = mock.MagicMock()
    mock_flow_run.id = "test-flow-run-id"
    mock_flow_run.name = "test-flow-run-name"
    mock_run_provision_deployment.return_value = mock_flow_run

    data = {
        "name": "first project",
        "description": "Project 1",
        "workspace_slug": "main",
        "pi_deleted_after_days": 90,
        "delete_after_days": 20,
        "expected_usage": "weekly",
    }
    response = client_admin.post("/projects/", json=data)
    assert response.status_code == 200

    # Verify deployment was triggered with provision_bigquery=False (USE_MOCK_BQ=True)
    mock_run_provision_deployment.assert_called_once()
    call_args = mock_run_provision_deployment.call_args[0][0]
    assert call_args["provision_bigquery"] is False
    assert call_args["provision_rate_limits"] is True


@pytest.mark.patch_settings(
    {"USE_MOCK_BQ": True, "ADD_BIG_QUERY_RATE_LIMITS_ON_PROJECT_CREATION": False}
)
@mock.patch("phiphi.pipeline_jobs.project_resources.run_provision_deployment")
def test_create_project_not_add_big_query_rate_limits(
    mock_run_provision_deployment,
    reseed_tables,
    client_admin: TestClient,
    patch_settings,
) -> None:
    """Test create project if not configured to add rate limits."""
    mock_flow_run = mock.MagicMock()
    mock_flow_run.id = "test-flow-run-id"
    mock_flow_run.name = "test-flow-run-name"
    mock_run_provision_deployment.return_value = mock_flow_run

    data = {
        "name": "first project",
        "description": "Project 1",
        "workspace_slug": "main",
        "pi_deleted_after_days": 90,
        "delete_after_days": 20,
        "expected_usage": "weekly",
    }
    response = client_admin.post("/projects/", json=data)
    assert response.status_code == 200

    # Verify deployment was triggered with provision_rate_limits=False
    mock_run_provision_deployment.assert_called_once()
    call_args = mock_run_provision_deployment.call_args[0][0]
    assert call_args["provision_bigquery"] is False
    assert call_args["provision_rate_limits"] is False


@mock.patch("phiphi.pipeline_jobs.project_resources.run_provision_deployment")
def test_create_project_has_unlimited_credits(
    mock_run_provision_deployment,
    reseed_tables,
    client_admin: TestClient,
) -> None:
    """Test create project when setting `has_unlimited_credits` to True."""
    mock_flow_run = mock.MagicMock()
    mock_flow_run.id = "test-flow-run-id"
    mock_flow_run.name = "test-flow-run-name"
    mock_run_provision_deployment.return_value = mock_flow_run

    data = {
        "name": "first project",
        "description": "Project 1",
        "workspace_slug": "main",
        "pi_deleted_after_days": 90,
        "delete_after_days": 20,
        "expected_usage": "weekly",
        "has_unlimited_credits": True,
    }
    response = client_admin.post("/projects/", json=data)
    assert response.status_code == 200
    project = response.json()
    assert project["has_unlimited_credits"] is True

    response = client_admin.get(f"/projects/{project['id']}")
    assert response.status_code == 200
    project = response.json()
    assert project["has_unlimited_credits"] is True
    assert project["total_allocated_credits"] == 0.0


@mock.patch("phiphi.pipeline_jobs.project_resources.run_provision_deployment")
def test_create_project_has_unlimited_credits_false(
    mock_run_provision_deployment,
    reseed_tables,
    client_admin: TestClient,
) -> None:
    """Test create project with default has_unlimited_credits.

    Testing that a default project has no credits.
    """
    mock_flow_run = mock.MagicMock()
    mock_flow_run.id = "test-flow-run-id"
    mock_flow_run.name = "test-flow-run-name"
    mock_run_provision_deployment.return_value = mock_flow_run

    data = {
        "name": "first project",
        "description": "Project 1",
        "workspace_slug": "main",
        "pi_deleted_after_days": 90,
        "delete_after_days": 20,
        "expected_usage": "weekly",
    }
    response = client_admin.post("/projects/", json=data)
    assert response.status_code == 200
    project = response.json()
    assert project["has_unlimited_credits"] is False

    response = client_admin.get(f"/projects/{project['id']}")
    assert response.status_code == 200
    project = response.json()
    assert project["has_unlimited_credits"] is False
    assert project["total_allocated_credits"] == 0.0


@pytest.mark.patch_settings({"USE_MOCK_BQ": True})
@mock.patch("phiphi.pipeline_jobs.projects.delete_project_db")
def test_delete_project_mock_bq(
    mock_project_delete_db, reseed_tables, client_admin: TestClient, session, patch_settings
) -> None:
    """Test delete project if there is an error in delete_project_db."""
    response = client_admin.delete("/projects/1")
    assert response.status_code == 200
    # Not called because USE_MOCK_BQ is True
    mock_project_delete_db.assert_not_called()
    # Project has been deleted
    project_response = client_admin.get("/projects/1")
    assert project_response.status_code == 404


@pytest.mark.patch_settings({"USE_MOCK_BQ": True})
@mock.patch("phiphi.pipeline_jobs.projects.delete_project_db")
def test_delete_project_unauthorisation(
    mock_project_delete_db, reseed_tables, client: TestClient, session, patch_settings
) -> None:
    """Test delete project with unauthorised user."""
    response = client.delete("/projects/1")
    mock_project_delete_db.assert_not_called()
    assert response.status_code == 401


def test_get_project_not_found(client_admin: TestClient, reseed_tables) -> None:
    """Test getting an project that does not exist."""
    response = client_admin.get("/projects/100000")
    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}


def test_get_project_admin(client_admin: TestClient, reseed_tables) -> None:
    """Test getting an project with admin."""
    seeded_project = project_seed.SEEDED_PROJECTS[0]
    response = client_admin.get(f"/projects/{seeded_project.id}")
    assert response.status_code == 200
    project = response.json()
    assert project["id"] == seeded_project.id
    assert project["name"] == seeded_project.name
    assert project["description"] == seeded_project.description
    assert project["workspace_slug"] == seeded_project.workspace_slug
    assert project["pi_deleted_after_days"] == seeded_project.pi_deleted_after_days
    assert project["delete_after_days"] == seeded_project.delete_after_days
    assert project["expected_usage"] == seeded_project.expected_usage
    assert project["created_at"] == seeded_project.created_at.isoformat()
    # The values of these are tested in other unit tests
    assert "last_job_run_completed_at" in project
    assert "latest_job_run" in project
    assert project["checked_problem_statement"] is False
    assert project["checked_sources"] is False
    assert project["checked_gather"] is False
    assert project["checked_classify"] is False
    assert project["checked_visualise"] is False
    assert project["checked_explore"] is False
    # seeded credit
    assert project["total_allocated_credits"] == 2010.1


def test_get_project_user(client_user_1: TestClient, reseed_tables) -> None:
    """Test getting an project with user for project."""
    seeded_project = project_seed.SEEDED_PROJECTS[0]
    response = client_user_1.get(f"/projects/{seeded_project.id}")
    assert response.status_code == 200
    project = response.json()
    assert project["id"] == seeded_project.id


def test_get_project_user_no_access(client_user_1: TestClient, reseed_tables) -> None:
    """Test getting an project with user for project."""
    seeded_project = project_seed.SEEDED_PROJECTS[1]
    response = client_user_1.get(f"/projects/{seeded_project.id}")
    assert response.status_code == 403


@pytest.mark.patch_settings({"USE_COOKIE_AUTH": False})
def test_get_projects_admin(client_admin: TestClient, reseed_tables, patch_settings) -> None:
    """Test getting projects with admin user."""
    response = client_admin.get("/projects/")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 6
    # Deleted projects are not included
    assert projects[0]["id"] == 7
    assert projects[1]["id"] == 6
    assert projects[2]["id"] == 5
    assert projects[3]["id"] == 3

    # The list projects should not get the job data
    assert "latest_job_run" not in projects[0]
    assert "last_job_run_completed_at" not in projects[0]


def test_get_projects_user(client_user_1: TestClient, reseed_tables, patch_settings) -> None:
    """Test getting projects with user."""
    response = client_user_1.get("/projects/")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 1
    assert projects[0]["id"] == 1


def test_get_projects_pagination(client_admin: TestClient, reseed_tables, patch_settings) -> None:
    """Test getting users with pagination."""
    response = client_admin.get("/projects/?start=1&end=1")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 1
    assert projects[0]["id"] == 6


@pytest.mark.freeze_time(UPDATE_TIME)
def test_update_project(
    client_admin: TestClient, reseed_tables, session: sqlalchemy.orm.Session
) -> None:
    """Test updating an project."""
    data = {"description": "New project", "checked_problem_statement": True}
    project_id = 1
    response = client_admin.put(f"/projects/{project_id}", json=data)
    assert response.status_code == 200
    project = response.json()
    assert project["description"] == data["description"]
    orm_project = session.get(models.Project, project_id)
    assert orm_project
    assert orm_project.description == data["description"]
    assert orm_project.checked_problem_statement is True
    assert orm_project.updated_at.isoformat() == UPDATE_TIME


def test_update_project_not_found(client_admin: TestClient, reseed_tables) -> None:
    """Test updating an project that does not exist."""
    data = {"description": "New project"}
    response = client_admin.put("/projects/100", json=data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}


def test_update_project_resources_provisioned_at(
    client_admin: TestClient, reseed_tables, session: sqlalchemy.orm.Session
) -> None:
    """Test updating project_resources_provisioned_at to null and back to datetime."""
    project_id = 1
    # Verify project starts with provisioned_at set
    orm_project = session.get(models.Project, project_id)
    assert orm_project
    assert orm_project.project_resources_provisioned_at is not None

    # Set to null
    response = client_admin.put(
        f"/projects/{project_id}", json={"project_resources_provisioned_at": None}
    )
    assert response.status_code == 200
    project = response.json()
    assert project["project_resources_provisioned_at"] is None
    session.refresh(orm_project)
    assert orm_project.project_resources_provisioned_at is None

    # Set back to a datetime
    new_datetime = "2024-05-01T10:00:00"
    response = client_admin.put(
        f"/projects/{project_id}", json={"project_resources_provisioned_at": new_datetime}
    )
    assert response.status_code == 200
    project = response.json()
    assert project["project_resources_provisioned_at"] == new_datetime
    session.refresh(orm_project)
    assert orm_project.project_resources_provisioned_at is not None


def test_update_project_superset_role_ids(
    client_admin: TestClient, reseed_tables, session: sqlalchemy.orm.Session
) -> None:
    """Test that the PUT endpoint can set and clear superset role IDs."""
    project_id = 1
    orm_project = session.get(models.Project, project_id)
    assert orm_project

    # Set role IDs via PUT
    response = client_admin.put(
        f"/projects/{project_id}",
        json={"superset_view_role_id": 10, "superset_edit_role_id": 20},
    )
    assert response.status_code == 200
    project = response.json()
    assert project["superset_view_role_id"] == 10
    assert project["superset_edit_role_id"] == 20
    session.refresh(orm_project)
    assert orm_project.superset_view_role_id == 10
    assert orm_project.superset_edit_role_id == 20

    # Clear role IDs via PUT
    response = client_admin.put(
        f"/projects/{project_id}",
        json={"superset_view_role_id": None, "superset_edit_role_id": None},
    )
    assert response.status_code == 200
    project = response.json()
    assert project["superset_view_role_id"] is None
    assert project["superset_edit_role_id"] is None
    session.refresh(orm_project)
    assert orm_project.superset_view_role_id is None
    assert orm_project.superset_edit_role_id is None


def test_set_project_resources_provisioned_stores_role_ids(
    session: sqlalchemy.orm.Session, reseed_tables
) -> None:
    """Test set_project_resources_provisioned persists superset role IDs and dashboard_id."""
    project_id = 1
    crud.set_project_resources_provisioned(
        session=session,
        project_id=project_id,
        dashboard_id=99,
        superset_view_role_id=10,
        superset_edit_role_id=20,
    )
    orm_project = session.get(models.Project, project_id)
    assert orm_project
    session.refresh(orm_project)
    assert orm_project.superset_view_role_id == 10
    assert orm_project.superset_edit_role_id == 20
    assert orm_project.dashboard_id == 99

    # Passing None for any field must not wipe the stored values
    crud.set_project_resources_provisioned(
        session=session,
        project_id=project_id,
        dashboard_id=None,
        superset_view_role_id=None,
        superset_edit_role_id=None,
    )
    session.refresh(orm_project)
    assert orm_project.superset_view_role_id == 10
    assert orm_project.superset_edit_role_id == 20
    assert orm_project.dashboard_id == 99


def test_update_project_unauthorised(client: TestClient, reseed_tables) -> None:
    """Test updating an project with unauthorised user."""
    data = {"description": "New project"}
    response = client.put("/projects/1", json=data)
    assert response.status_code == 401


def test_update_project_checklist(
    client_user_1: TestClient, reseed_tables, session: sqlalchemy.orm.Session
) -> None:
    """Test updating project checklist with user access."""
    project_id = 1
    data = {"checked_problem_statement": True, "checked_sources": True}
    response = client_user_1.put(f"/projects/{project_id}/checklist", json=data)
    assert response.status_code == 200
    project = response.json()
    assert project["checked_problem_statement"] is True
    assert project["checked_sources"] is True
    assert project["checked_gather"] is False
    orm_project = session.get(models.Project, project_id)
    assert orm_project
    assert orm_project.checked_problem_statement is True
    assert orm_project.checked_sources is True


def test_update_project_checklist_admin(
    client_admin: TestClient, reseed_tables, session: sqlalchemy.orm.Session
) -> None:
    """Test updating project checklist with admin."""
    project_id = 1
    data = {"checked_gather": True}
    response = client_admin.put(f"/projects/{project_id}/checklist", json=data)
    assert response.status_code == 200
    project = response.json()
    assert project["checked_gather"] is True


def test_update_project_checklist_no_access(client_user_1: TestClient, reseed_tables) -> None:
    """Test updating project checklist without access."""
    # User 1 does not have access to project 2
    project_id = 2
    data = {"checked_problem_statement": True}
    response = client_user_1.put(f"/projects/{project_id}/checklist", json=data)
    assert response.status_code == 403


def test_update_project_checklist_not_found(client_admin: TestClient, reseed_tables) -> None:
    """Test updating project checklist for non-existent project."""
    data = {"checked_problem_statement": True}
    response = client_admin.put("/projects/100000/checklist", json=data)
    assert response.status_code == 404


def test_project_not_provisioned_use_vs_view(client_admin: TestClient, reseed_tables) -> None:
    """Test that unprovisioned project returns 409 for use access and 200 for view access."""
    # Project 7 has project_resources_provisioned_at=None
    project_id = 7

    # View access (get_project_detail) should return 200
    response = client_admin.get(f"/projects/{project_id}")
    assert response.status_code == 200
    project = response.json()
    assert project["project_resources_provisioned_at"] is None

    # Use access (update_project_checklist) should return 409
    data = {"checked_problem_statement": True}
    response = client_admin.put(f"/projects/{project_id}/checklist", json=data)
    assert response.status_code == 409
    assert "resources are still being provisioned" in response.json()["detail"]


@mock.patch("phiphi.pipeline_jobs.project_resources.run_provision_deployment")
def test_workspace_defaults_main(
    mock_run_provision_deployment,
    client_admin: TestClient,
    reseed_tables,
) -> None:
    """Test that workspace defaults to main, when nothing is passed as parameter."""
    mock_flow_run = mock.MagicMock()
    mock_flow_run.id = "test-flow-run-id"
    mock_flow_run.name = "test-flow-run-name"
    mock_run_provision_deployment.return_value = mock_flow_run

    data = {
        "name": "first project",
        "description": "Project 1",
        "pi_deleted_after_days": 90,
        "delete_after_days": 20,
        "expected_usage": "one_off",
    }
    response = client_admin.post("/projects/", json=data)
    mock_run_provision_deployment.assert_called_once()
    assert response.status_code == 200
    project = response.json()
    assert project["workspace_slug"] == "main"


@mock.patch("phiphi.pipeline_jobs.project_resources.run_provision_deployment")
@pytest.mark.freeze_time(CREATED_TIME)
def test_create_project_with_non_existing_workspace(
    mock_run_provision_deployment,
    reseed_tables,
    client_admin: TestClient,
) -> None:
    """Test create and then get of an project, with a workspace that doesn't exist."""
    data = {
        "name": "first project",
        "description": "Project 1",
        "workspace_slug": "non-existing",
        "pi_deleted_after_days": 90,
        "delete_after_days": 20,
        "expected_usage": "weekly",
    }
    response = client_admin.post("/projects/", json=data)
    mock_run_provision_deployment.assert_not_called()
    assert response.status_code == 400
    assert response.json() == {"detail": "Workspace not found"}


@pytest.mark.freeze_time(CREATED_TIME)
def test_project_with_latest_job_run(client_admin: TestClient, reseed_tables) -> None:
    """Test that the latest job run is returned."""
    response = client_admin.get("/projects/1")
    assert response.status_code == 200
    project = response.json()
    assert project["last_job_run_completed_at"] == "2024-04-01T12:00:23"
    # The job_run that is completed is not the same as the latest_job_run
    assert project["latest_job_run"]["id"] == 23
    assert project["latest_job_run"]["completed_at"] != project["last_job_run_completed_at"]


@pytest.mark.freeze_time(CREATED_TIME)
def test_project_with_latest_job_run_2(client_admin: TestClient, reseed_tables) -> None:
    """Test that the latest job run is returned."""
    response = client_admin.get("/projects/2")
    assert response.status_code == 200
    project = response.json()
    # This job run is not completed and is the latest
    assert project["last_job_run_completed_at"] is None
    assert project["latest_job_run"]["id"] == 6
    assert project["latest_job_run"]["completed_at"] == project["last_job_run_completed_at"]


@pytest.mark.freeze_time(CREATED_TIME)
def test_project_estimated_total_costs(client_admin: TestClient, reseed_tables) -> None:
    """Test that the estimated total costs is calculated correctly."""
    job_run_create_1 = seed_job_runs.TEST_GATHER_COMPLETED_JOB_RUN_PROJECT_6_WITH_ESTIMATED_COSTS_1
    # Needed for mypy
    assert job_run_create_1.estimated_total_cost
    job_run_1_estimate = job_run_create_1.estimated_total_cost
    job_run_1_cost = (
        seed_job_runs.TEST_GATHER_COMPLETED_JOB_RUN_PROJECT_6_WITH_ESTIMATED_COSTS_1_TOTAL_COST
    )
    job_run_create_2 = seed_job_runs.TEST_GATHER_RUNNING_JOB_RUN_PROJECT_6_WITH_ESTIMATED_COSTS_2
    # Needed for mypy
    assert job_run_create_2.estimated_total_cost
    job_run_2_estimate = job_run_create_2.estimated_total_cost
    assert job_run_1_estimate > job_run_1_cost
    response = client_admin.get("/projects/6")
    assert response.status_code == 200
    project = response.json()
    assert project["total_costs"] == job_run_1_cost
    assert project["estimated_total_costs"] == job_run_2_estimate + job_run_1_cost
