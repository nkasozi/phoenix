"""Add_job_runs_table.

Revision ID: b710357283bb
Revises: 4054f263d95c
Create Date: 2024-05-16 09:37:39.956164

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b710357283bb"
down_revision: Union[str, None] = "4054f263d95c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for b710357283bb."""
    op.create_table(
        "job_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("row_created_at", sa.DateTime(), nullable=False),
        sa.Column("foreign_id", sa.Integer(), nullable=False),
        sa.Column("foreign_job_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("flow_run_id", sa.String(), nullable=True),
        sa.Column("flow_run_name", sa.String(), nullable=True),
        sa.Column("started_processing_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade for b710357283bb."""
    op.drop_table("job_runs")
