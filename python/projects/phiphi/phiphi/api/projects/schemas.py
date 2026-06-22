"""Schemas for the projects."""

import datetime
from enum import Enum
from typing import Annotated

import pydantic
from typing_extensions import Self

from phiphi.api.projects.job_runs import schemas as job_runs_schemas


class ExpectedUsage(str, Enum):
    """Expected usage enum."""

    one_off = "one_off"
    weekly = "weekly"
    monthly = "monthly"
    daily = "daily"


pi_delete_pydantic_field = pydantic.Field(
    default=183, description="PI deletion time in days, min 1, max 365", ge=1, le=365
)
delete_after_days_field = pydantic.Field(
    default=183, description="Deletion time in days, min 1, max 365", ge=1, le=365
)
workspace_slug_field = pydantic.Field(
    default="main", description="The workspace slug of the project"
)


class ProjectBase(pydantic.BaseModel):
    """Project base schema.

    Shared properties of all projects.
    """

    name: Annotated[str, pydantic.Field(description="The name of the project")]
    description: Annotated[str, pydantic.Field(description="The description of the project")]
    workspace_slug: Annotated[str, workspace_slug_field]

    pi_deleted_after_days: Annotated[int, pi_delete_pydantic_field]
    delete_after_days: Annotated[int, delete_after_days_field]
    expected_usage: Annotated[
        ExpectedUsage, pydantic.Field(description="The workspace expected usage of the project")
    ]
    dashboard_id: Annotated[
        int | None, pydantic.Field(description="The dashboard id of the project")
    ] = None
    has_unlimited_credits: Annotated[
        bool,
        pydantic.Field(
            description=(
                "Whether the project has unlimited credits overriding the allocated credits. "
                "Defaults to False."
            ),
            default=False,
        ),
    ]


class ProjectCreate(ProjectBase):
    """Project create schema.

    Properties to receive via API on creation.
    """

    initial_credit_allocation_amount: Annotated[
        float | None,
        pydantic.Field(description="The initial credit allocation amount", default=None),
    ] = None
    initial_credit_allocation_description: Annotated[
        str | None,
        pydantic.Field(
            description=(
                "The initial credit allocation description. "
                "This is required if initial_credit_allocation_amount is set."
            ),
            default=None,
        ),
    ] = None

    @pydantic.model_validator(mode="after")
    def check_init_credit_allocation_description(self) -> Self:
        """Check if initial credit allocation description is provided when amount is provided."""
        amount = self.initial_credit_allocation_amount
        description = self.initial_credit_allocation_description
        if amount is not None and description is None:
            raise ValueError(
                "Initial credit allocation description is required when amount is provided."
            )
        return self


class ProjectResponse(ProjectBase):
    """Project schema.

    Contains only the information from the project table. It has a light SQL footprint and should
    be used as the main Project schema.

    Properties to return to client.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    checked_problem_statement: bool = False
    checked_sources: bool = False
    checked_gather: bool = False
    checked_classify: bool = False
    checked_visualise: bool = False
    checked_explore: bool = False
    project_resources_provisioned_at: datetime.datetime | None = None
    superset_view_role_id: int | None = None
    superset_edit_role_id: int | None = None


class ProjectDetail(ProjectResponse):
    """Project Detailed schema.

    There are a number of fields that are more expensive to calculate and are not needed in the
    list view or create view.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    last_job_run_completed_at: datetime.datetime | None
    latest_job_run: job_runs_schemas.JobRunResponse | None = None
    total_costs: float
    total_allocated_credits: Annotated[
        float,
        pydantic.Field(description="The total allocated credits of the project"),
    ]
    estimated_total_costs: Annotated[
        float,
        pydantic.Field(description="The estimated total costs of the project"),
    ]


class ProjectListResponse(ProjectBase):
    """Project List schema.

    Properties to return to client.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    project_resources_provisioned_at: datetime.datetime | None = None


class ProjectUpdate(pydantic.BaseModel):
    """Project update schema."""

    name: str | None = None
    description: str | None = None
    pi_deleted_after_days: Annotated[int | None, pi_delete_pydantic_field]
    delete_after_days: Annotated[int | None, delete_after_days_field]
    expected_usage: ExpectedUsage | None = None
    workspace_slug: Annotated[str | None, workspace_slug_field]
    dashboard_id: int | None = None
    checked_problem_statement: bool = False
    checked_sources: bool = False
    checked_gather: bool = False
    checked_classify: bool = False
    checked_visualise: bool = False
    checked_explore: bool = False
    has_unlimited_credits: Annotated[
        bool | None,
        pydantic.Field(
            description=(
                "Whether the project has unlimited credits overriding the allocated credits."
            )
        ),
    ] = None
    project_resources_provisioned_at: datetime.datetime | None = None
    superset_view_role_id: int | None = None
    superset_edit_role_id: int | None = None


class ProjectChecklistUpdate(pydantic.BaseModel):
    """Project checklist update schema."""

    checked_problem_statement: bool | None = None
    checked_sources: bool | None = None
    checked_gather: bool | None = None
    checked_classify: bool | None = None
    checked_visualise: bool | None = None
    checked_explore: bool | None = None
