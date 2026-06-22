"""Rename classes_dict to classes.

Revision ID: d406c721af32
Revises: 7c6392dd7767
Create Date: 2024-10-15 08:45:59.192384

This revision was done before there was any data in classes_dict. This is why it can add a column
with nullable=False.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from phiphi.api import base_models

# revision identifiers, used by Alembic.
revision: str = "d406c721af32"
down_revision: Union[str, None] = "7c6392dd7767"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for d406c721af32."""
    op.add_column(
        "classifier_versions",
        sa.Column("classes", base_models.JSONEncodedValue(), nullable=False),
    )
    op.drop_column("classifier_versions", "classes_dict")


def downgrade() -> None:
    """Downgrade for d406c721af32."""
    op.add_column(
        "classifier_versions",
        sa.Column("classes_dict", sa.VARCHAR(), autoincrement=False, nullable=False),
    )
    op.drop_column("classifier_versions", "classes")
