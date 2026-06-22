"""Add manual_upload_gathers table.

Revision ID: 3c2a32ada281
Revises: 4c3f3861752b
Create Date: 2024-12-11 09:34:59.682475

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3c2a32ada281"
down_revision: Union[str, None] = "4c3f3861752b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 3c2a32ada281."""
    op.create_table(
        "manual_upload_gathers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uploaded_file_name", sa.String(), nullable=False),
        sa.Column("file_url", sa.String(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("file_row_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id"],
            ["gathers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade for 3c2a32ada281."""
    op.drop_table("manual_upload_gathers")
