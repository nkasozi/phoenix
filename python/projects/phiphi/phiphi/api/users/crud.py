"""User crud functionality."""

import sqlalchemy.orm

from phiphi.api import exceptions
from phiphi.api.users import models, schemas


def create_user(session: sqlalchemy.orm.Session, user: schemas.UserCreate) -> schemas.UserResponse:
    """Create a new user."""
    if get_user_by_email(session, user.email):
        raise exceptions.HttpException400(detail="User already exists")

    orm_user = models.User(**user.dict())
    session.add(orm_user)
    session.commit()
    session.refresh(orm_user)
    return schemas.UserResponse.model_validate(orm_user)


def read_user(session: sqlalchemy.orm.Session, user_id: int) -> schemas.UserResponse | None:
    """Read a user."""
    orm_user = session.get(models.User, user_id)
    if orm_user is None:
        return None
    return schemas.UserResponse.model_validate(orm_user)


def read_users(
    session: sqlalchemy.orm.Session, start: int = 0, end: int = 100
) -> list[schemas.UserResponse]:
    """Retrieve users."""
    query = sqlalchemy.select(models.User).offset(start).limit(end)
    users = session.scalars(query).all()
    if not users:
        return []
    return [schemas.UserResponse.model_validate(user) for user in users]


def get_user_by_email(session: sqlalchemy.orm.Session, email: str) -> schemas.UserResponse | None:
    """Retrieve a user by email."""
    orm_user = session.query(models.User).filter(models.User.email == email).first()
    if orm_user is None:
        return None
    return schemas.UserResponse.model_validate(orm_user)


def update_user(
    session: sqlalchemy.orm.Session, user_id: int, user: schemas.UserUpdate
) -> schemas.UserResponse | None:
    """Update a user."""
    orm_user = session.get(models.User, user_id)
    if orm_user is None:
        return None
    for field, value in user.dict(exclude_unset=True).items():
        setattr(orm_user, field, value)
    session.commit()
    session.refresh(orm_user)
    return schemas.UserResponse.model_validate(orm_user)
