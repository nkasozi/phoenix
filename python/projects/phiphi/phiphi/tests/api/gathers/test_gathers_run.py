"""Test of the gather runs."""

from unittest import mock

import pytest
from fastapi.testclient import TestClient
from prefect.client.schemas import objects

from phiphi.api.projects.gathers import run
from phiphi.api.projects.job_runs import schemas as job_run_schemas
from phiphi.seed import apify_facebook_comments_gather as seed_facebook_comment_gathers
from phiphi.seed import apify_tiktok_searches_posts_gather as seed_gather
from phiphi.seed import projects as seed_projects

CREATED_TIME = "2024-04-01T12:00:01"
UPDATE_TIME = "2024-04-01T12:00:02"


@pytest.mark.parametrize(
    "gather_id, project_id",
    [
        (4, 2),
        (6, 1),
    ],
)
@pytest.mark.freeze_time(CREATED_TIME)
@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_create_get_job_runs_for_project_within_credit_usage(
    m_run_deployment,
    gather_id,
    project_id,
    reseed_tables,
    client_admin: TestClient,
) -> None:
    """Test create gather run and then get of an job run.

    This is for projects that are within credit usage.
    """
    mock_flow_run = mock.MagicMock(spec=objects.FlowRun)
    mock_flow_run.id = "mock_uuid"
    mock_flow_run.name = "mock_flow_run"
    m_run_deployment.return_value = mock_flow_run

    response = client_admin.post(f"/projects/{project_id}/gathers/{gather_id}/run")
    assert response.status_code == 200
    gather = response.json()
    job_run = gather["latest_job_run"]
    assert job_run["foreign_id"] == gather_id
    assert job_run["foreign_job_type"] == run.DEFAULT_GATHER_RUN_JOB_TYPE.value
    assert job_run["created_at"] == CREATED_TIME
    assert job_run["project_id"] == project_id
    assert job_run["status"] == job_run_schemas.Status.in_queue
    assert job_run["flow_run_id"] == "mock_uuid"
    assert job_run["flow_run_name"] == "mock_flow_run"
    assert job_run["completed_at"] is None
    assert job_run["estimated_total_cost"] == gather["job_run_resource_estimate"]["max_total_cost"]
    m_run_deployment.assert_called_once_with(
        name="flow_runner_flow/flow_runner_flow",
        parameters={
            "project_id": project_id,
            "job_type": run.DEFAULT_GATHER_RUN_JOB_TYPE.value,
            "job_source_id": gather_id,
            "job_run_id": job_run["id"],
        },
        job_variables=job_run_schemas.FLOW_RUNNER_FLOW_JOB_VARIABLES,
    )

    response = client_admin.get(f"/projects/{project_id}/job_runs/{job_run['id']}")
    assert response.status_code == 200

    job_run = response.json()
    assert job_run["id"] == job_run["id"]


@pytest.mark.freeze_time(CREATED_TIME)
@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_create_run_deployments_error(
    m_run_deployment, reseed_tables, client_admin: TestClient
) -> None:
    """Test that if an error occurs in the deployment, the job run is updated."""
    gather_id = 4
    project_id = 2

    m_run_deployment.side_effect = Exception("Error")

    response = client_admin.post(f"/projects/{project_id}/gathers/{gather_id}/run")
    assert response.status_code == 200
    gather = response.json()
    job_run = gather["latest_job_run"]
    assert job_run["foreign_id"] == gather_id
    assert job_run["foreign_job_type"] == run.DEFAULT_GATHER_RUN_JOB_TYPE.value
    assert job_run["created_at"] == CREATED_TIME
    assert job_run["project_id"] == project_id
    assert job_run["status"] == job_run_schemas.Status.failed
    assert job_run["completed_at"] == CREATED_TIME

    response = client_admin.get(f"/projects/{project_id}/job_runs/{job_run['id']}")
    assert response.status_code == 200

    job_run = response.json()
    assert job_run["id"] == job_run["id"]
    assert job_run["status"] == job_run_schemas.Status.failed

    # Second call to run gather now works as the first job is completed
    mock_flow_run = mock.MagicMock(spec=objects.FlowRun)
    mock_flow_run.id = "mock_uuid"
    mock_flow_run.name = "mock_flow_run"
    m_run_deployment.return_value = mock_flow_run
    m_run_deployment.side_effect = None
    response = client_admin.post(f"/projects/{project_id}/gathers/{gather_id}/run")
    assert response.status_code == 200
    gather_2 = response.json()
    job_run_2 = gather_2["latest_job_run"]
    assert job_run_2["foreign_id"] == gather_id
    assert job_run_2["foreign_job_type"] == run.DEFAULT_GATHER_RUN_JOB_TYPE.value
    assert job_run_2["created_at"] == CREATED_TIME
    assert job_run_2["project_id"] == project_id
    assert job_run_2["status"] == job_run_schemas.Status.in_queue
    assert job_run_2["flow_run_id"] == "mock_uuid"
    assert job_run_2["flow_run_name"] == "mock_flow_run"
    assert job_run_2["id"] != job_run["id"]


