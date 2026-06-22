"""Add intermediatory_class_to_keyword_configs table.

Revision ID: 973f495eefb9
Revises: 1b298897d1fd
Create Date: 2024-10-16 05:41:09.866179

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "973f495eefb9"
down_revision: Union[str, None] = "1b298897d1fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 973f495eefb9."""
    op.create_table(
        "intermediatory_class_to_keyword_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("classifier_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("musts", sa.String(), nullable=False),
        sa.Column("nots", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["class_id"],
            ["intermediatory_classes.id"],
        ),
        sa.ForeignKeyConstraint(
            ["classifier_id"],
            ["classifiers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "classifier_id",
            "class_id",
            "musts",
            "nots",
            name="uq_intermediatory_class_to_keyword_configs",
        ),
    )
    op.create_index(
        "ix_intermediatory_class_to_keyword_configs",
        "intermediatory_class_to_keyword_configs",
        ["classifier_id", "class_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade for 973f495eefb9."""
    op.drop_index(
        "ix_intermediatory_class_to_keyword_configs",
        table_name="intermediatory_class_to_keyword_configs",
    )
    op.drop_table("intermediatory_class_to_keyword_configs")
