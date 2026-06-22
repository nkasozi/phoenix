"""Create users table.

Revision ID: 476d06370a9c
Revises:
Create Date: 2024-03-29 10:38:47.711702

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "476d06370a9c"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE_NAME: str = "users"


def upgrade() -> None:
    """Upgrade for 476d06370a9c."""
    op.create_table(
        TABLE_NAME,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), TABLE_NAME, ["email"], unique=True)


def downgrade() -> None:
    """Downgrade for 476d06370a9c."""
    op.drop_index(op.f("ix_users_email"), table_name=TABLE_NAME)
    op.drop_table(TABLE_NAME)
