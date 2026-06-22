"""Tests for pipeline_job_params."""

import unittest.mock as mock

from phiphi.api.projects.job_runs import pipeline_job_params, schemas


def test_pipeline_job_params_classify_all_tabulate_form() -> None:
    """Test form for classify_all_tabulate job type."""
    project_id = 5
    project_namespace = "project_id5"
    job_source_id = 0
    job_run_id = 99
    classifiers_params = {"classifiers_dict_list": [{"id": 1}]}
    tabulate_params = {"active_classifiers_versions": [(1, 1)]}

    with (
        mock.patch.object(
            pipeline_job_params, "get_all_classifiers_params", return_value=classifiers_params
        ),
        mock.patch.object(
            pipeline_job_params, "get_tabulate_flow_params", return_value=tabulate_params
        ),
    ):
        result = pipeline_job_params.form(
            project_id=project_id,
            project_namespace=project_namespace,
            job_type=schemas.ForeignJobType.classify_all_tabulate,
            job_source_id=job_source_id,
            job_run_id=job_run_id,
        )

    assert result.deployment_name == "classify_all_tabulate_flow/classify_all_tabulate_flow"
    assert result.parameters["project_id"] == project_id
    assert result.parameters["job_source_id"] == job_source_id
    assert result.parameters["job_run_id"] == job_run_id
    assert result.parameters["project_namespace"] == project_namespace
    assert (
        result.parameters["classifiers_dict_list"] == classifiers_params["classifiers_dict_list"]
    )
    assert (
        result.parameters["active_classifiers_versions"]
        == tabulate_params["active_classifiers_versions"]
    )


def test_pipeline_job_params_classify_all_tabulate_form_seeded(reseed_tables) -> None:
    """Test form for classify_all_tabulate using seeded classifiers."""
    project_id = 1
    project_namespace = "project_id1"
    job_source_id = 0
    job_run_id = 10

    result = pipeline_job_params.form(
        project_id=project_id,
        project_namespace=project_namespace,
        job_type=schemas.ForeignJobType.classify_all_tabulate,
        job_source_id=job_source_id,
        job_run_id=job_run_id,
    )

    assert result.deployment_name == "classify_all_tabulate_flow/classify_all_tabulate_flow"
    assert result.parameters["project_id"] == project_id
    assert result.parameters["job_source_id"] == job_source_id
    assert result.parameters["job_run_id"] == job_run_id
    assert result.parameters["project_namespace"] == project_namespace
    classifiers_dict_list = result.parameters["classifiers_dict_list"]
    active_classifiers_versions = result.parameters["active_classifiers_versions"]
    assert len(classifiers_dict_list) > 0
    assert len(active_classifiers_versions) > 0
    for classifier_dict in classifiers_dict_list:
        assert "id" in classifier_dict
        assert "latest_version" in classifier_dict
        latest_version = classifier_dict["latest_version"]
        assert latest_version is not None
        assert "version_id" in latest_version
        assert (classifier_dict["id"], latest_version["version_id"]) in active_classifiers_versions
