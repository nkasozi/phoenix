"""Seed the projects."""

from sqlalchemy.orm import Session

from phiphi.api.projects import crud, schemas

TEST_PROJECT_CREATE = schemas.ProjectCreate(
    name="Phoenix Project 1",
    description="Project 1, with allocated credits and not unlimited.",
    workspace_slug="main",
    pi_deleted_after_days=90,
    delete_after_days=20,
    expected_usage=schemas.ExpectedUsage.weekly,
    has_unlimited_credits=False,
)

TEST_PROJECT_CREATE_2 = schemas.ProjectCreate(
    name="Phoenix Project 2",
    description="Project 2, with no allocated credits but has unlimited credits.",
    workspace_slug="main",
    pi_deleted_after_days=90,
    delete_after_days=20,
    expected_usage=schemas.ExpectedUsage.monthly,
    has_unlimited_credits=True,
)

TEST_PROJECT_CREATE_3 = schemas.ProjectCreate(
    name="Phoenix Project 3",
    description="Project 3 has a total cost equal to the allocated credits",
    workspace_slug="test",
    pi_deleted_after_days=90,
    delete_after_days=20,
    expected_usage=schemas.ExpectedUsage.weekly,
    has_unlimited_credits=False,
)

TEST_PROJECT_CREATE_4_DELETED = schemas.ProjectCreate(
    name="Phoenix Project 4",
    description="Project 4",
    workspace_slug="test",
    pi_deleted_after_days=90,
    delete_after_days=20,
    expected_usage=schemas.ExpectedUsage.weekly,
    has_unlimited_credits=False,
)

TEST_PROJECT_CREATE_5 = schemas.ProjectCreate(
    name="Phoenix Project 5",
    description="Project 5 has no allocated credits and no unlimited credits",
    workspace_slug="test",
    pi_deleted_after_days=90,
    delete_after_days=20,
    expected_usage=schemas.ExpectedUsage.weekly,
    has_unlimited_credits=False,
)


TEST_PROJECT_CREATE_6 = schemas.ProjectCreate(
    name="Phoenix Project 6",
    description="Project 6 estimated total costs and allocated credits",
    workspace_slug="test",
    pi_deleted_after_days=90,
    delete_after_days=20,
    expected_usage=schemas.ExpectedUsage.weekly,
    has_unlimited_credits=False,
)

TEST_PROJECT_CREATE_7_NOT_PROVISIONED = schemas.ProjectCreate(
    name="Phoenix Project 7",
    description="Project 7 has no project_resources_provisioned_at",
    workspace_slug="main",
    pi_deleted_after_days=90,
    delete_after_days=20,
    expected_usage=schemas.ExpectedUsage.weekly,
    has_unlimited_credits=False,
)


SEEDED_PROJECTS: list[schemas.ProjectResponse] = []


def seed_test_project(session: Session) -> None:
    """Seed the project."""
    SEEDED_PROJECTS.clear()
    projects_to_provision = [
        TEST_PROJECT_CREATE,
        TEST_PROJECT_CREATE_2,
        TEST_PROJECT_CREATE_3,
        TEST_PROJECT_CREATE_4_DELETED,
        TEST_PROJECT_CREATE_5,
        TEST_PROJECT_CREATE_6,
    ]

    for project in projects_to_provision:
        created_project = crud.create_project(session=session, user_id=1, project=project)
        crud.set_project_resources_provisioned(
            session=session, project_id=created_project.id, dashboard_id=None
        )
        SEEDED_PROJECTS.append(created_project)

    # Create project without provisioning resources
    not_provisioned_project = crud.create_project(
        session=session, user_id=1, project=TEST_PROJECT_CREATE_7_NOT_PROVISIONED
    )
    SEEDED_PROJECTS.append(not_provisioned_project)

    crud.delete_project(session=session, project_id=4)
