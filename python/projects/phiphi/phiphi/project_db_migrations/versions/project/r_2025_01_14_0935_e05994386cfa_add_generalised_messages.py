"""Add generalised_messages table.

Revision ID: e05994386cfa
Revises: 3099ccfdde06
Create Date: 2025-01-14 09:35:16.517868

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e05994386cfa"
down_revision: Union[str, None] = "3099ccfdde06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for e05994386cfa."""
    op.create_table(
        "generalised_messages",
        sa.Column("gather_id", sa.Integer(), nullable=False),
        sa.Column("gather_batch_id", sa.Integer(), nullable=False),
        sa.Column("gathered_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("phoenix_processed_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("gather_type", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("data_type", sa.String(), nullable=False),
        sa.Column("pi_platform_message_id", sa.String(), nullable=True),
        sa.Column("pi_platform_message_author_id", sa.String(), nullable=True),
        sa.Column("pi_platform_message_author_name", sa.String(), nullable=True),
        sa.Column("pi_platform_parent_message_id", sa.String(), nullable=True),
        sa.Column("pi_platform_root_message_id", sa.String(), nullable=True),
        sa.Column("pi_text", sa.String(), nullable=True),
        sa.Column("pi_platform_message_url", sa.String(), nullable=True),
        sa.Column("platform_message_last_updated_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("phoenix_platform_message_id", sa.String(), nullable=False),
        sa.Column("phoenix_platform_message_author_id", sa.String(), nullable=False),
        sa.Column("phoenix_platform_parent_message_id", sa.String(), nullable=True),
        sa.Column("phoenix_platform_root_message_id", sa.String(), nullable=True),
        sa.Column("like_count", sa.Integer(), nullable=False),
        sa.Column("share_count", sa.Integer(), nullable=False),
        sa.Column("comment_count", sa.Integer(), nullable=False),
        sa.Column("tiktok_post_plays", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade for e05994386cfa."""
    op.drop_table("generalised_messages")
