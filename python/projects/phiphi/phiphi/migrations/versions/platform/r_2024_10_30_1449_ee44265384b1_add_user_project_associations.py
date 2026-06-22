"""Add user_project_associations table.

Revision ID: ee44265384b1
Revises: 7794ea5cfd9b
Create Date: 2024-10-30 14:49:01.285671

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ee44265384b1"
down_revision: Union[str, None] = "7794ea5cfd9b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for ee44265384b1."""
    op.create_table(
        "user_project_associations",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
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
        sa.PrimaryKeyConstraint("user_id", "project_id"),
    )
    op.create_index(
        "idx_user_id_project_id_role",
        "user_project_associations",
        ["user_id", "project_id", "role"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade for ee44265384b1."""
    op.drop_index("idx_user_id_project_id_role", table_name="user_project_associations")
    op.drop_table("user_project_associations")
