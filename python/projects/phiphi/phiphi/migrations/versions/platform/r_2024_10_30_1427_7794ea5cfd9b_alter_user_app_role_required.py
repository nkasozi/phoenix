"""Alter user app_role required.

Revision ID: 7794ea5cfd9b
Revises: c46b83ddcfec
Create Date: 2024-10-30 14:27:04.576947

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7794ea5cfd9b"
down_revision: Union[str, None] = "c46b83ddcfec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 7794ea5cfd9b."""
    op.execute("UPDATE users SET app_role = 'user' WHERE app_role IS NULL")
    op.alter_column("users", "app_role", existing_type=sa.VARCHAR(), nullable=False)


def downgrade() -> None:
    """Downgrade for 7794ea5cfd9b."""
    op.alter_column("users", "app_role", existing_type=sa.VARCHAR(), nullable=True)
