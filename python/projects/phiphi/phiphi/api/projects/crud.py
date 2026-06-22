"""Project crud functionality."""

import datetime
import logging

import sqlalchemy.orm

from phiphi import config, utils
from phiphi.api import exceptions
from phiphi.api.projects import (
    credit_allocations,
    job_runs,
    models,
    schemas,
    user_project_associations,
)
from phiphi.api.workspaces import models as workspace_models
from phiphi.pipeline_jobs import project_resources, projects

utils.init_logging()

logger = logging.getLogger(__name__)


def create_orm_project_not_commited(
    session: sqlalchemy.orm.Session,
    user_id: int,
    project: schemas.ProjectCreate,
) -> models.Project:
    """Create a new project without commit.

    This is so it is possible to rollback the transaction if any error occurs in the caller of this
    function.
    """
    logger.info(f"Creating project {project.name} for user {user_id}")
    orm_workspace = (
        session.query(workspace_models.Workspace)
        .filter(workspace_models.Workspace.slug == project.workspace_slug)
        .first()
    )

    logger.debug(f"Found workspace: {orm_workspace}")
    if orm_workspace is None:
        raise exceptions.WorkspaceNotFound()

    try:
        project_base_fields = set(schemas.ProjectBase.model_fields.keys())
        project_data = project.dict(include=project_base_fields)
        orm_project = models.Project(**project_data)
        session.add(orm_project)
        logger.debug(f"ORM Project created: {orm_project}")
        # Get the id of the project without committing the transaction
        session.flush()
        if project.initial_credit_allocation_amount:
            logger.debug(f"Creating initial credit allocation for project {orm_project.id}")
            orm_credit_allocations = credit_allocations.CreditAllocations(
                user_id=user_id,
                project_id=orm_project.id,
                amount=project.initial_credit_allocation_amount,
                description=project.initial_credit_allocation_description,
            )
            session.add(orm_credit_allocations)

        session.refresh(orm_project)
        return orm_project
    except Exception as e:
        session.rollback()
        raise e


def create_project(
    session: sqlalchemy.orm.Session,
    user_id: int,
    project: schemas.ProjectCreate,
) -> schemas.ProjectResponse:
    """Create a new project.

    This function can be used to create a new project without external resources, such as for
    tests.
    """
    orm_project = create_orm_project_not_commited(session, user_id, project)
    session.commit()
    session.refresh(orm_project)
    return schemas.ProjectResponse.model_validate(orm_project)


async def create_project_with_external_resources(
    session: sqlalchemy.orm.Session,
    user_id: int,
    project: schemas.ProjectCreate,
) -> schemas.ProjectResponse:
    """Create a new project and trigger background resource provisioning.

    If PROVISION_PROJECT_RESOURCES_ON_PROJECT_CREATE is True, triggers a background
    Prefect deployment to provision BigQuery dataset and other resources. The project
    is returned immediately without waiting for provisioning to complete.

    If PROVISION_PROJECT_RESOURCES_ON_PROJECT_CREATE is False, the project is created
    without any external resources (useful for testing).

    The project is only committed to the database after the provisioning deployment
    is successfully triggered. If the deployment fails to start, the transaction
    is rolled back.

    Args:
        session: Database session.
        user_id: The ID of the user creating the project.
        project: The project creation schema.

    Returns:
        The created project response.
    """
    orm_project = create_orm_project_not_commited(session, user_id, project)
    # At this point we have project ID (from flush) but transaction is not committed

    # Trigger background provisioning if enabled
    if config.settings.PROVISION_PROJECT_RESOURCES_ON_PROJECT_CREATE:
        project_namespace = utils.get_project_namespace(orm_project.id)

        # Determine which resources to provision based on config
        provision_bigquery = not config.settings.USE_MOCK_BQ
        provision_rate_limits = config.settings.ADD_BIG_QUERY_RATE_LIMITS_ON_PROJECT_CREATION
        provision_superset = config.settings.SUPERSET_PROVISIONING_ENABLED

        logger.info(
            f"Triggering background provisioning for project {orm_project.id}: "
            f"bigquery={provision_bigquery}, rate_limits={provision_rate_limits}, "
            f"superset={provision_superset}"
        )

        try:
            await project_resources.start_provision_deployment(
                project_id=orm_project.id,
                project_name=orm_project.name,
                project_namespace=project_namespace,
                workspace_slug=orm_project.workspace_slug,
                with_dummy_data=True,
                provision_bigquery=provision_bigquery,
                provision_rate_limits=provision_rate_limits,
                provision_superset=provision_superset,
            )
            logger.info(f"Background provisioning triggered for project {orm_project.id}")
        except Exception as e:
            session.rollback()
            logger.error(
                f"Failed to trigger provisioning for project {orm_project.id}: {e}",
                exc_info=e,
            )
            raise e

    # Only commit after deployment is successfully triggered (or if provisioning disabled)
    session.commit()
    session.refresh(orm_project)
    logger.info(f"Project {orm_project.id} created successfully")
    return schemas.ProjectResponse.model_validate(orm_project)


