"""Module containing the Prefect flow for classify."""

from typing import Coroutine

import prefect

from phiphi import constants
from phiphi.api.projects.classifiers import base_schemas, response_schemas
from phiphi.api.projects.job_runs import pipeline_job_result_schemas
from phiphi.pipeline_jobs.classify import (
    hugging_face_classifier,
    keyword_match_classifier,
    manual_authors_classifier,
    perspective_api,
)


@prefect.flow(name="classify_flow")
async def classify_flow(
    classifier_dict: dict,  # dict of response_schemas.ClassifierPipeline
    job_run_id: int,
    project_namespace: str,
) -> pipeline_job_result_schemas.PipelineJobResult:
    """Flow which runs classifier on all (as yet unclassified by this classifier) messages.

    This flow is async because the Hugging Face classifier uses async calls.
    """
    prefect_logger = prefect.get_run_logger()
    prefect_logger.info(f"Starting classify_flow for job_run_id={job_run_id}")
    classifier = response_schemas.classifier_pipeline_adapter.validate_python(classifier_dict)

    if classifier.type == base_schemas.ClassifierType.keyword_match:
        keyword_match_classifier.classify(
            classifier=classifier, bigquery_dataset=project_namespace, job_run_id=job_run_id
        )
    elif classifier.type == base_schemas.ClassifierType.manual_post_authors:
        manual_authors_classifier.classify(
            classifier=classifier, bigquery_dataset=project_namespace, job_run_id=job_run_id
        )
    elif classifier.type == base_schemas.ClassifierType.perspective_api:
        perspective_api.classify_with_concurrency(
            classifier=classifier, bigquery_dataset=project_namespace, job_run_id=job_run_id
        )
    elif classifier.type == base_schemas.ClassifierType.hugging_face:
        _ = await hugging_face_classifier.classify(
            classifier=classifier,
            bigquery_dataset=project_namespace,
            job_run_id=job_run_id,
            logger=prefect_logger,
        )
    else:
        raise ValueError(f"{classifier.type=} not implemented.")
    return pipeline_job_result_schemas.PipelineJobResult()


def create_deployments(
    override_work_pool_name: str | None = None,
    deployment_name_prefix: str = "",
    image: str = constants.DEFAULT_IMAGE,
    tags: list[str] = [],
    build: bool = False,
    push: bool = False,
) -> list[Coroutine]:
    """Create deployments for flow.

    Args:
        override_work_pool_name (str | None): The name of the work pool to use to override the
        default work pool.
        deployment_name_prefix (str, optional): The prefix of the deployment name. Defaults to "".
        image (str, optional): The image to use for the deployments. Defaults to
        constants.DEFAULT_IMAGE.
        tags (list[str], optional): The tags to use for the deployments. Defaults to [].
        build (bool, optional): If True, build the image. Defaults to False.
        push (bool, optional): If True, push the image. Defaults to False.

    Returns:
        list[Coroutine]: List of coroutines that create deployments.
    """
    work_pool_name = str(constants.WorkPool.main)
    if override_work_pool_name:
        work_pool_name = override_work_pool_name
    task = classify_flow.deploy(
        name=deployment_name_prefix + classify_flow.name,
        work_pool_name=work_pool_name,
        image=image,
        build=build,
        push=push,
        tags=tags,
    )

    return [task]
