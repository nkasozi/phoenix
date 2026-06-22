"""Add soft deleted to projects.

Revision ID: abb72fed04ae
Revises: 76ac5b340772
Create Date: 2024-06-12 10:06:45.186202

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "abb72fed04ae"
down_revision: Union[str, None] = "76ac5b340772"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for abb72fed04ae."""
    op.add_column("projects", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.create_index("idx_deleted_at", "projects", ["deleted_at"], unique=False)
    op.create_index("idx_project_id_deteted_at", "projects", ["id", "deleted_at"], unique=False)


def downgrade() -> None:
    """Downgrade for abb72fed04ae."""
    op.drop_index("idx_project_id_deteted_at", table_name="projects")
    op.drop_index("idx_deleted_at", table_name="projects")
    op.drop_column("projects", "deleted_at")
