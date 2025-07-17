"""Fix3 sequence for chemicaloperations

Revision ID: 7efe5ebe3d0a
Revises: 0c32f4a2f8d7
Create Date: 2025-07-17 22:47:40.319336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7efe5ebe3d0a'
down_revision: Union[str, Sequence[str], None] = '0c32f4a2f8d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix broken sequence for chemicaloperations table."""
    op.execute("""
        SELECT setval(
            'chemicaloperations_id_seq',
            COALESCE((SELECT MAX(id) + 1 FROM chemicaloperations), 1)
        );
    """)


def downgrade() -> None:
    """No downgrade needed for sequence fix."""
    # Сброс последовательности не рекомендуется, так как может привести к конфликтам ID
    pass
