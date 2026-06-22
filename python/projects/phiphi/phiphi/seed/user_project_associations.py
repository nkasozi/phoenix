"""Seed the user project associations."""

from sqlalchemy.orm import Session

from phiphi.api.projects import user_project_associations


def seed_test_user_project_associations(session: Session) -> None:
    """Seed the user project associations."""
    user_project_associations.create_user_project_association(
        session=session,
        project_id=1,
        # This is TEST_USER_1_CREATE
        user_id=2,
        user_project_association=user_project_associations.UserProjectAssociationCreate(
            role=user_project_associations.Role.user
        ),
    )

    # Add to delete project
    user_project_associations.create_user_project_association(
        session=session,
        project_id=4,
        user_id=2,
        user_project_association=user_project_associations.UserProjectAssociationCreate(
            role=user_project_associations.Role.user
        ),
    )
