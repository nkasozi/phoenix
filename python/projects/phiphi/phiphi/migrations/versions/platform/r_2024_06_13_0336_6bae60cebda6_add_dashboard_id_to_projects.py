"""Add dashboard_id to projects.

Revision ID: 6bae60cebda6
Revises: abb72fed04ae
Create Date: 2024-06-13 03:36:46.592585

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6bae60cebda6"
down_revision: Union[str, None] = "abb72fed04ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 6bae60cebda6."""
    op.add_column("projects", sa.Column("dashboard_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade for 6bae60cebda6."""
    op.drop_column("projects", "dashboard_id")
