"""Reimplement classifiers.

Revision ID: 36150ecd833a
Revises: 7f9234efb602
Create Date: 2024-10-01 21:54:36.808142

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from phiphi.api import base_models

# revision identifiers, used by Alembic.
revision: str = "36150ecd833a"
down_revision: Union[str, None] = "7f9234efb602"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 36150ecd833a."""
    op.create_table(
        "classifier_versions",
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column("classifier_id", sa.Integer(), nullable=False),
        sa.Column("classes_dict", base_models.JSONEncodedValue(), nullable=False),
        sa.Column("params", base_models.JSONEncodedValue(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["classifier_id"],
            ["classifiers.id"],
        ),
        sa.PrimaryKeyConstraint("version_id"),
    )
    op.drop_table("classes")
    op.drop_column("classifiers", "params")


def downgrade() -> None:
    """Downgrade for 36150ecd833a."""
    op.add_column(
        "classifiers", sa.Column("params", sa.VARCHAR(), autoincrement=False, nullable=True)
    )
    op.create_table(
        "classes",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name="classes_pkey"),
    )
    op.drop_table("classifier_versions")
