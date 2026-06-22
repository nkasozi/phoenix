"""Schemas for the workspaces."""

import datetime
from typing import Annotated

import pydantic


class WorkspaceBase(pydantic.BaseModel):
    """Workspace base schema.

    Shared properties of all workspace schemas.
    """

    description: Annotated[str, pydantic.Field(description="The description of the Workspace")]
    name: Annotated[str, pydantic.Field(description="The name of the Workspace")]
    slug: Annotated[str, pydantic.Field(description="The slug of the Workspace")]


class WorkspaceCreate(WorkspaceBase):
    """Workspace create schema.

    Properties to receive via API on creation.
    """


class WorkspaceResponse(WorkspaceBase):
    """Workspace schema.

    Properties to return to client.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    slug: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class WorkspaceUpdate(pydantic.BaseModel):
    """Workspace update schema."""

    name: str | None = None
    description: str | None = None
    slug: str | None = None


class SlugResponse(pydantic.BaseModel):
    """Workspace unique slug."""

    slug: str
