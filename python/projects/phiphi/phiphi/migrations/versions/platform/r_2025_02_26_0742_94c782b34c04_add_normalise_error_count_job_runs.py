"""Add gather_normalise_error_count column to job_runs.

Revision ID: 94c782b34c04
Revises: 9ae82d1a1aa5
Create Date: 2025-02-26 07:42:00.021955

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "94c782b34c04"
down_revision: Union[str, None] = "9ae82d1a1aa5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 94c782b34c04."""
    op.add_column(
        "job_runs", sa.Column("gather_normalise_error_count", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade for 94c782b34c04."""
    op.drop_column("job_runs", "gather_normalise_error_count")
