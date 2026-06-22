"""Add_job_runs_foreign_index.

Revision ID: 63f1d6bace12
Revises: b710357283bb
Create Date: 2024-05-17 03:07:01.219384

"""

from typing import Sequence, Union

from alembic import op

revision: str = "63f1d6bace12"
down_revision: Union[str, None] = "b710357283bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 63f1d6bace12."""
    op.create_index(
        "idx_foreign_job_type_foreign_id",
        "job_runs",
        ["foreign_job_type", "foreign_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade for 63f1d6bace12."""
    op.drop_index("idx_foreign_job_type_foreign_id", table_name="job_runs")
