"""Credit allocations for a projects."""

import datetime
from typing import Annotated

import pydantic
import sqlalchemy as sa

from phiphi import platform_db
from phiphi.api import base_models


class CreditAllocationsBase(platform_db.Base):
    """CreditAllocations base model.

    An auditable log of credit allocations for a project.
    """

    __abstract__ = True

    id: sa.orm.Mapped[int] = sa.orm.mapped_column(primary_key=True)
    # User is added so we know who did the allocation.
    user_id: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.ForeignKey("users.id"))
    project_id: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.ForeignKey("projects.id"))
    amount: sa.orm.Mapped[float]
    # Description so we know why the allocation was made.
    description: sa.orm.Mapped[str]


class CreditAllocations(CreditAllocationsBase, base_models.TimestampModel):
    """CreditAllocations model."""

    __tablename__ = "credit_allocations"

    __table_args__ = (sa.Index("idx_credit_allocations_project_id", "project_id"),)


class CreditAllocationCreate(pydantic.BaseModel):
    """Credit allocation create."""

    amount: Annotated[
        float,
        pydantic.Field(
            description=(
                "The amount to add to the credit. "
                "Can be positive or negative to adjust the credit as needed."
            )
        ),
    ]
    description: Annotated[
        str, pydantic.Field(description="The reason for the credit allocation.")
    ]


class CreditAllocationResponse(pydantic.BaseModel):
    """Credit allocation response."""

    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    user_id: int
    project_id: int
    amount: float
    description: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


def create_credit_allocation(
    session: sa.orm.Session,
    user_id: int,
    project_id: int,
    credit_allocation_create: CreditAllocationCreate,
) -> CreditAllocationResponse:
    """Add a credit allocation."""
    credit_allocation = CreditAllocations(
        user_id=user_id,
        project_id=project_id,
        amount=credit_allocation_create.amount,
        description=credit_allocation_create.description,
    )
    session.add(credit_allocation)
    session.commit()
    return CreditAllocationResponse.model_validate(credit_allocation)


def get_credit_allocations(
    session: sa.orm.Session, project_id: int
) -> list[CreditAllocationResponse]:
    """Get all credit allocations for a project."""
    credit_allocations = (
        session.query(CreditAllocations)
        .order_by(CreditAllocations.id.desc())
        .filter(CreditAllocations.project_id == project_id)
        .all()
    )
    return [
        CreditAllocationResponse.model_validate(credit_allocation)
        for credit_allocation in credit_allocations
    ]


def get_total_credit_allocation(session: sa.orm.Session, project_id: int) -> float:
    """Get the total credit allocation for a project."""
    total_credit_allocation = (
        session.query(sa.func.sum(CreditAllocations.amount))
        .filter(CreditAllocations.project_id == project_id)
        .scalar()
    )
    return total_credit_allocation or 0.0
