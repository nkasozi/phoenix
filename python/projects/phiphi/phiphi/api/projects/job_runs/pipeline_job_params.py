"""Form params for pipeline job deployments."""

import dataclasses
from typing import Any

from phiphi import (
    # Need to import the Base for the polymorphic_identity to work
    all_platform_models,  # noqa: F401
    platform_db,
)
from phiphi.api.projects import classifiers, gathers
from phiphi.api.projects.job_runs import schemas


@dataclasses.dataclass
class PipelineJobParams:
    """Pipeline job parameters."""

    deployment_name: str
    parameters: dict[str, Any]


def get_gather_flow_params(project_id: int, gather_id: int) -> dict[str, Any]:
    """Get the parameters for the gather flow."""
    with platform_db.get_session_context() as session:
        gather = gathers.child_crud.get_child_gather(
            session=session, project_id=project_id, gather_id=gather_id
        )
    if gather is None:
        raise ValueError(f"Gather with {project_id=}, {gather_id=} not found.")
    params = {
        "gather_dict": gather.model_dump(),
        "gather_child_type": gather.child_type.value,
    }
    return params


def get_classify_flow_params(project_id: int, classifier_id: int) -> dict[str, Any]:
    """Get the parameters for the classify flow."""
    with platform_db.get_session_context() as session:
        classifier = classifiers.crud.get_pipeline_classifier(
            session=session, project_id=project_id, classifier_id=classifier_id
        )
    if classifier is None:
        raise ValueError(
            f"Classifier with {project_id=}, {classifier_id=} not found, "
            " or is not a valid pipeline classifier."
            "Check `classifiers.crud.get_pipeline_classifier` for more information."
        )
    params = {
        "classifier_dict": classifier.model_dump(),
    }
    return params


def get_all_classifiers_params(project_id: int) -> dict[str, Any]:
    """Get list of specs for all classifiers."""
    with platform_db.get_session_context() as session:
        # We don't want to include single run classifiers in the gather classify tabulate flow
        classifiers_list = classifiers.crud.get_pipeline_classifiers(
            session=session, project_id=project_id, include_single_run_classifiers=False
        )
    params = {
        "classifiers_dict_list": [_classifier.model_dump() for _classifier in classifiers_list],
    }
    return params


def get_tabulate_flow_params(project_id: int) -> dict[str, Any]:
    """Get the parameters for the tabulate flow.

    Tabulate needs to know which classifiers are still active in the project, and what their latest
    version is, so that it can pull the correct classification data.
    """
    with platform_db.get_session_context() as session:
        # We want to include_single_run_classifiers in the active classifiers
        classifiers_list = classifiers.crud.get_pipeline_classifiers(
            session=session, project_id=project_id, include_single_run_classifiers=True
        )
    params = {
        "active_classifiers_versions": [
            (_classifier.id, _classifier.latest_version.version_id)
            for _classifier in classifiers_list
        ],
    }
    return params


def form(
    project_id: int,
    project_namespace: str,
    job_type: schemas.ForeignJobType,
    job_source_id: int,
    job_run_id: int,
) -> PipelineJobParams:
    """Form parameters and deployment name for the flow_runner_flow run deployment.

    Args:
        project_id: Project ID.
        project_namespace: Project namespace.
        job_type: Job type.
        job_source_id: Job source ID.
        job_run_id: Job run ID.

    Returns:
        Parameters for the flow_runner_flow run deployment.
    """
    base_params = {"job_run_id": job_run_id, "project_namespace": project_namespace}

    # Mapping from job type to a tuple of (deployment_name, parameter updater lambda)
    job_config = {
        schemas.ForeignJobType.gather: (
            "gather_flow/gather_flow",
            lambda: get_gather_flow_params(project_id=project_id, gather_id=job_source_id),
        ),
        schemas.ForeignJobType.classify: (
            "classify_flow/classify_flow",
            lambda: get_classify_flow_params(project_id=project_id, classifier_id=job_source_id),
        ),
        schemas.ForeignJobType.tabulate: (
            "tabulate_flow/tabulate_flow",
            lambda: get_tabulate_flow_params(project_id=project_id),
        ),
        schemas.ForeignJobType.delete_gather: (
            "delete_gather_flow/delete_gather_flow",
            lambda: {"gather_id": job_source_id},
        ),
        schemas.ForeignJobType.gather_classify_tabulate: (
            "gather_classify_tabulate_flow/gather_classify_tabulate_flow",
            lambda: (
                get_gather_flow_params(project_id=project_id, gather_id=job_source_id)
                | get_all_classifiers_params(project_id=project_id)
                | get_tabulate_flow_params(project_id=project_id)
            ),
        ),
        schemas.ForeignJobType.classify_tabulate: (
            "classify_tabulate_flow/classify_tabulate_flow",
            lambda: (
                get_classify_flow_params(project_id=project_id, classifier_id=job_source_id)
                | get_tabulate_flow_params(project_id=project_id)
            ),
        ),
        schemas.ForeignJobType.classify_all_tabulate: (
            "classify_all_tabulate_flow/classify_all_tabulate_flow",
            lambda: (
                get_all_classifiers_params(project_id=project_id)
                | get_tabulate_flow_params(project_id=project_id)
            ),
        ),
        schemas.ForeignJobType.delete_gather_tabulate: (
            "delete_gather_tabulate_flow/delete_gather_tabulate_flow",
            lambda: get_tabulate_flow_params(project_id=project_id),
        ),
        schemas.ForeignJobType.classifier_archive: (
            "tabulate_flow/tabulate_flow",
            lambda: get_tabulate_flow_params(project_id=project_id),
        ),
        schemas.ForeignJobType.classifier_restore: (
            "tabulate_flow/tabulate_flow",
            lambda: get_tabulate_flow_params(project_id=project_id),
        ),
    }

    if job_type not in job_config:
        raise NotImplementedError(f"Job type {job_type=} not implemented yet.")

    deployment_name, params_getter = job_config[job_type]
    params = base_params | params_getter()

    # Add additional parameters for composite flows.
    if job_type in {
        schemas.ForeignJobType.gather_classify_tabulate,
        schemas.ForeignJobType.classify_tabulate,
        schemas.ForeignJobType.classify_all_tabulate,
        schemas.ForeignJobType.delete_gather_tabulate,
    }:
        params = params | {"project_id": project_id, "job_source_id": job_source_id}

    return PipelineJobParams(deployment_name=deployment_name, parameters=params)
