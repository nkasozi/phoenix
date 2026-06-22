"""Generic_timestamps_job_runs.

Revision ID: 76ac5b340772
Revises: 551a38f8383e
Create Date: 2024-05-18 03:51:24.194157

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "76ac5b340772"
down_revision: Union[str, None] = "551a38f8383e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 76ac5b340772."""
    op.add_column("job_runs", sa.Column("created_at", sa.DateTime(), nullable=False))
    op.add_column("job_runs", sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.drop_column("job_runs", "row_created_at")


def downgrade() -> None:
    """Downgrade for 76ac5b340772."""
    op.add_column(
        "job_runs",
        sa.Column("row_created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    )
    op.drop_column("job_runs", "updated_at")
    op.drop_column("job_runs", "created_at")
    # ### end Alembic commands ###