def update_project(
    session: sqlalchemy.orm.Session, project_id: int, project: schemas.ProjectUpdate
) -> schemas.ProjectResponse | None:
    """Update an project."""
    orm_project = get_non_deleted_project_model(session, project_id)
    if orm_project is None:
        return None
    for field, value in project.dict(exclude_unset=True).items():
        setattr(orm_project, field, value)
    session.commit()
    session.refresh(orm_project)
    return schemas.ProjectResponse.model_validate(orm_project)


def update_project_checklist(
    session: sqlalchemy.orm.Session, project_id: int, checklist: schemas.ProjectChecklistUpdate
) -> schemas.ProjectResponse | None:
    """Update project checklist fields."""
    orm_project = get_non_deleted_project_model(session, project_id)
    if orm_project is None:
        return None
    for field, value in checklist.dict(exclude_unset=True).items():
        setattr(orm_project, field, value)
    session.commit()
    session.refresh(orm_project)
    return schemas.ProjectResponse.model_validate(orm_project)


def get_total_costs_and_esimated_total_costs(
    session: sqlalchemy.orm.Session, project_id: int
) -> tuple[float, float]:
    """Get total costs and estimated total costs for a project.

    The total costs are only for completed job runs.

    The estimated_total_costs is the total costs plus the estimated costs of incomplete job runs.
    """
    total_costs = job_runs.crud.get_total_costs_for_project(session, project_id)
    estimated_incomplete = job_runs.crud.get_estimated_incomplete_costs_for_project(
        session, project_id
    )
    return total_costs, total_costs + estimated_incomplete


def get_project(
    session: sqlalchemy.orm.Session, project_id: int
) -> schemas.ProjectResponse | None:
    """Get an project."""
    orm_project = get_non_deleted_project_model(session, project_id)
    if orm_project is None:
        return None
    return schemas.ProjectResponse.model_validate(orm_project)


def form_project_detail(
    session: sqlalchemy.orm.Session, project: schemas.ProjectResponse
) -> schemas.ProjectDetail:
    """Form project detail.

    Will get the extra data from the database and form the ProjectDetail.
    """
    project_id = project.id
    # Calculate total allocated credits from CreditAllocations
    total_allocated = credit_allocations.get_total_credit_allocation(session, project_id)

    # Calculate total costs from JobRuns
    total_costs, estimated_total = get_total_costs_and_esimated_total_costs(session, project_id)

    # Get latest_job_run
    latest_job_run = job_runs.crud.get_latest_job_run(session, project_id)

    # Get last_job_run_completed_at
    # If the latest_job_run is completed then use that, otherwise get the last completed job run
    last_job_run_completed_at: datetime.datetime | None = None
    if latest_job_run is not None and latest_job_run.completed_at is not None:
        last_job_run_completed_at = latest_job_run.completed_at
    else:
        last_job_run_completed_at = job_runs.crud.get_last_job_run_completed_at_for_project(
            session, project_id
        )

    # Convert ORM project to ProjectDetail schema with explicit totals
    project_data = project.model_dump()
    project_detail = schemas.ProjectDetail(
        **project_data,
        latest_job_run=latest_job_run,
        last_job_run_completed_at=last_job_run_completed_at,
        total_costs=total_costs,
        total_allocated_credits=total_allocated,
        estimated_total_costs=estimated_total,
    )
    return project_detail


def get_all_projects(
    session: sqlalchemy.orm.Session, end: int | None = None, start: int = 0, desc: bool = True
) -> list[schemas.ProjectListResponse]:
    """Get projects.

    Args:
        session: An active SQLAlchemy session.
        start: The starting index for pagination.
        end: The ending index for pagination.
        desc: Whether to order the projects by ID in descending order.

    Returns:
        A list of ProjectListResponse schemas, or an empty list if no projects found.
    """
    query = (
        sqlalchemy.select(models.Project).filter(models.Project.deleted_at.is_(None)).offset(start)
    )
    if end is not None:
        query = query.limit(end)
    if desc:
        query = query.order_by(models.Project.id.desc())
    else:
        query = query.order_by(models.Project.id.asc())
    projects = session.scalars(query).all()
    if not projects:
        return []
    return [schemas.ProjectListResponse.model_validate(project) for project in projects]


