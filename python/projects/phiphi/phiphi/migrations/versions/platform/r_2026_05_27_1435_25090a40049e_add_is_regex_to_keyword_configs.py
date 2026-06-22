"""Add is regex to keyword configs.

Revision ID: 25090a40049e
Revises: 869965e2ceda
Create Date: 2026-05-27 14:35:08.777375

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "25090a40049e"
down_revision: Union[str, None] = "869965e2ceda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 25090a40049e."""
    op.add_column(
        "intermediatory_class_to_keyword_configs",
        sa.Column("is_regex", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade for 25090a40049e."""
    op.drop_column("intermediatory_class_to_keyword_configs", "is_regex")
