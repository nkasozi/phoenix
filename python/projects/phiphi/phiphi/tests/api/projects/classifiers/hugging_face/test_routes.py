"""Test Hugging Face."""

import datetime
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from prefect.client.schemas import objects

from phiphi.api.projects.classifiers.hugging_face import model_validation
from phiphi.api.projects.job_runs import schemas as job_run_schemas

CREATED_TIME = datetime.datetime(2021, 1, 1, 0, 0, 0)
UPDATE_TIME = datetime.datetime(2021, 1, 1, 1, 0, 0)


@pytest.mark.freeze_time(CREATED_TIME)
@mock.patch(
    "phiphi.api.projects.classifiers.hugging_face.model_validation.is_valid_model",
    return_value=True,
)
@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_create_hugging_face_classifier(
    m_run_deployment, m_is_valid_model, reseed_tables, client_admin: TestClient
) -> None:
    """Test create Hugging Face classifier."""
    mock_flow_run = mock.MagicMock(spec=objects.FlowRun)
    mock_flow_run.id = "mock_uuid"
    mock_flow_run.name = "mock_flow_run"
    m_run_deployment.return_value = mock_flow_run
    model_id = "distilbert-base-uncased-finetuned-sst-2-english"
    data = {
        "name": "First Hugging Face classifier",
        "description": "Test Classifier Description",
        "latest_version": {
            "params": {
                "model_id": model_id,
            }
        },
    }
    project_id = 1
    response = client_admin.post(f"/projects/{project_id}/classifiers/hugging_face/", json=data)
    assert response.status_code == 200
    m_is_valid_model.assert_called_once_with(model_id)
    classifier = response.json()

    assert classifier["name"] == data["name"]
    assert classifier["id"] is not None
    assert classifier["project_id"] == project_id
    latest_version = classifier["latest_version"]
    #  assert latest_version["params"]["model_id"] == data["latest_version"]["params"]["model_id"]
    assert latest_version["params"]["bucketing_configs"] == [
        {
            "class_name": "*",
            "buckets": [
                {"name": "low_prob", "upper_threshold": 0.25},
                {"name": "medium_prob", "upper_threshold": 0.5},
                {"name": "high_prob", "upper_threshold": 0.75},
                {"name": "very_high_prob", "upper_threshold": 1.0},
            ],
        }
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


EXCEPTION = model_validation.InvalidModelError(error_key="test", message="Invalid model ID")


@pytest.mark.freeze_time(CREATED_TIME)
@mock.patch(
    "phiphi.api.projects.classifiers.hugging_face.model_validation.is_valid_model",
    side_effect=EXCEPTION,
)
@mock.patch("phiphi.api.projects.job_runs.prefect_deployment.wrapped_run_deployment")
def test_create_hugging_face_classifier_invalid_model(
    m_run_deployment, m_is_valid_model, reseed_tables, client_admin: TestClient
) -> None:
    """Test create Hugging Face classifier with invalid model."""
    mock_flow_run = mock.MagicMock(spec=objects.FlowRun)
    mock_flow_run.id = "mock_uuid"
    mock_flow_run.name = "mock_flow_run"
    m_run_deployment.return_value = mock_flow_run
    model_id = "invalid"
    data = {
        "name": "First Hugging Face classifier",
        "description": "Test Classifier Description",
        "latest_version": {
            "params": {
                "model_id": model_id,
            }
        },
    }
    project_id = 1
    response = client_admin.post(f"/projects/{project_id}/classifiers/hugging_face/", json=data)
    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "message": "Invalid model ID",
            "error_key": "test",
        }
    }
    m_is_valid_model.assert_called_once_with(model_id)
    m_run_deployment.assert_not_called()
