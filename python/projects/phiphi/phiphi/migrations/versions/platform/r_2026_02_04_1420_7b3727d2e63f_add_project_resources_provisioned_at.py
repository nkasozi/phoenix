"""Add project_resources_provisioned_at column to projects.

Revision ID: 7b3727d2e63f
Revises: 5f6a8c26ff98
Create Date: 2026-02-04 14:20:56.087435

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7b3727d2e63f"
down_revision: Union[str, None] = "5f6a8c26ff98"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 7b3727d2e63f."""
    op.add_column(
        "projects",
        sa.Column("project_resources_provisioned_at", sa.DateTime(), nullable=True),
    )
    op.execute(
        """
        UPDATE projects
        SET project_resources_provisioned_at = created_at
        WHERE project_resources_provisioned_at IS NULL;
        """
    )


def downgrade() -> None:
    """Downgrade for 7b3727d2e63f."""
    op.drop_column("projects", "project_resources_provisioned_at")
