"""Add apify tiktok comments gathers.

Revision ID: ec85edb9a339
Revises: 323e15610133
Create Date: 2024-09-12 14:09:47.950029

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from phiphi.api import base_models

# revision identifiers, used by Alembic.
revision: str = "ec85edb9a339"
down_revision: Union[str, None] = "323e15610133"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for ec85edb9a339."""
    op.create_table(
        "apify_tiktok_comments_gathers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_url_list", base_models.JSONEncodedValue(), nullable=False),
        sa.Column("limit_comments_per_post", sa.Integer(), nullable=False),
        sa.Column("include_comment_replies", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id"],
            ["gathers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade for ec85edb9a339."""
    op.drop_table("apify_tiktok_comments_gathers")
