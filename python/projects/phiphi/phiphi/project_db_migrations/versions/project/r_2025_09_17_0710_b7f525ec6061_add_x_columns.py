"""Add x_columns to project db tables.

Revision ID: b7f525ec6061
Revises: 17f6c46bc658
Create Date: 2025-09-17 07:10:46.604580
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7f525ec6061"
down_revision: Union[str, None] = "17f6c46bc658"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for b7f525ec6061."""
    conn = op.get_bind()
    # Add nullable x_post_retweeted_id column to generalised_messages table
    # For BigQuery, we add nullable columns directly and they default to NULL
    conn.execute(
        sa.text("ALTER TABLE `generalised_messages` ADD COLUMN `x_post_retweeted_id` STRING")
    )
    conn.execute(
        sa.text("ALTER TABLE `tabulated_messages` ADD COLUMN `x_post_retweeted_id` STRING")
    )
    # Removing x_tweet_quotes as this data has been incorporated into comment count
    op.drop_column("tabulated_messages", "x_tweet_quotes")

    conn.execute(sa.text("ALTER TABLE `generalised_messages` ADD COLUMN `x_is_quote` BOOL"))
    conn.execute(sa.text("ALTER TABLE `tabulated_messages` ADD COLUMN `x_comment_is_quote` BOOL"))

    conn.execute(sa.text("ALTER TABLE `generalised_messages` ADD COLUMN `x_is_reply` BOOL"))
    conn.execute(sa.text("ALTER TABLE `tabulated_messages` ADD COLUMN `x_comment_is_reply` BOOL"))


def downgrade() -> None:
    """Downgrade for b7f525ec6061."""
    op.drop_column("generalised_messages", "x_post_retweeted_id")
    op.drop_column("tabulated_messages", "x_post_retweeted_id")
    op.drop_column("generalised_messages", "x_is_quote")
    op.drop_column("tabulated_messages", "x_comment_is_quote")
    op.drop_column("generalised_messages", "x_is_reply")
    op.drop_column("tabulated_messages", "x_comment_is_reply")
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE `tabulated_messages` ADD COLUMN `x_tweet_quotes` INT64"))
