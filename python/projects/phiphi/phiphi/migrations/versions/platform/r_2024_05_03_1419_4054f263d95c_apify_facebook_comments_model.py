"""apify_facebook_comments_model.

Revision ID: 4054f263d95c
Revises: df1988f5395d
Create Date: 2024-05-03 14:19:47.327842

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from phiphi.api import base_models

# revision identifiers, used by Alembic.
revision: str = "4054f263d95c"
down_revision: Union[str, None] = "6d4b2c6a304c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE_NAME = "apify_facebook_comments_gathers"


def upgrade() -> None:
    """Upgrade for 4054f263d95c."""
    op.create_table(
        TABLE_NAME,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("limit_comments_per_post", sa.Integer(), nullable=False),
        sa.Column("post_url_list", base_models.JSONEncodedValue(), nullable=False),
        sa.Column("sort_comments_by", sa.String(), nullable=False),
        sa.Column("include_comment_replies", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id"],
            ["gathers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade for 4054f263d95c."""
    op.drop_table(TABLE_NAME)
