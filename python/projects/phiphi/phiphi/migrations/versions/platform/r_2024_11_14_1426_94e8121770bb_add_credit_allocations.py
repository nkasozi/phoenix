"""Add credit_allocations.

Revision ID: 94e8121770bb
Revises: 0b1b5abdfed0
Create Date: 2024-11-14 14:26:05.726723

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "94e8121770bb"
down_revision: Union[str, None] = "0b1b5abdfed0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 94e8121770bb."""
    op.create_table(
        "credit_allocations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_credit_allocations_project_id", "credit_allocations", ["project_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade for 94e8121770bb."""
    op.drop_index("idx_credit_allocations_project_id", table_name="credit_allocations")
    op.drop_table("credit_allocations")
