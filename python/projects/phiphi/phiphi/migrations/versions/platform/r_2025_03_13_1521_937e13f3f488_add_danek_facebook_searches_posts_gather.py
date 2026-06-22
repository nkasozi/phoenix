"""A database migration for adding the `danek_facebook_searches_posts_gathers` table.

Revision ID: 937e13f3f488
Revises: 94c782b34c04
Create Date: 2025-03-13 15:21:59.574805

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from phiphi.api import base_models

# revision identifiers, used by Alembic.
revision: str = "937e13f3f488"
down_revision: Union[str, None] = "94c782b34c04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 937e13f3f488."""
    op.create_table(
        "danek_facebook_searches_posts_gathers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stop_scraping_per_search_after_count", sa.Integer(), nullable=False),
        sa.Column("search_list", base_models.JSONEncodedValue(), nullable=False),
        sa.Column("proxy_country_to_gather_from", sa.String(), nullable=True),
        sa.Column("posts_created_after", sa.String(), nullable=True),
        sa.Column("posts_created_before", sa.String(), nullable=True),
        sa.Column("recent_posts", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id"],
            ["gathers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade for 937e13f3f488."""
    op.drop_table("danek_facebook_searches_posts_gathers")
