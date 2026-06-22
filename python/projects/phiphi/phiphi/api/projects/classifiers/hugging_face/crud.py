"""Hugging Face crud functionality."""

import sqlalchemy as sa

from phiphi.api.projects import classifiers
from phiphi.api.projects.classifiers import simple_classifier_crud
from phiphi.api.projects.classifiers.hugging_face import schemas


async def create_classifier_and_run(
    session: sa.orm.Session,
    project_id: int,
    classifier_create: schemas.HuggingFaceClassifierCreate,
) -> schemas.HuggingFaceClassifierDetail:
    """Create a hugging_face classifier."""
    return await simple_classifier_crud.create_classifier_and_run(
        session,
        project_id,
        classifier_create,
        classifiers.base_schemas.ClassifierType.hugging_face,
        schemas.HuggingFaceClassifierDetail,
    )
