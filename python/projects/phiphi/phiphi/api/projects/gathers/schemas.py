"""Schemas for gathers."""

import datetime
from enum import Enum
from typing import Annotated, Any, Dict

import pydantic

from phiphi.api.projects.job_runs import schemas as job_runs_schemas


class ChildTypeName(str, Enum):
    """Child Type Enum.

    Additions to this enum should be reflected in the CHILD_TYPES_MAP in child_types.py file.
    """

    apify_facebook_posts = "apify_facebook_posts"
    apify_facebook_search_posts = "apify_facebook_search_posts"
    apify_facebook_comments = "apify_facebook_comments"
    apify_tiktok_hashtags_posts = "apify_tiktok_hashtags_posts"
    apify_tiktok_accounts_posts = "apify_tiktok_accounts_posts"
    apify_tiktok_searches_posts = "apify_tiktok_searches_posts"
    apify_tiktok_comments = "apify_tiktok_comments"
    apify_x_advanced_searches_posts_comments = "apify_x_advanced_searches_posts_comments"
    apify_x_simple_searches_posts_comments = "apify_x_simple_searches_posts_comments"
    danek_facebook_searches_posts = "danek_facebook_searches_posts"
    danek_instagram_posts = "danek_instagram_posts"
    danek_instagram_comments = "danek_instagram_comments"
    manual_upload = "manual_upload"


class Platform(str, Enum):
    """Platform enum."""

    facebook = "facebook"
    tiktok = "tiktok"
    x = "x"
    telegram = "telegram"
    instagram = "instagram"
    media_articles = "media articles"
    youtube = "youtube"


class DataType(str, Enum):
    """data type enum."""

    posts = "posts"
    comments = "comments"


class GatherBase(pydantic.BaseModel):
    """Gather base schema.

    Shared properties of all gathers.
    """

    name: Annotated[str, pydantic.Field(description="The name of the gather")]


class GatherResponse(GatherBase):
    """Gather schema.

    Properties to return to client.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    project_id: int
    latest_job_run: job_runs_schemas.JobRunResponse | None = None
    delete_job_run: job_runs_schemas.JobRunResponse | None = None
    child_type: Annotated[
        ChildTypeName, pydantic.Field(description="The child type of the gather")
    ]


class GatherChildResponseBase(GatherResponse):
    """Gather child response base schema.

    This includes shared functionality and properties for the child gathers.

    It should be considered an abstract class and not be used directly.
    """

    def serialize_to_apify_input(self) -> Dict[str, Any]:
        """Serialize the instance to a dictionary suitable for Apify API."""
        # Collect base fields and computed fields from the parent class
        # To be filtered out from the serialization so that the child attributes are left.
        base_fields = set(GatherChildResponseBase.model_fields.keys()) | set(
            GatherChildResponseBase.model_computed_fields.keys()
        )
        # We exclude Nones because Apify's Optional fields often have to be omitted, rather then
        # set to None.
        instance_dict = self.model_dump(by_alias=True, exclude_unset=True, exclude_none=True)
        apify_dict = {key: value for key, value in instance_dict.items() if key not in base_fields}
        return apify_dict

    # Both the property and computed_field decorators are used other wise mypy thinks that the
    # property is a function
    # Mypy doesn't allow both property and computed_field decorators, hence the ignore
    @pydantic.computed_field  # type: ignore[prop-decorator]
    @property
    def job_run_resource_estimate(self) -> job_runs_schemas.JobRunResourceEstimate:
        """Compute the job run resource estimate."""
        raise NotImplementedError("This method should be implemented in the child class.")


class GatherCreate(GatherBase):
    """Gather create schema.

    Properties to receive via API on creation.
    """


class GatherUpdate(pydantic.BaseModel):
    """Gather update schema."""

    name: Annotated[str | None, pydantic.Field(default=None, description="The name of the gather")]

    class Config:
        """Config."""

        # Don't allow extra fields on the update so that if a user tries to update a field that is
        # not allowed they are given an error.
        extra = pydantic.Extra.forbid
