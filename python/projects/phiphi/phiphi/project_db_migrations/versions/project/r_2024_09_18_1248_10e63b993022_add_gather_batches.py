"""Add gather_batches table.

Revision ID: 10e63b993022
Revises: 43f647aeb286
Create Date: 2024-09-18 12:48:51.961426

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "10e63b993022"
down_revision: Union[str, None] = "43f647aeb286"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 10e63b993022."""
    op.create_table(
        "gather_batches",
        sa.Column("gather_id", sa.Integer(), nullable=False),
        sa.Column("job_run_id", sa.Integer(), nullable=False),
        sa.Column("gather_type", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("data_type", sa.String(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("gathered_at", sa.TIMESTAMP(), nullable=False),
        # This has to be a string because sqlalchemy has not yet implemented
        # a JSON type for BigQuery.
        # https://github.com/googleapis/python-bigquery-sqlalchemy/issues/546
        # And not in pandas gbq:
        # https://github.com/googleapis/python-bigquery/issues/1966
        sa.Column("json_data", sa.String(), nullable=False),
        sa.Column("last_processed_at", sa.TIMESTAMP(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade for 10e63b993022."""
    op.drop_table("gather_batches")
