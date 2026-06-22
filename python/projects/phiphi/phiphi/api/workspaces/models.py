"""Workspace Models."""

from phiphi import platform_db
from phiphi.api import base_models
from sqlalchemy import orm


class WorkspaceBase(platform_db.Base):
    """Workspace Model."""

    __abstract__ = True

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    name: orm.Mapped[str]
    description: orm.Mapped[str]
    slug: orm.Mapped[str] = orm.mapped_column(index=True, unique=True)


class Workspace(WorkspaceBase, base_models.TimestampModel):
    """Workspace model that can inherit from multiple models."""

    __tablename__ = "workspaces"
