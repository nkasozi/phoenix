"""Add classified_messages table.

Revision ID: 82d406d86348
Revises: 10e63b993022
Create Date: 2024-09-18 13:36:35.630542

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "82d406d86348"
down_revision: Union[str, None] = "10e63b993022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 82d406d86348."""
    op.create_table(
        "classified_messages",
        sa.Column("classifier_id", sa.Integer(), nullable=False),
        sa.Column("classifier_version_id", sa.Integer(), nullable=False),
        sa.Column("class_name", sa.String(), nullable=False),
        sa.Column("phoenix_platform_message_id", sa.String(), nullable=False),
        sa.Column("job_run_id", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade for 82d406d86348."""
    op.drop_table("classified_messages")
