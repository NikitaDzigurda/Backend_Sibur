"""Fix sequence for user profile

Revision ID: c982b338c99d
Revises: ad265911badf
Create Date: 2025-07-17 22:57:04.576244

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c982b338c99d'
down_revision: Union[str, Sequence[str], None] = 'ad265911badf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix broken sequence for chemicalobjects table."""
    op.execute("""
        SELECT setval(
            'userprofile_id_seq',
            COALESCE((SELECT MAX(id) FROM userprofile), 1)
        );
    """)


def downgrade() -> None:
    """No downgrade needed for sequence fix."""
    # Можно сбросить sequence обратно в 1, но это может привести к ошибкам
    pass
