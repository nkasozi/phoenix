"""Add index class_id to intermediatory_class_to_keyword_configs.

Revision ID: 2471145c028e
Revises: 973f495eefb9
Create Date: 2024-10-16 08:25:42.817828

"""

from typing import Sequence, Union

from alembic import op

revision: str = "2471145c028e"
down_revision: Union[str, None] = "973f495eefb9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 2471145c028e."""
    op.create_index(
        "ix_intermediatory_class_to_keyword_configs_class_id",
        "intermediatory_class_to_keyword_configs",
        ["class_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade for 2471145c028e."""
    op.drop_index(
        "ix_intermediatory_class_to_keyword_configs_class_id",
        table_name="intermediatory_class_to_keyword_configs",
    )
