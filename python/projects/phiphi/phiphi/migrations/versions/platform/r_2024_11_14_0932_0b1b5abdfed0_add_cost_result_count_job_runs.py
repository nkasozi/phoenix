"""Add cost and gather_result_count columns to job_runs.

Revision ID: 0b1b5abdfed0
Revises: ee44265384b1
Create Date: 2024-11-14 09:32:27.340163

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0b1b5abdfed0"
down_revision: Union[str, None] = "ee44265384b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 0b1b5abdfed0."""
    op.add_column("job_runs", sa.Column("total_cost", sa.Float(), nullable=True))
    op.add_column("job_runs", sa.Column("gather_result_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade for 0b1b5abdfed0."""
    op.drop_column("job_runs", "gather_result_count")
    op.drop_column("job_runs", "total_cost")
