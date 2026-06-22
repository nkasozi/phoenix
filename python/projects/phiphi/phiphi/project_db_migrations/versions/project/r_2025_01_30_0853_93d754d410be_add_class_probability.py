"""Add class_probability.

Revision ID: 93d754d410be
Revises: e05994386cfa
Create Date: 2025-01-30 08:53:42.419024

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "93d754d410be"
down_revision: Union[str, None] = "e05994386cfa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 93d754d410be."""
    conn = op.get_bind()
    # It would seem that the server_default is not working correctly with the FLOAT64 type as
    # sa.add_column( requires a server_default to be a string but the query ALTER TABLE ... FLOAT64
    # DEFAULT '1.0' NOT NULL is invalid
    # Doing the raw sql instead
    # It is also not possible to create a not nullable (REQUIRED) column:
    # https://cloud.google.com/bigquery/docs/managing-table-schemas#add_an_empty_column
    # Not possible to create a column with a default has to be done in three separate queries
    conn.execute(
        sa.text("ALTER TABLE `classified_messages` ADD COLUMN `class_probability` FLOAT64")
    )
    conn.execute(
        sa.text(
            "ALTER TABLE `classified_messages` ALTER COLUMN `class_probability` SET DEFAULT 1.0"
        )
    )
    conn.execute(sa.text("UPDATE `classified_messages` SET `class_probability` = 1.0 WHERE TRUE"))


def downgrade() -> None:
    """Downgrade for 93d754d410be."""
    op.drop_column("classified_messages", "class_probability")
