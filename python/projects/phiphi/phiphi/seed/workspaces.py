"""Seed the workspaces."""

from sqlalchemy.orm import Session

from phiphi import config
from phiphi.api.workspaces import crud, schemas

TEST_WORKSPACE_CREATE = schemas.WorkspaceCreate(
    name="Phoenix", description="Workspace 1", slug="phoenix"
)

TEST_WORKSPACE_CREATE_2 = schemas.WorkspaceCreate(
    name="Test", description="Testing seed", slug="test"
)


def seed_test_workspace(session: Session) -> None:
    """Seed the workspace."""
    workspaces = [TEST_WORKSPACE_CREATE, TEST_WORKSPACE_CREATE_2]

    for workspace in workspaces:
        crud.create_workspace(session=session, workspace=workspace)


def init_main_workspace(session: Session) -> schemas.WorkspaceResponse:
    """Create the first workspace."""
    workspace = crud.get_workspace(session, "main")
    if not workspace:
        workspace_in = schemas.WorkspaceCreate(
            name=config.settings.FIRST_WORKSPACE_NAME,
            description=config.settings.FIRST_WORKSPACE_DESCRIPTION,
            slug=config.settings.FIRST_WORKSPACE_SLUG,
        )
        workspace = crud.create_workspace(session=session, workspace=workspace_in)
    return workspace
