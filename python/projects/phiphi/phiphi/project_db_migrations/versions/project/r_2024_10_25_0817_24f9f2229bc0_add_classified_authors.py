"""Add classified_authors table.

Revision ID: 24f9f2229bc0
Revises: 0da2461a263f
Create Date: 2024-10-25 08:17:17.325958

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "24f9f2229bc0"
down_revision: Union[str, None] = "0da2461a263f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 24f9f2229bc0."""
    op.create_table(
        "classified_authors",
        sa.Column("classifier_id", sa.Integer(), nullable=False),
        sa.Column("classifier_version_id", sa.Integer(), nullable=False),
        sa.Column("class_name", sa.String(), nullable=False),
        sa.Column("phoenix_platform_message_author_id", sa.String(), nullable=False),
        sa.Column("job_run_id", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade for 24f9f2229bc0."""
    op.drop_table("classified_authors")
