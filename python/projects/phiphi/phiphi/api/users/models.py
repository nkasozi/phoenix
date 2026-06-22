"""User Models."""

from typing import Optional

from sqlalchemy import orm

from phiphi import platform_db
from phiphi.api import base_models


class UserBase(platform_db.Base):
    """User model."""

    __abstract__ = True

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    email: orm.Mapped[str] = orm.mapped_column(index=True, unique=True)
    display_name: orm.Mapped[Optional[str]]
    # This must be set
    app_role: orm.Mapped[str]


class User(UserBase, base_models.TimestampModel):
    """User model that can inherit from multiple models."""

    __tablename__ = "users"
