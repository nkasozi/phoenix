"""Add last_edited_at to classifiers.

Revision ID: 1b298897d1fd
Revises: d406c721af32
Create Date: 2024-10-15 09:56:19.767501

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1b298897d1fd"
down_revision: Union[str, None] = "d406c721af32"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 1b298897d1fd."""
    op.add_column("classifiers", sa.Column("last_edited_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade for 1b298897d1fd."""
    op.drop_column("classifiers", "last_edited_at")
