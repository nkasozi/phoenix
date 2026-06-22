"""Classifier Response schemas.

This copies ideas from Pydantic discriminator:
https://docs.pydantic.dev/latest/concepts/unions/#nested-discriminated-unions
"""

import datetime
from typing import Annotated, Optional, Union

import pydantic

from phiphi.api.projects.classifiers import base_schemas
from phiphi.api.projects.classifiers.hugging_face import schemas as hugging_face_schemas
from phiphi.api.projects.classifiers.keyword_match import schemas as keyword_match_schemas
from phiphi.api.projects.classifiers.manual_post_authors import (
    schemas as manual_post_authors_schemas,
)
from phiphi.api.projects.classifiers.perspective_api import schemas as perspective_api_schemas
from phiphi.api.projects.job_runs import schemas as job_runs_schemas

classifier_detail_union = Union[
    keyword_match_schemas.KeywordMatchClassifierDetail,
    manual_post_authors_schemas.ManualPostAuthorsClassifierDetail,
    perspective_api_schemas.PerspectiveAPIClassifierDetail,
    hugging_face_schemas.HuggingFaceClassifierDetail,
]

ClassifierDetail = Annotated[
    classifier_detail_union,
    # This tells pydantic to use the `type` field to determine the type of the response
    # and optimises the Union
    pydantic.Field(description="Any classifier response", discriminator="type"),
]

# This is the work around for the typing as documented here:
# https://docs.pydantic.dev/latest/api/type_adapter/#pydantic.type_adapter.TypeAdapter
classifier_detail_adapter: pydantic.TypeAdapter[classifier_detail_union] = pydantic.TypeAdapter(
    ClassifierDetail
)


class ClassifierSummary(base_schemas.ClassifierResponseBase):
    """Classifier Summary.

    Properties to return to client for a request like list the classifiers.

    Can be used to get a summary of the classifier.

    We are not using a union of sub classifiers because it improves speed and the strong typing of
    the latest_version is not needed.
    """

    archived_at: Optional[datetime.datetime]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    last_edited_at: Optional[datetime.datetime]
    latest_job_run: job_runs_schemas.JobRunResponse | None = None


classifier_pipeline_union = Union[
    keyword_match_schemas.KeywordMatchClassifierPipeline,
    manual_post_authors_schemas.ManualPostAuthorsClassifierPipeline,
    perspective_api_schemas.PerspectiveAPIClassifierPipeline,
    hugging_face_schemas.HuggingFaceClassifierPipeline,
]

ClassifierPipeline = Annotated[
    classifier_pipeline_union,
    pydantic.Field(description="Any classifier response", discriminator="type"),
]

classifier_pipeline_adapter: pydantic.TypeAdapter[classifier_pipeline_union] = (
    pydantic.TypeAdapter(ClassifierPipeline)
)
