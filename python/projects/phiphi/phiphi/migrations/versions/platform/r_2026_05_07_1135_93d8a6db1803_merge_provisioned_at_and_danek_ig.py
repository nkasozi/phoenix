"""merge_provisioned_at_and_danek_ig.

Revision ID: 93d8a6db1803
Revises: 7b3727d2e63f, 7ce037bb58a4
Create Date: 2026-05-07 11:35:09.961780

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "93d8a6db1803"
down_revision: Union[str, Sequence[str], None] = ("7b3727d2e63f", "7ce037bb58a4")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for 93d8a6db1803."""
    pass


def downgrade() -> None:
    """Downgrade for 93d8a6db1803."""
    pass
