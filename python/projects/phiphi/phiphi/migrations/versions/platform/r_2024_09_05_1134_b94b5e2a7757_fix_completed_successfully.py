"""Fix completed successfully.

Revision ID: b94b5e2a7757
Revises: d31116c6bea5
Create Date: 2024-09-05 11:34:17.009210

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b94b5e2a7757"
down_revision: Union[str, None] = "d31116c6bea5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade for b94b5e2a7757."""
    op.execute(
        """
        UPDATE job_runs
        SET status = 'completed_successfully'
        WHERE status = 'completed_sucessfully';
        """
    )


def downgrade() -> None:
    """Downgrade for b94b5e2a7757."""
    op.execute(
        """
        UPDATE job_runs
        SET status = 'completed_sucessfully'
        WHERE status = 'completed_successfully';
        """
    )
