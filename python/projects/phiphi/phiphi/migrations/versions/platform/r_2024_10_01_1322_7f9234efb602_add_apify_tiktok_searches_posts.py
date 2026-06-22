"""Add Apify TikTok searches posts gathers table.

Revision ID: 7f9234efb602
Revises: ec85edb9a339
Create Date: 2024-10-01 13:22:00.825800

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from phiphi.api import base_models

# revision identifiers, used by Alembic.
revision: str = "7f9234efb602"
down_revision: Union[str, None] = "ec85edb9a339"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 7f9234efb602."""
    op.create_table(
        "apify_tiktok_searches_posts_gathers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("limit_posts_per_search", sa.Integer(), nullable=False),
        sa.Column("search_list", base_models.JSONEncodedValue(), nullable=False),
        sa.Column("proxy_country_to_gather_from", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"],
            ["gathers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade for 7f9234efb602."""
    op.drop_table("apify_tiktok_searches_posts_gathers")