@pytest.mark.freeze_time(CREATED_TIME)
@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_create_guard_for_repeated_job_run(
    m_run_deployment, reseed_tables, client_admin: TestClient
) -> None:
    """Test don't allow to create a second running job.

    There is currently a bug in this functionality if you run a job_run of the type `gather` and
    then try to run a job_run of the type `gather_classify_tabulate` the second job_run will be
    created even though the first job_run is still running. This should not be the case.
    """
    gather_response = client_admin.get("/projects/1/gathers/1")
    gather = gather_response.json()
    job_run = gather["latest_job_run"]
    assert job_run["completed_at"] is None
    response = client_admin.post("/projects/1/gathers/1/run")
    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "Foreign object has an active job run. "
            "Type: ForeignJobType.gather_classify_tabulate, Id: 1"
        )
    }
    m_run_deployment.assert_not_called()


@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_create_guard(m_run_deployment, reseed_tables, client_admin: TestClient) -> None:
    """Test that if a gather is not found, a job run is not created."""
    # Project is not found
    response = client_admin.post("/projects/4/gathers/1/run")
    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
    m_run_deployment.assert_not_called()

    # Project is found and gather exists but the gather is not in the project
    response = client_admin.post("/projects/1/gathers/3/run")
    assert response.status_code == 400
    assert response.json() == {"detail": "Gather not found"}
    m_run_deployment.assert_not_called()


@pytest.mark.freeze_time(CREATED_TIME)
@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_create_get_job_runs_costs_guard(
    m_run_deployment, reseed_tables, client_admin: TestClient
) -> None:
    """Test create is forbidden when total of project costs exceed allocated credits."""
    gather = seed_gather.TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHERS[1]
    project_id = gather.project_id

    response = client_admin.post(f"/projects/{project_id}/gathers/{gather.id}/run")
    assert response.status_code == 403
    assert response.json() == {"detail": run.NO_REMAINING_CREDITS}
    m_run_deployment.assert_not_called()


@pytest.mark.freeze_time(CREATED_TIME)
@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_create_get_job_runs_costs_guard_for_no_credits(
    m_run_deployment, reseed_tables, client_admin: TestClient
) -> None:
    """Test create is forbidden when no allocated credits and has_unlimited_credits is False."""
    project = seed_projects.SEEDED_PROJECTS[4]
    gather = seed_gather.TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHERS[2]

    # Check project costs and credits state
    project_id = project.id
    response = client_admin.get(f"/projects/{project_id}/")
    assert response.status_code == 200
    project_detail = response.json()
    assert project_detail["has_unlimited_credits"] is False
    assert project_detail["total_costs"] == 0
    assert project_detail["total_allocated_credits"] == 0

    response = client_admin.post(f"/projects/{project_id}/gathers/{gather.id}/run")
    assert response.status_code == 403
    assert response.json() == {"detail": run.NO_REMAINING_CREDITS}
    m_run_deployment.assert_not_called()


