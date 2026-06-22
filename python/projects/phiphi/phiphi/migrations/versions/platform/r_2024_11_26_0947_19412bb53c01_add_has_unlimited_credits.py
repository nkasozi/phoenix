"""Add has_unlimited_credits column to projects.

Revision ID: 19412bb53c01
Revises: 94e8121770bb
Create Date: 2024-11-26 09:47:52.976206

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "19412bb53c01"
down_revision: Union[str, None] = "94e8121770bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 19412bb53c01."""
    op.add_column(
        "projects",
        sa.Column("has_unlimited_credits", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    """Downgrade for 19412bb53c01."""
    op.drop_column("projects", "has_unlimited_credits")
