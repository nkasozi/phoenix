"""Create workspace model.

Revision ID: 7cb955da8fb9
Revises: f766ea48c9d1
Create Date: 2024-04-10 09:12:01.520951

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7cb955da8fb9"
down_revision: Union[str, None] = "f766ea48c9d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE_NAME = "workspaces"


def upgrade() -> None:
    """Upgrade for 7cb955da8fb9."""
    op.create_table(
        TABLE_NAME,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workspaces_slug"), "workspaces", ["slug"], unique=True)


def downgrade() -> None:
    """Downgrade for 7cb955da8fb9."""
    op.drop_index(op.f("ix_workspaces_slug"), table_name=TABLE_NAME)
    op.drop_table(TABLE_NAME)
