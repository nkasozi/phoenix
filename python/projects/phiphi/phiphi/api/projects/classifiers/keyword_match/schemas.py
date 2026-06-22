"""Keyword Match Schemas."""

import datetime
from enum import Enum
from typing import Annotated, Literal, NotRequired, Optional

import pydantic
import re2
from typing_extensions import Self, TypedDict

from phiphi.api.projects.classifiers import base_schemas


def validate_re2_regex(pattern: str) -> None:
    """Validate that a regex pattern is compatible with RE2.

    Uses google-re2 to compile the pattern, which ensures exact compatibility
    with BigQuery's regex engine.
    """
    try:
        re2.compile(pattern)
    except re2.error as e:
        raise ValueError(
            f"Invalid RE2 regex: {e}. See https://github.com/google/re2/wiki/Syntax"
        ) from e


class ImportMode(Enum):
    """Import mode for CSV import."""

    replace = "replace"
    append = "append"


class KeywordConfigCSVRow(pydantic.BaseModel):
    """Validated row from a keyword config CSV."""

    class_name: str
    class_description: str
    musts: str = ""
    nots: str = ""
    is_regex: bool = False

    @pydantic.field_validator("class_name")
    @classmethod
    def class_name_not_empty(cls, v: str) -> str:
        """Validate that class_name is not empty."""
        if not v.strip():
            raise ValueError("class_name must not be empty.")
        return v.strip()

    @pydantic.field_validator("class_description")
    @classmethod
    def class_description_strip(cls, v: str) -> str:
        """Strip whitespace from class_description."""
        return v.strip()

    @pydantic.model_validator(mode="after")
    def validate_regex_syntax(self) -> Self:
        """Validate that musts and nots are valid RE2 regexes when is_regex is True."""
        if self.is_regex:
            if self.musts:
                validate_re2_regex(self.musts)
            if self.nots:
                validate_re2_regex(self.nots)
        return self


MUSTS_DESCRIPTION = (
    "Whitespace separated list of keywords that must all match to classify as this class"
)
NOTS_DESCRIPTION = (
    "Whitespace separated list of keywords; "
    "to be classified into this class, it must not contain any of the words"
)


class IntermediatoryClassToKeywordConfigCreate(pydantic.BaseModel):
    """Intermediatory class to keyword config create schema."""

    class_id: int
    musts: Annotated[str, pydantic.Field(description=MUSTS_DESCRIPTION)]
    nots: Annotated[Optional[str], pydantic.Field(description=NOTS_DESCRIPTION)] = ""
    is_regex: Annotated[
        bool,
        pydantic.Field(
            description="When True, musts and nots are treated as raw RE2 regexes "
            "without escaping or tokenization.",
        ),
    ] = False

    @pydantic.model_validator(mode="after")
    def check_musts_and_nots(self) -> Self:
        """Check that at least one of 'musts' or 'nots' is a non-empty string."""
        if not self.musts and not self.nots:
            raise ValueError("At least one of 'musts' or 'nots' must be a non-empty string.")
        return self

    @pydantic.model_validator(mode="after")
    def validate_regex_syntax(self) -> Self:
        """Validate that musts and nots are valid RE2 regexes when is_regex is True."""
        if self.is_regex:
            if self.musts:
                validate_re2_regex(self.musts)
            if self.nots:
                validate_re2_regex(self.nots)
        return self


class IntermediatoryClassToKeywordConfigResponse(IntermediatoryClassToKeywordConfigCreate):
    """Intermediatory class to keyword config response schema."""

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    class_name: str
    # Class description is added as this makes the UI for the console to compute easier
    class_description: str


class ClassToKeywordConfig(TypedDict):
    """Class to keyword config containing keyword matches.

    This is a TypedDict rather then a pydantic models as fast api recommends using TypedDict for
    nested objects to improve performance.
    https://docs.pydantic.dev/latest/concepts/performance/#use-typeddict-over-nested-models
    """

    class_name: str
    musts: Annotated[
        str,
        pydantic.Field(
            description=MUSTS_DESCRIPTION,
        ),
    ]
    nots: NotRequired[
        Annotated[Optional[str], pydantic.Field(description=NOTS_DESCRIPTION, default="")]
    ]
    is_regex: NotRequired[
        Annotated[
            bool,
            pydantic.Field(
                description="When True, musts and nots are treated as raw RE2 regexes "
                "without escaping or tokenization. Defaults to False.",
                default=False,
            ),
        ]
    ]


class KeywordMatchParams(TypedDict):
    """Params subschema for keyword match classifier.

    This is a TypedDict rather then a pydantic models as fast api recommends using TypedDict for
    nested objects to improve performance.
    https://docs.pydantic.dev/latest/concepts/performance/#use-typeddict-over-nested-models
    """

    class_to_keyword_configs: list[ClassToKeywordConfig]


class KeywordMatchVersionBase(pydantic.BaseModel):
    """Keyword match version base schema."""

    classes: list[base_schemas.ClassLabel]
    params: KeywordMatchParams


class KeywordMatchVersionResponse(KeywordMatchVersionBase, base_schemas.ClassifierVersionResponse):
    """Keyword match version schema."""


class KeywordMatchClassifierResponse(base_schemas.ClassifierResponseBase):
    """Keyword match classifier response."""

    # This seems to be the correct way to do this:
    # https://github.com/pydantic/pydantic/issues/8708
    type: Literal[base_schemas.ClassifierType.keyword_match]
    latest_version: Optional[KeywordMatchVersionResponse] = None


class KeywordMatchClassifierDetail(
    KeywordMatchClassifierResponse, base_schemas.ClassifierDetailBase
):
    """Keyword match classifier response."""

    intermediatory_class_to_keyword_configs: list[IntermediatoryClassToKeywordConfigResponse] = []


class KeywordMatchClassifierPipeline(
    KeywordMatchClassifierResponse, base_schemas.ClassifierPipelineBase
):
    """Keyword match classifier response."""

    latest_version: KeywordMatchVersionResponse
