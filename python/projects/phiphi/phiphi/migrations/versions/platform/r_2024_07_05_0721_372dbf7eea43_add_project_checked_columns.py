"""Add project checked columns.

Revision ID: 372dbf7eea43
Revises: 6bae60cebda6
Create Date: 2024-07-05 07:21:43.738130

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "372dbf7eea43"
down_revision: Union[str, None] = "6bae60cebda6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 372dbf7eea43."""
    op.add_column("projects", sa.Column("checked_problem_statement", sa.Boolean(), nullable=True))
    op.add_column("projects", sa.Column("checked_sources", sa.Boolean(), nullable=True))
    op.add_column("projects", sa.Column("checked_gather", sa.Boolean(), nullable=True))
    op.add_column("projects", sa.Column("checked_classify", sa.Boolean(), nullable=True))
    op.add_column("projects", sa.Column("checked_visualise", sa.Boolean(), nullable=True))
    op.add_column("projects", sa.Column("checked_explore", sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade for 372dbf7eea43."""
    op.drop_column("projects", "checked_explore")
    op.drop_column("projects", "checked_visualise")
    op.drop_column("projects", "checked_classify")
    op.drop_column("projects", "checked_gather")
    op.drop_column("projects", "checked_sources")
    op.drop_column("projects", "checked_problem_statement")
