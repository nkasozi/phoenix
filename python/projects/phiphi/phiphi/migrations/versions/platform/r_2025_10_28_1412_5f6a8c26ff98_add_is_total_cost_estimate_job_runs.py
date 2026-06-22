"""Add is_total_cost_estimated to job_runs.

Revision ID: 5f6a8c26ff98
Revises: bf190b6b19a7
Create Date: 2025-10-28 14:12:40.041329

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5f6a8c26ff98"
down_revision: Union[str, None] = "bf190b6b19a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 5f6a8c26ff98."""
    op.add_column(
        "job_runs",
        sa.Column(
            "is_total_cost_estimated", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )


def downgrade() -> None:
    """Downgrade for 5f6a8c26ff98."""
    op.drop_column("job_runs", "is_total_cost_estimated")
