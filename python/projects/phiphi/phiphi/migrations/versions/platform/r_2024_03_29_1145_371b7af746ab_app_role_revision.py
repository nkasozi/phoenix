"""App_role_revision.

Revision ID: 371b7af746ab
Revises: 476d06370a9c
Create Date: 2024-03-29 11:45:33.153102

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "371b7af746ab"
down_revision: Union[str, None] = "476d06370a9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE_NAME = "users"
COLUMN_NAME = "app_role"


def upgrade() -> None:
    """Upgrade for 371b7af746ab."""
    op.add_column(TABLE_NAME, sa.Column(COLUMN_NAME, sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade for 371b7af746ab."""
    op.drop_column(TABLE_NAME, COLUMN_NAME)
