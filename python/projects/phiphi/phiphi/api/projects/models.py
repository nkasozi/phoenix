"""Project Models."""

import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, orm

from phiphi import platform_db
from phiphi.api import base_models


class ProjectBase(platform_db.Base):
    """Project Model."""

    __abstract__ = True

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    name: orm.Mapped[str]
    description: orm.Mapped[str]
    workspace_slug: orm.Mapped[str] = orm.mapped_column(
        ForeignKey("workspaces.slug"), default="main"
    )
    pi_deleted_after_days: orm.Mapped[int]
    delete_after_days: orm.Mapped[int]
    expected_usage: orm.Mapped[Optional[str]]
    deleted_at: orm.Mapped[Optional[datetime.datetime]]
    dashboard_id: orm.Mapped[Optional[int]]
    has_unlimited_credits: orm.Mapped[bool] = orm.mapped_column(default=False)
    # Needs to be optional or problems with the database and we thought that this was better then
    # using a server_default=sa.sql.expression.false() in the migration.
    checked_problem_statement: orm.Mapped[Optional[bool]] = orm.mapped_column(default=False)
    checked_sources: orm.Mapped[Optional[bool]] = orm.mapped_column(default=False)
    checked_gather: orm.Mapped[Optional[bool]] = orm.mapped_column(default=False)
    checked_classify: orm.Mapped[Optional[bool]] = orm.mapped_column(default=False)
    checked_visualise: orm.Mapped[Optional[bool]] = orm.mapped_column(default=False)
    checked_explore: orm.Mapped[Optional[bool]] = orm.mapped_column(default=False)
    project_resources_provisioned_at: orm.Mapped[Optional[datetime.datetime]]
    superset_view_role_id: orm.Mapped[Optional[int]]
    superset_edit_role_id: orm.Mapped[Optional[int]]


class Project(ProjectBase, base_models.TimestampModel):
    """Project model that can inherit from multiple models."""

    __tablename__ = "projects"
    __table_args__ = (
        # Requests with `WHERE project_id and deleted_at is not null` will also use this index.
        Index("idx_project_id_deteted_at", "id", "deleted_at"),
        Index(
            "idx_deleted_at",
            "deleted_at",
        ),
    )

    # Relationship to get all related JobRuns for project, ordered by id descending
    job_runs = orm.relationship(
        "JobRuns",
        order_by="desc(JobRuns.id)",
        primaryjoin="Project.id == foreign(JobRuns.project_id)",
        lazy="select",
    )

    credit_allocations = orm.relationship(
        "CreditAllocations",
        order_by="desc(CreditAllocations.id)",
        primaryjoin="Project.id == foreign(CreditAllocations.project_id)",
        lazy="select",
    )
