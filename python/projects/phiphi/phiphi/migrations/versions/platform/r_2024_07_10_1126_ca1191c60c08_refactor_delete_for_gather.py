"""Refactor delete attributes for gather.

Revision ID: ca1191c60c08
Revises: 372dbf7eea43
Create Date: 2024-07-10 11:26:20.856995

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "ca1191c60c08"
down_revision: Union[str, None] = "372dbf7eea43"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for ca1191c60c08."""
    op.add_column("gathers", sa.Column("delete_job_run_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_gathers_job_runs", "gathers", "job_runs", ["delete_job_run_id"], ["id"]
    )
    op.drop_column("gathers", "deleted_at")


def downgrade() -> None:
    """Downgrade for ca1191c60c08."""
    op.add_column(
        "gathers",
        sa.Column("deleted_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    )
    op.drop_constraint("fk_gathers_job_runs", "gathers", type_="foreignkey")
    op.drop_column("gathers", "delete_job_run_id")
