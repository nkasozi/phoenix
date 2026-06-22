"""Add estimated_total_cost column to job_runs.

Revision ID: 4c3f3861752b
Revises: 19412bb53c01
Create Date: 2024-11-27 15:58:18.894049

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4c3f3861752b"
down_revision: Union[str, None] = "19412bb53c01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 4c3f3861752b."""
    op.add_column("job_runs", sa.Column("estimated_total_cost", sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade for 4c3f3861752b."""
    op.drop_column("job_runs", "estimated_total_cost")
