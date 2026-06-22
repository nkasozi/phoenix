"""Add workspace project relationship.

Revision ID: 6d4b2c6a304c
Revises: df23bee88382
Create Date: 2024-04-12 13:55:26.167391

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6d4b2c6a304c"
down_revision: Union[str, None] = "df23bee88382"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE_NAME = "projects"


def upgrade() -> None:
    """Upgrade for 6d4b2c6a304c."""
    op.add_column(
        TABLE_NAME,
        sa.Column("workspace_slug", sa.String(), nullable=False, server_default="main"),
    )
    op.create_foreign_key(
        "fk_workspace_slug", TABLE_NAME, "workspaces", ["workspace_slug"], ["slug"]
    )
    op.drop_column(TABLE_NAME, "workspace_id")


def downgrade() -> None:
    """Downgrade for df23bee88382."""
    op.add_column(
        TABLE_NAME, sa.Column("workspace_id", sa.VARCHAR(), autoincrement=False, nullable=False)
    )
    op.drop_constraint("fk_workspace_slug", TABLE_NAME, type_="foreignkey")
    op.drop_column(TABLE_NAME, "workspace_slug")
