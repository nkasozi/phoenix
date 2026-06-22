"""Seed the users."""

from sqlalchemy.orm import Session

from phiphi import config
from phiphi.api.users import crud, schemas

# Quick way of allowing tests to check this user.
# If more objects are added like this it Might be a good idea to refactor this so that all seeded
# objects are added to a registry that seed.main returns.
TEST_USER_1_CREATE = schemas.UserCreate(email="test1@phiphi.com", display_name="Test User 1")


def seed_test_users(session: Session) -> None:
    """Seed the users."""
    users = [
        TEST_USER_1_CREATE,
        schemas.UserCreate(email="test2@phiphi.com", display_name="Test User 2"),
    ]
    for user in users:
        crud.create_user(session=session, user=user)


def init_first_admin_user(session: Session) -> schemas.UserResponse:
    """Create the first admin."""
    user = crud.read_user(session, 1)
    if not user:
        user_in = schemas.UserCreate(
            email=config.settings.FIRST_ADMIN_USER_EMAIL,
            display_name=config.settings.FIRST_ADMIN_USER_DISPLAY_NAME,
            app_role=schemas.AppRole.admin,
        )
        user = crud.create_user(session=session, user=user_in)
    return user
