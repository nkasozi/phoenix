"""Add intermediatory author classes.

Revision ID: 0f2140a3053f
Revises: 2471145c028e
Create Date: 2024-10-24 11:27:29.679315

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0f2140a3053f"
down_revision: Union[str, None] = "2471145c028e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 0f2140a3053f."""
    op.create_table(
        "intermediatory_author_classes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("classifier_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("phoenix_platform_message_author_id", sa.String(), nullable=False),
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
            "phoenix_platform_message_author_id",
            name="uq_intermediatory_author_classes",
        ),
    )
    op.create_index(
        "ix_intermediatory_author_classes",
        "intermediatory_author_classes",
        ["classifier_id", "class_id"],
        unique=False,
    )
    op.create_index(
        "ix_intermediatory_author_classes_class_id",
        "intermediatory_author_classes",
        ["class_id"],
        unique=False,
    )
    op.create_index(
        "ix_intermediatory_author_classes_phoenix_id",
        "intermediatory_author_classes",
        ["phoenix_platform_message_author_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade for 0f2140a3053f."""
    op.drop_index(
        "ix_intermediatory_author_classes_phoenix_id", table_name="intermediatory_author_classes"
    )
    op.drop_index(
        "ix_intermediatory_author_classes_class", table_name="intermediatory_author_classes"
    )
    op.drop_index("ix_intermediatory_author_classes", table_name="intermediatory_author_classes")
    op.drop_table("intermediatory_author_classes")
