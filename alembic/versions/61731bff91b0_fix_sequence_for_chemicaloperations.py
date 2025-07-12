"""Fix sequence for chemicaloperations

Revision ID: 84d98641c948
Revises: <предыдущая_ревизия>
Create Date: 2025-07-12 12:05:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61731bff91b0'
down_revision: Union[str, Sequence[str], None] = '785b67ff517f'
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