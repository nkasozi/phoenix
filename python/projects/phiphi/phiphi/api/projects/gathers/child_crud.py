"""Generic gather crud."""

from typing import Type, TypeVar

import sqlalchemy.orm

from phiphi.api import exceptions
from phiphi.api.projects.gathers import child_types
from phiphi.api.projects.gathers import crud as gather_crud
from phiphi.api.projects.gathers import models as gather_model
from phiphi.api.projects.gathers import schemas as gather_schema
from phiphi.api.projects.gathers.apify_facebook_comments import (
    models as facebook_comment_models,  # noqa: F401
)
from phiphi.api.projects.gathers.apify_facebook_posts import (
    models as facebook_post_models,  # noqa: F401
)

# Although these are the same as child_route types we need to redefine them here
# otherwise we get strange errors
response_schema_type = TypeVar("response_schema_type", bound=gather_schema.GatherChildResponseBase)
create_schema_type = TypeVar("create_schema_type", bound=gather_schema.GatherCreate)
child_model_type = TypeVar("child_model_type", bound=gather_model.Gather)


def create_child_gather(
    response_schema: Type[response_schema_type],
    session: sqlalchemy.orm.Session,
    project_id: int,
    request_schema: create_schema_type,
    child_model: Type[child_model_type],
    child_type: gather_schema.ChildTypeName,
) -> response_schema_type:
    """Create child gather.

    A generalised function to create a child gather. This function is used to create
    child gathers for different platforms and data types.

    Args:
        response_schema (Type[response_schema_type]): Response schema
        session (sqlalchemy.orm.Session): Database session
        project_id (int): Project id
        request_schema (create_schema_type): Request schema
        child_model (Type[child_model_type]): Child model
        child_type (str): Child type

    Returns:
        response_schema_type: Response schema
    """
    orm_child_gather = child_model(
        **request_schema.dict(),
        project_id=project_id,
        child_type=child_type,
    )
    session.add(orm_child_gather)
    session.commit()
    session.refresh(orm_child_gather)
    return response_schema.model_validate(orm_child_gather)


def get_child_gather(
    session: sqlalchemy.orm.Session,
    project_id: int,
    gather_id: int,
) -> child_types.AllChildTypesUnion | None:
    """Get a child gather.

    A generalised function to get a child gather. This function is used to get
    child gathers for different platforms and data types.
    """
    orm_gather = gather_crud.get_orm_gather(session, project_id, gather_id)
    if orm_gather is None:
        return None

    child_type = gather_schema.ChildTypeName(orm_gather.child_type)
    child_reponse_type = child_types.get_response_type(child_type)
    return child_reponse_type.model_validate(orm_gather)


def update_child_gather(
    session: sqlalchemy.orm.Session,
    project_id: int,
    gather_id: int,
    request_schema: gather_schema.GatherUpdate,
) -> child_types.AllChildTypesUnion | None:
    """Update a child gather.

    A generalised function to update a child gather. This function is used to update
    child gathers for different platforms and data types.
    """
    orm_gather = gather_crud.get_orm_gather(session, project_id, gather_id)
    if orm_gather is None:
        raise exceptions.GatherNotFound()

    for field in request_schema.dict(exclude_unset=True):
        setattr(orm_gather, field, request_schema.dict()[field])

    session.add(orm_gather)
    session.commit()
    session.refresh(orm_gather)
    child_type = gather_schema.ChildTypeName(orm_gather.child_type)
    child_reponse_type = child_types.get_response_type(child_type)
    return child_reponse_type.model_validate(orm_gather)
