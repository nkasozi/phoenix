"""Add intermediatory classes table.

Revision ID: 7c6392dd7767
Revises: 8eae2d691cdc
Create Date: 2024-10-10 14:12:58.224620

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7c6392dd7767"
down_revision: Union[str, None] = "8eae2d691cdc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 7c6392dd7767."""
    op.create_table(
        "intermediatory_classes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("classifier_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["classifier_id"],
            ["classifiers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("classifier_id", "name", name="uq_classifier_classname"),
    )
    op.create_index(
        "ix_classifier_classname",
        "intermediatory_classes",
        ["classifier_id", "name"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade for 7c6392dd7767."""
    op.drop_index("ix_classifier_classname", table_name="intermediatory_classes")
    op.drop_table("intermediatory_classes")
