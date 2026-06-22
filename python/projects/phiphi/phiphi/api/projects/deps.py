"""Dependencies for routes for the project."""

from enum import Enum
from typing import Annotated, Callable

import fastapi

from phiphi.api import deps, exceptions
from phiphi.api.projects import crud, schemas, user_project_associations


class AccessLevel(str, Enum):
    """Access levels for project authorization."""

    VIEW = "view"  # Can view project details
    USE = "use"  # Can use project resources
    # Will add different level roles as needed


# Mapping of access levels to required roles
ACCESS_LEVEL_ROLES: dict[AccessLevel, list[user_project_associations.Role]] = {
    AccessLevel.VIEW: [user_project_associations.Role.user],
    AccessLevel.USE: [user_project_associations.Role.user],
    # Will add different level roles as needed
}


def get_project_access_dependency(access_level: AccessLevel) -> Callable:
    """Create a dependency that checks if a user has the specified access level for a project.

    This function returns a FastAPI dependency function that can be used to check
    if the current user has the required access level for a specific project.

    Args:
        access_level: The required access level

    Returns:
        A FastAPI dependency function
    """

    async def authorize_project_access(
        project_id: int,
        session: deps.SessionDep,
        user: deps.CurrentUser,
    ) -> schemas.ProjectResponse:
        """Check if the current user has the required access level for the specified project.

        Args:
            project_id: The ID of the project to check access for
            session: Database session dependency
            user: Current user dependency

        Returns:
            The project if access is granted

        Raises:
            HTTPException: If access is denied
        """
        # Get the project
        project = crud.get_project(session, project_id)
        if project is None:
            raise exceptions.ProjectNotFound()

        # If user is admin, grant access immediately
        if user.is_admin():
            return project

        # Get the required roles for the access level
        required_roles = ACCESS_LEVEL_ROLES[access_level]

        # If there are no required roles for non-admins, only admins can access
        if not required_roles:
            raise exceptions.Forbidden("You don't have access to this project")

        # Check if the user has any of the required roles
        association = (
            session.query(user_project_associations.UserProjectAssociations)
            .filter(
                user_project_associations.UserProjectAssociations.project_id == project_id,
                user_project_associations.UserProjectAssociations.user_id == user.id,
                user_project_associations.UserProjectAssociations.role.in_(required_roles),
            )
            .first()
        )

        if association is None:
            # User doesn't have the required role
            raise exceptions.Forbidden("You don't have the required access to this project")

        return project

    return authorize_project_access


# Create factory functions for the dependencies
ProjectViewAccessDep = Annotated[
    schemas.ProjectResponse, fastapi.Depends(get_project_access_dependency(AccessLevel.VIEW))
]


def get_project_use_access_with_provisioned_check(
    project: Annotated[
        schemas.ProjectResponse, fastapi.Depends(get_project_access_dependency(AccessLevel.USE))
    ],
) -> schemas.ProjectResponse:
    """Check USE access and ensure project resources are provisioned.

    Uses sub-dependency to first check access, then validates resources are provisioned.
    """
    crud.assert_project_resources_provisioned(project)
    return project


ProjectUseAccessDep = Annotated[
    schemas.ProjectResponse, fastapi.Depends(get_project_use_access_with_provisioned_check)
]
