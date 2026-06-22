"""Rename limit_total_comments to limit_comments_per_post in TikTok comments gather.

Revision ID: 9ae82d1a1aa5
Revises: 3c2a32ada281
Create Date: 2025-02-12 08:20:01.983020

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9ae82d1a1aa5"
down_revision: Union[str, None] = "3c2a32ada281"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 9ae82d1a1aa5."""
    # 1. Add the new column with nullable=True first.
    op.add_column(
        "apify_tiktok_comments_gathers",
        sa.Column("limit_total_comments", sa.Integer(), nullable=True),
    )

    # 2. Copy data from 'limit_comments_per_post' to 'limit_total_comments'.
    op.execute(
        """
        UPDATE apify_tiktok_comments_gathers
        SET limit_total_comments = limit_comments_per_post
        """
    )

    # 3. Alter the column to make it NOT NULL.
    op.alter_column(
        "apify_tiktok_comments_gathers",
        "limit_total_comments",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # 4. Drop the old column.
    op.drop_column("apify_tiktok_comments_gathers", "limit_comments_per_post")


def downgrade() -> None:
    """Downgrade for 9ae82d1a1aa5."""
    # 1. Re-add the old column with nullable=True first.
    op.add_column(
        "apify_tiktok_comments_gathers",
        sa.Column("limit_comments_per_post", sa.Integer(), nullable=True),
    )

    # 2. Copy data from 'limit_total_comments' to 'limit_comments_per_post'.
    op.execute(
        """
        UPDATE apify_tiktok_comments_gathers
        SET limit_comments_per_post = limit_total_comments
        """
    )

    # 3. Alter the old column to make it NOT NULL.
    op.alter_column(
        "apify_tiktok_comments_gathers",
        "limit_comments_per_post",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # 4. Drop the new column.
    op.drop_column("apify_tiktok_comments_gathers", "limit_total_comments")
