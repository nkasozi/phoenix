"""Seed the credit allocations."""

from sqlalchemy.orm import Session

from phiphi.api.projects import credit_allocations


def seed_test_credit_allocations(session: Session) -> None:
    """Seed the credit allocations."""
    credit_allocations.create_credit_allocation(
        session=session,
        user_id=1,
        project_id=1,
        credit_allocation_create=credit_allocations.CreditAllocationCreate(
            amount=2000, description="Test"
        ),
    )

    credit_allocations.create_credit_allocation(
        session=session,
        user_id=1,
        project_id=1,
        credit_allocation_create=credit_allocations.CreditAllocationCreate(
            amount=-10, description="Test 2"
        ),
    )

    credit_allocations.create_credit_allocation(
        session=session,
        user_id=1,
        project_id=1,
        credit_allocation_create=credit_allocations.CreditAllocationCreate(
            amount=20.1, description="Test 3"
        ),
    )

    credit_allocations.create_credit_allocation(
        session=session,
        user_id=1,
        project_id=3,
        credit_allocation_create=credit_allocations.CreditAllocationCreate(
            amount=100, description="Credit allocation for project 3"
        ),
    )

    credit_allocations.create_credit_allocation(
        session=session,
        user_id=1,
        project_id=6,
        credit_allocation_create=credit_allocations.CreditAllocationCreate(
            amount=200,
            description=("Credit allocation for project 6"),
        ),
    )
