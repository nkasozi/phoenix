"""Add classifiers and classes tables.

Revision ID: d1891a8b0a04
Revises: 16684153ddc6
Create Date: 2024-08-21 14:52:01.630593

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from phiphi.api import base_models

# revision identifiers, used by Alembic.
revision: str = "d1891a8b0a04"
down_revision: Union[str, None] = "16684153ddc6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for d1891a8b0a04."""
    op.create_table(
        "classes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "classifiers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("params", base_models.JSONEncodedValue(), nullable=True),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade for d1891a8b0a04."""
    op.drop_table("classifiers")
    op.drop_table("classes")
