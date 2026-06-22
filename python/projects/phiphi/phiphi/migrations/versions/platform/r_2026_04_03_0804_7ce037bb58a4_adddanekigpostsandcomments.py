"""AddDanekIGPostsAndComments.

Revision ID: 7ce037bb58a4
Revises: 5f6a8c26ff98
Create Date: 2026-04-03 08:04:17.664661

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from phiphi.api import base_models

# revision identifiers, used by Alembic.
revision: str = "7ce037bb58a4"
down_revision: Union[str, None] = "5f6a8c26ff98"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 7ce037bb58a4."""
    op.create_table(
        "danek_instagram_posts_gathers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_username_list", base_models.JSONEncodedValue(), nullable=False),
        sa.Column("limit_posts_per_account", sa.Integer(), nullable=False),
        sa.Column("posts_created_after", sa.String(), nullable=True),
        sa.Column("scrape_comments_count_per_post", sa.Integer(), nullable=False),
        sa.Column("limit_child_comments_per_comment", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id"],
            ["gathers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "danek_instagram_comments_gathers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id_list", base_models.JSONEncodedValue(), nullable=False),
        sa.Column("limit_comments_per_post", sa.Integer(), nullable=False),
        sa.Column("limit_child_comments_per_comment", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id"],
            ["gathers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade for 7ce037bb58a4."""
    op.drop_table("danek_instagram_posts_gathers")
    op.drop_table("danek_instagram_comments_gathers")
