"""Add description to classifiers.

Revision ID: c46b83ddcfec
Revises: 0f2140a3053f
Create Date: 2024-10-24 13:53:13.008601

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c46b83ddcfec"
down_revision: Union[str, None] = "0f2140a3053f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for c46b83ddcfec."""
    # It is not possible to add a non-nullable column without a default value
    op.add_column(
        "classifiers", sa.Column("description", sa.String(), nullable=True, server_default="")
    )
    # Change it so it is not optional
    op.alter_column("classifiers", "description", nullable=False)


def downgrade() -> None:
    """Downgrade for c46b83ddcfec."""
    op.drop_column("classifiers", "description")
