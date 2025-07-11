"""Fix sequence for chemicalobjects

Revision ID: 83c97530b837
Revises: 0f7c3c55e6ea
Create Date: 2025-07-10 10:46:09.486476
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83c97530b837'
down_revision: Union[str, Sequence[str], None] = '0f7c3c55e6ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix broken sequence for chemicalobjects table."""
    op.execute("""
        SELECT setval(
            'chemicalobjects_id_seq',
            COALESCE((SELECT MAX(id) FROM chemicalobjects), 1)
        );
    """)


def downgrade() -> None:
    """No downgrade needed for sequence fix."""
    # Можно сбросить sequence обратно в 1, но это может привести к ошибкам
    pass
