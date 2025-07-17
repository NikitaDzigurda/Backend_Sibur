"""Fix2 sequence for chemicaloperations

Revision ID: 0c32f4a2f8d7
Revises: 61731bff91b0
Create Date: 2025-07-17 22:41:08.416695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c32f4a2f8d7'
down_revision: Union[str, Sequence[str], None] = '61731bff91b0'
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