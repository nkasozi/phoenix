"""Remove platform and data_type columns from gather_batches.

Revision ID: 3099ccfdde06
Revises: 24f9f2229bc0
Create Date: 2024-12-05 11:05:43.949697

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3099ccfdde06"
down_revision: Union[str, None] = "24f9f2229bc0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 3099ccfdde06."""
    op.drop_column("gather_batches", "platform")
    op.drop_column("gather_batches", "data_type")


def downgrade() -> None:
    """Downgrade for 3099ccfdde06.

    This downgrade does not create the columns with the same name as the upgrade because the
    it is not possible to create non-nullable columns. Furthermore it is not possible (or easy)
    to get the platform and data_type from the child type.

    The downgrade is used in the alembic migration check in the integration test.
    """
    op.add_column("gather_batches", sa.Column("data_type", sa.VARCHAR(), nullable=True))
    op.add_column("gather_batches", sa.Column("platform", sa.VARCHAR(), nullable=True))
