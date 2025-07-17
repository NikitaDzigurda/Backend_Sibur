"""Fix sequence for percent chemical elements

Revision ID: ad265911badf
Revises: 7efe5ebe3d0a
Create Date: 2025-07-17 22:51:19.212000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad265911badf'
down_revision: Union[str, Sequence[str], None] = '7efe5ebe3d0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix broken sequence for chemicalobjects table."""
    op.execute("""
        SELECT setval(
            'percentchemicalelements_id_seq',
            COALESCE((SELECT MAX(id) FROM percentchemicalelements), 1)
        );
    """)


def downgrade() -> None:
    """No downgrade needed for sequence fix."""
    # Можно сбросить sequence обратно в 1, но это может привести к ошибкам
    pass
