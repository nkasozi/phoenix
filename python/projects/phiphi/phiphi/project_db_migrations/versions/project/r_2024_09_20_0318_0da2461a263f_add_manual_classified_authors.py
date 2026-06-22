"""Add manually_classified_authors table.

Revision ID: 0da2461a263f
Revises: 82d406d86348
Create Date: 2024-09-20 03:18:38.596542

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0da2461a263f"
down_revision: Union[str, None] = "82d406d86348"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 0da2461a263f."""
    op.create_table(
        "manually_classified_authors",
        sa.Column("class_name", sa.String(), nullable=False),
        sa.Column("phoenix_platform_author_id", sa.String(), nullable=False),
        sa.Column("last_updated_at", sa.TIMESTAMP(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade for 0da2461a263f."""
    op.drop_table("manually_classified_authors")
