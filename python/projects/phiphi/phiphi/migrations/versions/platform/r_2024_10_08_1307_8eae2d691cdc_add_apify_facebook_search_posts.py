"""Add Apify Facebook search posts gathers table.

Revision ID: 8eae2d691cdc
Revises: 36150ecd833a
Create Date: 2024-10-08 13:07:30.006892

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from phiphi.api import base_models

# revision identifiers, used by Alembic.
revision: str = "8eae2d691cdc"
down_revision: Union[str, None] = "36150ecd833a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 8eae2d691cdc."""
    op.create_table(
        "apify_facebook_search_posts_gathers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("search_query", sa.String(), nullable=False),
        sa.Column("limit_posts", sa.Integer(), nullable=False),
        sa.Column("limit_retries", sa.Integer(), nullable=False),
        sa.Column("recent_posts", sa.Boolean(), nullable=True),
        sa.Column("proxy", base_models.JSONEncodedValue(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"],
            ["gathers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade for 8eae2d691cdc."""
    op.drop_table("apify_facebook_search_posts_gathers")
