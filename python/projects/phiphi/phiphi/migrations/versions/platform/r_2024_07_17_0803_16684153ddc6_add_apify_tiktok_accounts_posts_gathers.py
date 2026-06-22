"""Add apify tiktok accounts posts gathers.

Revision ID: 16684153ddc6
Revises: ca1191c60c08
Create Date: 2024-07-17 08:03:17.629552

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from phiphi.api import base_models

revision: str = "16684153ddc6"
down_revision: Union[str, None] = "ca1191c60c08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 16684153ddc6."""
    op.create_table(
        "apify_tiktok_accounts_posts_gathers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("limit_posts_per_account", sa.Integer(), nullable=False),
        sa.Column("account_username_list", base_models.JSONEncodedValue(), nullable=False),
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
    """Downgrade for 16684153ddc6."""
    op.drop_table("apify_tiktok_accounts_posts_gathers")
