"""Base Schemas for classifiers."""

import datetime
from enum import Enum
from typing import Annotated, Any, Optional

import pydantic

from phiphi.api.projects.job_runs import schemas as job_runs_schemas


class ClassifierType(str, Enum):
    """Classifier type enum."""

    keyword_match = "keyword_match"
    manual_post_authors = "manual_post_authors"
    perspective_api = "perspective_api"
    hugging_face = "hugging_face"


# There are classifier types that should not be re run on every gather.
SINGLE_RUN_CLASSIFIER_TYPES = [ClassifierType.manual_post_authors]


class IntermediatoryClassBase(pydantic.BaseModel):
    """Class schema."""

    name: str
    description: str


class IntermediatoryClassCreate(IntermediatoryClassBase):
    """Class create schema."""


class IntermediatoryClassPatch(pydantic.BaseModel):
    """Class Patch schema."""

    name: Annotated[
        Optional[str], pydantic.Field(description="The name of the Classifier", default=None)
    ]
    description: Annotated[
        Optional[str],
        pydantic.Field(description="The description of the Classifier", default=None),
    ]


class IntermediatoryClassResponse(IntermediatoryClassBase):
    """Class response schema."""

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ClassLabel(pydantic.BaseModel):
    """Class label schema.

    This was called ClassLabel as opposed to Class to avoid confusion with the Python class.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    name: str
    description: str


class ClassifierCreate(pydantic.BaseModel):
    """Classifier create schema.

    Properties to receive via API on creation.

    No version of the classifier is created at this point, only the classifier itself.
    """

    name: Annotated[str, pydantic.Field(description="The name of the Classifier")]
    description: Annotated[str, pydantic.Field(description="The description of the Classifier")]


class ClassifierSimpleVersionBase(pydantic.BaseModel):
    """Simple Classifier version base schema.

    This is used for classifiers that do not have a complex versioning system.
    """

    classes: list[ClassLabel] = pydantic.Field(
        default_factory=list, description="The classes of the Classifier"
    )
    params: Annotated[Any, pydantic.Field(description="The params of the Classifier")]


class ClassifierCreateWithVersion(ClassifierCreate):
    """Classifier with version create schema.

    This includes the latest version of the Classifier.
    """

    latest_version: Annotated[
        ClassifierSimpleVersionBase,
        pydantic.Field(description="The latest version of the Classifier"),
    ]


class ClassifierWithIntermediatoryCreate(ClassifierCreate):
    """Classifier with intermediatory classes create schema.

    This includes the intermediatory classes. That will be stored in `intermediatory_classes`
    table.
    """

    intermediatory_classes: list[IntermediatoryClassCreate]


class ClassifierPatch(pydantic.BaseModel):
    """Classifier patch schema.

    Properties to receive via API on update.
    """

    name: Annotated[
        Optional[str], pydantic.Field(description="The name of the Classifier", default=None)
    ]
    description: Annotated[
        Optional[str],
        pydantic.Field(description="The description of the Classifier", default=None),
    ]


class ClassifierVersionResponse(pydantic.BaseModel):
    """Classifier version schema.

    Properties to return to client.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    # Although this is duplicated in the ClassifierResponseBase, it is good to have here for
    # testing versions and the response from the create of a version
    classifier_id: int
    version_id: Annotated[
        int, pydantic.Field(description="The ID of this version (of the corresponding Classifier)")
    ]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    classes: list[ClassLabel]
    # Typed as Any as the subclasses will define the params
    params: Annotated[Any, pydantic.Field(description="The params of the Classifier")]


class ClassifierResponseBase(pydantic.BaseModel):
    """Classifier schema.

    Base properties for the Classifier.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    description: str
    type: ClassifierType
    # It is possible to have a classifier without any versions
    # This then uses the intermediatory tables to store data about the version
    latest_version: Annotated[
        Optional[ClassifierVersionResponse],
        pydantic.Field(description="The latest version of the Classifier", default=None),
    ]


class ClassifierDetailBase(ClassifierResponseBase):
    """Classifier detail schema.

    Detailed version of the classifier used for viewing and editing.
    """

    archived_at: Optional[datetime.datetime]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    last_edited_at: Optional[datetime.datetime]
    intermediatory_classes: list[IntermediatoryClassResponse]
    latest_job_run: job_runs_schemas.JobRunResponse | None = None


class ClassifierPipelineBase(ClassifierResponseBase):
    """Classifier Pipeline.

    Pipeline classifiers always have a version.
    """

    latest_version: Annotated[
        ClassifierVersionResponse,
        pydantic.Field(description="The latest version of the Classifier"),
    ]
