"""Add_apify_x_simple_searches.

Revision ID: bf190b6b19a7
Revises: e25ef50f76a4
Create Date: 2025-10-03 08:05:24.556784

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from phiphi.api import base_models

# revision identifiers, used by Alembic.
revision: str = "bf190b6b19a7"
down_revision: Union[str, None] = "e25ef50f76a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for bf190b6b19a7."""
    op.create_table(
        "apify_x_simple_searches_posts_comments_gathers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("handle_list", base_models.JSONEncodedValue(), nullable=False),
        sa.Column("keywords_list", base_models.JSONEncodedValue(), nullable=False),
        sa.Column("limit_results_per_search", sa.Integer(), nullable=False),
        sa.Column("posts_created_after", sa.String(), nullable=True),
        sa.Column("posts_created_before", sa.String(), nullable=True),
        sa.Column("sort", sa.String(), nullable=True),
        sa.Column("location_near", sa.String(), nullable=True),
        sa.Column("search_list", base_models.JSONEncodedValue(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id"],
            ["gathers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade for bf190b6b19a7."""
    op.drop_table("apify_x_simple_searches_posts_comments_gathers")
