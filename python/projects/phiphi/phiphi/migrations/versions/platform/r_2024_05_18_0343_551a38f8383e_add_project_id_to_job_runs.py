"""Add_project_id_to_job_runs.

Revision ID: 551a38f8383e
Revises: 63f1d6bace12
Create Date: 2024-05-18 03:43:23.446661

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "551a38f8383e"
down_revision: Union[str, None] = "63f1d6bace12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 551a38f8383e."""
    op.add_column("job_runs", sa.Column("project_id", sa.Integer(), nullable=False))
    op.create_index(
        "idx_project_id_foreign_job_type_foreign_id",
        "job_runs",
        ["project_id", "foreign_job_type", "foreign_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade for 551a38f8383e."""
    op.drop_index("idx_project_id_foreign_job_type_foreign_id", table_name="job_runs")
    op.drop_column("job_runs", "project_id")