def get_all_active_project_ids(
    session: sqlalchemy.orm.Session, offset: int | None = None, limit: int | None = None
) -> list[int]:
    """Get project IDs.

    Queries only the `id` column for non-deleted projects,
    ordered by ID descending, and returns a list of IDs.

    Args:
        session: An active SQLAlchemy session.
        offset: The number of rows to skip before returning results.
        limit: The maximum number of rows to return.

    Returns:
        A list of project IDs, or an empty list if no projects found.
    """
    query = (
        sqlalchemy.select(models.Project.id)
        .filter(models.Project.deleted_at.is_(None))
        .order_by(models.Project.id.desc())
    )
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    project_ids = session.scalars(query).all()
    return list(project_ids)


def get_user_projects(
    session: sqlalchemy.orm.Session, user_id: int, end: int | None = None, start: int = 0
) -> list[schemas.ProjectListResponse]:
    """Get projects for a user."""
    # To be implemented
    query = (
        session.query(models.Project)
        .join(user_project_associations.UserProjectAssociations)
        .filter(models.Project.deleted_at.is_(None))
        .filter(user_project_associations.UserProjectAssociations.user_id == user_id)
        .order_by(models.Project.id.desc())
        .offset(start)
    )
    if end is not None:
        query = query.limit(end)
    projects = query.all()
    if not projects:
        return []
    return [schemas.ProjectListResponse.model_validate(project) for project in projects]


def get_orm_project_with_guard(session: sqlalchemy.orm.Session, project_id: int) -> None:
    """Guard for null instnaces."""
    orm_project = get_non_deleted_project_model(session, project_id)
    if orm_project is None:
        raise exceptions.ProjectNotFound()


def set_project_resources_provisioned(
    session: sqlalchemy.orm.Session,
    project_id: int,
    dashboard_id: int | None = None,
    provisioned_at: datetime.datetime | None = None,
    superset_view_role_id: int | None = None,
    superset_edit_role_id: int | None = None,
) -> None:
    """Set the project as provisioned by updating its 'project_resources_provisioned_at' timestamp.

    dashboard_id and role IDs are only written when a non-None value is passed; None leaves
    existing values intact.
    To explicitly update or clear these values use update_project_superset_role_ids.

    Args:
        session: Database session.
        project_id: The project ID.
        dashboard_id: The dashboard ID. None leaves existing value intact.
        provisioned_at: The datetime to set. Defaults to current time if not provided.
        superset_view_role_id: The Superset view-only role ID. None leaves existing value intact.
        superset_edit_role_id: The Superset edit role ID. None leaves existing value intact.
    """
    orm_project = get_non_deleted_project_model(session, project_id)
    if orm_project is None:
        raise exceptions.ProjectNotFound()
    orm_project.project_resources_provisioned_at = provisioned_at or datetime.datetime.utcnow()
    if dashboard_id is not None:
        orm_project.dashboard_id = dashboard_id
    if superset_view_role_id is not None:
        orm_project.superset_view_role_id = superset_view_role_id
    if superset_edit_role_id is not None:
        orm_project.superset_edit_role_id = superset_edit_role_id
    session.commit()


def assert_project_resources_provisioned(project: schemas.ProjectResponse) -> None:
    """Guard that raises exception if project resources are not yet provisioned.

    Call this before creating any job run to ensure BigQuery dataset and
    Superset dashboard exist.

    Args:
        project: The project response schema.
    """
    if project.project_resources_provisioned_at is None:
        raise exceptions.ProjectResourcesNotProvisioned(project.id)


def assert_project_resources_provisioned_with_get(
    session: sqlalchemy.orm.Session,
    project_id: int,
) -> None:
    """Fetch project and guard that resources are provisioned.

    Convenience function that combines get_project and
    assert_project_resources_provisioned. Use when you don't already have
    the project fetched.
    """
    project = get_project(session, project_id)
    if project is None:
        raise exceptions.ProjectNotFound()
    assert_project_resources_provisioned(project)


def get_non_deleted_project_model(
    session: sqlalchemy.orm.Session, project_id: int
) -> models.Project | None:
    """Get a non-deleted project model."""
    orm_project = (
        session.query(models.Project)
        .filter(
            models.Project.deleted_at.is_(None),
            models.Project.id == project_id,
        )
        .first()
    )
    return orm_project


def delete_project(
    session: sqlalchemy.orm.Session, project_id: int, delete_project_db: bool = False
) -> None:
    """Delete an project."""
    orm_project = get_non_deleted_project_model(session, project_id)
    if orm_project is None:
        raise exceptions.ProjectNotFound()
    if delete_project_db and not config.settings.USE_MOCK_BQ:
        project_namespace = utils.get_project_namespace(project_id)
        projects.delete_project_db(project_namespace)
    orm_project.deleted_at = datetime.datetime.utcnow()
    session.add(orm_project)
    session.commit()
    return None