# Make the mean cost per 100k results 50000.0 so it is 0.5 for each result
@pytest.mark.patch_settings(
    {
        "MEAN_COST_PER_100K_RESULTS_DICT": {"apify_facebook_comments": 50000.00},
        "GATHER_COST_ESTIMATE_ERROR_MARGIN": 0.95,
    }
)
@pytest.mark.freeze_time(CREATED_TIME)
@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_create_get_job_runs_costs_guard_for_estimate_above_credits(
    m_run_deployment, reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test create is forbidden when the estimated cost exceeds the allocated credits."""
    project = seed_projects.SEEDED_PROJECTS[0]
    gather = seed_facebook_comment_gathers.SEEDED_FACEBOOK_COMMENTS_GATHERS[2]

    # Check project costs and credits state
    project_id = project.id
    response = client_admin.get(f"/projects/{project_id}/")
    assert response.status_code == 200
    project_detail = response.json()
    assert project_detail["has_unlimited_credits"] is False
    assert project_detail["total_costs"] == 0
    # Check that the seeds are correct and the gather estimate is greater then the credits
    assert (
        project_detail["total_allocated_credits"] < gather.job_run_resource_estimate.max_total_cost
    )

    response = client_admin.post(f"/projects/{project_id}/gathers/{gather.id}/run")
    assert response.status_code == 403
    assert response.json() == {"detail": run.ESTIMATE_OVER_REMAINING_CREDITS}
    m_run_deployment.assert_not_called()


# Make the mean cost per 100k results 100000.0 so it is 1 for each result
@pytest.mark.patch_settings(
    {
        "MEAN_COST_PER_100K_RESULTS_DICT": {"apify_tiktok_searches_posts": 100000.00},
        "GATHER_COST_ESTIMATE_ERROR_MARGIN": 0.95,
    }
)
@pytest.mark.freeze_time(CREATED_TIME)
@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_create_get_job_runs_costs_guard_for_estimate_with_running_job_runs_above_credits(
    m_run_deployment, reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test create is forbidden when the estimated cost exceeds the allocated credits.

    This includes the estimated total costs of the running gathers in the project.
    """
    project = seed_projects.SEEDED_PROJECTS[5]
    gather = seed_gather.TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHERS[5]
    # This will be times the error margin
    assert gather.job_run_resource_estimate.max_total_cost == 53

    # Check project costs and credits state
    project_id = project.id
    response = client_admin.get(f"/projects/{project_id}/")
    assert response.status_code == 200
    project_detail = response.json()
    assert project_detail["has_unlimited_credits"] is False
    assert project_detail["total_costs"] == 50
    assert project_detail["estimated_total_costs"] == 150
    assert project_detail["total_allocated_credits"] == 200

    # Checking the seeds are correctly set up so that the gathers for project 6 do have job runs
    # Once the seeds are refactored it will be possible to remove this check
    response = client_admin.get(f"/projects/{project_id}/gathers/")
    assert response.status_code == 200
    gathers = response.json()
    assert len(gathers) == 3
    assert gathers[0]["latest_job_run"] is None
    assert gathers[1]["latest_job_run"]["status"] == job_run_schemas.Status.awaiting_start.value
    assert (
        gathers[2]["latest_job_run"]["status"]
        == job_run_schemas.Status.completed_successfully.value
    )

    response = client_admin.post(f"/projects/{project_id}/gathers/{gather.id}/run")
    assert response.status_code == 403
    assert response.json() == {
        "detail": run.ESTIMATE_INCLUDING_RUNNING_GATHERS_OVER_REMAINING_CREDITS
    }
    m_run_deployment.assert_not_called()


# Make the mean cost per 100k results 100000.0 so it is 1 for each result
@pytest.mark.patch_settings(
    {
        "MEAN_COST_PER_100K_RESULTS_DICT": {"apify_tiktok_searches_posts": 100000.00},
        "GATHER_COST_ESTIMATE_ERROR_MARGIN": 0.94,
    }
)
@pytest.mark.freeze_time(CREATED_TIME)
@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_create_get_job_runs_costs_guard_for_estimate_with_running_job_runs_below_credits(
    m_run_deployment, reseed_tables, client_admin: TestClient, patch_settings
) -> None:
    """Test create is not forbidden when the estimated cost does not exceeds the allocated credits.

    This includes the estimated total costs of the running gathers in the project.
    """
    mock_flow_run = mock.MagicMock(spec=objects.FlowRun)
    mock_flow_run.id = "mock_uuid"
    mock_flow_run.name = "mock_flow_run"
    m_run_deployment.return_value = mock_flow_run

    # Updating gather
    project = seed_projects.SEEDED_PROJECTS[5]
    gather = seed_gather.TEST_APIFY_TIKTOK_SEARCHES_POSTS_GATHERS[5]
    # This will be times the error margin
    limit = 53
    update_data = {
        "limit_posts_per_search": limit,
    }
    url = f"/projects/{project.id}/gathers/{gather.child_type.value}/{gather.id}"
    gather_response = client_admin.patch(url, json=update_data)
    assert gather_response.status_code == 200
    gather_json = gather_response.json()
    assert gather_json["limit_posts_per_search"] == limit

    # Check project costs and credits state
    project_id = project.id
    response = client_admin.get(f"/projects/{project_id}/")
    assert response.status_code == 200
    project_detail = response.json()
    assert project_detail["has_unlimited_credits"] is False
    assert project_detail["total_costs"] == 50
    assert project_detail["estimated_total_costs"] == 150
    assert project_detail["total_allocated_credits"] == 200

    response = client_admin.post(f"/projects/{project_id}/gathers/{gather.id}/run")
    assert response.status_code == 200
    m_run_deployment.assert_called_once()
