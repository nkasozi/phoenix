"""Remove mistaken columns apify tiktok hashtags posts.

Revision ID: 323e15610133
Revises: d31116c6bea5
Create Date: 2024-09-06 10:58:02.319196

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "323e15610133"
down_revision: Union[str, None] = "b94b5e2a7757"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 323e15610133."""
    op.drop_column("apify_tiktok_hashtags_posts_gathers", "posts_created_since_num_days")
    op.drop_column("apify_tiktok_hashtags_posts_gathers", "posts_created_after")


def downgrade() -> None:
    """Downgrade for 323e15610133."""
    op.add_column(
        "apify_tiktok_hashtags_posts_gathers",
        sa.Column("posts_created_after", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "apify_tiktok_hashtags_posts_gathers",
        sa.Column(
            "posts_created_since_num_days", sa.INTEGER(), autoincrement=False, nullable=True
        ),
    )
