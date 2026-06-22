"""Schemas for the users."""

import datetime
from enum import Enum

import pydantic


class AppRole(str, Enum):
    """App role enum."""

    admin = "admin"
    user = "user"


class UserBase(pydantic.BaseModel):
    """User base schema.

    Shared properties of all users.
    """

    email: pydantic.EmailStr | None = None
    display_name: str | None = None
    app_role: AppRole | None = AppRole.user


class UserCreate(UserBase):
    """User create schema.

    Properties to receive via API on creation.
    """

    email: pydantic.EmailStr
    display_name: str


class UserResponse(UserBase):
    """User schema.

    Properties to return to client.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    created_at: datetime.datetime

    def is_admin(self) -> bool:
        """Check if the user is an admin."""
        return self.app_role == AppRole.admin


class UserUpdate(pydantic.BaseModel):
    """User update schema."""

    display_name: str | None = None


class UserAdminUpdate(UserUpdate):
    """User admin update schema."""

    app_role: AppRole | None = None
