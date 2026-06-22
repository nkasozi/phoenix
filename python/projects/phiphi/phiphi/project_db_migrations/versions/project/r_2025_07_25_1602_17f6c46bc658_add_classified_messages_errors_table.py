"""Add classified_messages_errors table.

Revision ID: 17f6c46bc658
Revises: cf0fb5d10597
Create Date: 2025-07-25 16:02:01.881653

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "17f6c46bc658"
down_revision: Union[str, None] = "cf0fb5d10597"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 17f6c46bc658."""
    op.create_table(
        "classified_messages_errors",
        sa.Column("classifier_id", sa.Integer(), nullable=False),
        sa.Column("classifier_version_id", sa.Integer(), nullable=False),
        sa.Column("phoenix_platform_message_id", sa.String(), nullable=False),
        sa.Column("job_run_id", sa.Integer(), nullable=False),
        sa.Column("error_json", sa.String(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade for 17f6c46bc658."""
    op.drop_table("classified_messages_errors")
