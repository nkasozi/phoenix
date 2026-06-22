"""Add apify tiktok hashtags posts.

Revision ID: d31116c6bea5
Revises: d1891a8b0a04
Create Date: 2024-08-21 15:14:32.256377

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from phiphi.api import base_models

# revision identifiers, used by Alembic.
revision: str = "d31116c6bea5"
down_revision: Union[str, None] = "d1891a8b0a04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for d31116c6bea5."""
    op.create_table(
        "apify_tiktok_hashtags_posts_gathers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("limit_posts_per_hashtag", sa.Integer(), nullable=False),
        sa.Column("hashtag_list", base_models.JSONEncodedValue(), nullable=False),
        sa.Column("posts_created_after", sa.String(), nullable=True),
        sa.Column("posts_created_since_num_days", sa.Integer(), nullable=True),
        sa.Column("proxy_country_to_gather_from", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"],
            ["gathers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade for d31116c6bea5."""
    op.drop_table("apify_tiktok_hashtags_posts_gathers")
