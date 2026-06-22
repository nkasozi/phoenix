"""Add apify_x_advanced_searches_posts_comments.

Revision ID: e25ef50f76a4
Revises: 937e13f3f488
Create Date: 2025-09-09 10:12:32.546093

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from phiphi.api import base_models

revision: str = "e25ef50f76a4"
down_revision: Union[str, None] = "937e13f3f488"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for e25ef50f76a4."""
    op.create_table(
        "apify_x_advanced_searches_posts_comments_gathers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("search_list", base_models.JSONEncodedValue(), nullable=False),
        sa.Column("limit_results_per_search", sa.Integer(), nullable=False),
        sa.Column("posts_created_after", sa.String(), nullable=True),
        sa.Column("posts_created_before", sa.String(), nullable=True),
        sa.Column("sort", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"],
            ["gathers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade for e25ef50f76a4."""
    op.drop_table("apify_x_advanced_searches_posts_comments_gathers")
