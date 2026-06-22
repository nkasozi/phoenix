"""Test Perspective API."""

import datetime
from typing import Any
from unittest import mock

import freezegun
import pytest
from fastapi.testclient import TestClient
from prefect.client.schemas import objects

from phiphi.api.projects.job_runs import schemas as job_run_schemas
from phiphi.seed.classifiers import perspective_api_seed

CREATED_TIME = datetime.datetime(2021, 1, 1, 0, 0, 0)
UPDATE_TIME = datetime.datetime(2021, 1, 1, 1, 0, 0)

DEFAULT_BUCKET_PARAMS: dict[str, Any] = {
    "flirtation": {"buckets": [], "enabled": False},
    "identity_attack": {"buckets": [], "enabled": False},
    "insult": {"buckets": [], "enabled": False},
    "severe_toxicity": {"buckets": [], "enabled": False},
    "sexually_explicit": {"buckets": [], "enabled": False},
    "threat": {"buckets": [], "enabled": False},
    "toxicity": {"buckets": [], "enabled": False},
}


@pytest.mark.freeze_time(CREATED_TIME)
@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_create_perspective_api_classifier(
    m_run_deployment, reseed_tables, client_admin: TestClient
) -> None:
    """Test create perspective_api classifier."""
    mock_flow_run = mock.MagicMock(spec=objects.FlowRun)
    mock_flow_run.id = "mock_uuid"
    mock_flow_run.name = "mock_flow_run"
    m_run_deployment.return_value = mock_flow_run
    data = {
        "name": "First perspective API classifier",
        "description": "Test Classifier Description",
        "latest_version": {
            "params": {
                "toxicity": {
                    "enabled": True,
                    "buckets": [
                        {"name": "low", "upper_threshold": 0.5},
                        {"name": "high", "upper_threshold": 1.0},
                    ],
                }
            }
        },
    }
    project_id = 1
    response = client_admin.post(f"/projects/{project_id}/classifiers/perspective_api/", json=data)
    assert response.status_code == 200
    classifier = response.json()

    assert classifier["name"] == data["name"]
    assert classifier["id"] is not None
    assert classifier["project_id"] == project_id
    assert classifier["type"] == "perspective_api"
    assert classifier["archived_at"] is None
    assert classifier["created_at"] == CREATED_TIME.isoformat()
    version = classifier["latest_version"]
    params: dict[str, Any] = version.get("params", {})

    expected_params = DEFAULT_BUCKET_PARAMS | params
    assert version["params"] == expected_params
    assert version["created_at"] == CREATED_TIME.isoformat()
    assert version["classes"] == [
        {"name": "low_toxicity", "description": "Score bucket 'low' for attribute 'toxicity'"},
        {"name": "high_toxicity", "description": "Score bucket 'high' for attribute 'toxicity'"},
    ]

    m_run_deployment.assert_called_once_with(
        name="flow_runner_flow/flow_runner_flow",
        parameters={
            "project_id": project_id,
            "job_type": job_run_schemas.ForeignJobType.classify_tabulate,
            "job_source_id": classifier["id"],
            "job_run_id": mock.ANY,
        },
        job_variables=job_run_schemas.FLOW_RUNNER_FLOW_JOB_VARIABLES,
    )


@pytest.mark.freeze_time(CREATED_TIME)
@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_version_and_run_perspective_api_classifier(
    m_run_deployment, reseed_tables, client_admin: TestClient
) -> None:
    """Test version_and_run perspective_api classifier."""
    seed_classifier = perspective_api_seed.TEST_PERSPECTIVE_API_CLASSIFIERS[0]
    project_id = seed_classifier.project_id
    classifier_id = seed_classifier.id
    mock_flow_run = mock.MagicMock(spec=objects.FlowRun)
    mock_flow_run.id = "mock_uuid"
    mock_flow_run.name = "mock_flow_run"
    m_run_deployment.return_value = mock_flow_run
    # Now create a new version using the version_and_run endpoint.
    # Not toxicity to check that the buckets are completely overwritten
    version_data = {
        "params": {
            "severe_toxicity": {
                "enabled": True,
                "buckets": [
                    {"name": "medium", "upper_threshold": 0.8},
                    {"name": "extreme", "upper_threshold": 1.0},
                ],
            },
            "flirtation": {
                "enabled": True,
                "buckets": [
                    {"name": "low", "upper_threshold": 0.5},
                    {"name": "high", "upper_threshold": 1.0},
                ],
            },
        }
    }
    with freezegun.freeze_time(UPDATE_TIME):
        version_response = client_admin.post(
            f"/projects/{project_id}/classifiers/perspective_api/{classifier_id}/version_and_run",
            json=version_data,
        )
    assert version_response.status_code == 200

    updated_classifier = version_response.json()
    updated_version = updated_classifier["latest_version"]

    params: dict[str, Any] = updated_version.get("params", {})

    expected_params = DEFAULT_BUCKET_PARAMS | params
    assert updated_version["params"] == expected_params

    # Ensure we've got the newly created version as the latest_version
    assert updated_version["created_at"] == UPDATE_TIME.isoformat()
    assert "medium_severe_toxicity" in {
        class_info["name"] for class_info in updated_version["classes"]
    }
    assert "extreme_severe_toxicity" in {
        class_info["name"] for class_info in updated_version["classes"]
    }
    assert "low_flirtation" in {class_info["name"] for class_info in updated_version["classes"]}
    assert "high_flirtation" in {class_info["name"] for class_info in updated_version["classes"]}

    m_run_deployment.assert_called_once_with(
        name="flow_runner_flow/flow_runner_flow",
        parameters={
            "project_id": project_id,
            "job_type": job_run_schemas.ForeignJobType.classify_tabulate,
            "job_source_id": classifier_id,
            "job_run_id": mock.ANY,
        },
        job_variables=job_run_schemas.FLOW_RUNNER_FLOW_JOB_VARIABLES,
    )
