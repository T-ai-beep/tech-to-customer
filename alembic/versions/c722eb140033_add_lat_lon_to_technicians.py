"""add lat lon to technicians

Revision ID: c722eb140033
Revises: 041bbedd5c6b
Create Date: 2025-11-29 08:39:43.216526

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c722eb140033'
down_revision: Union[str, Sequence[str], None] = '041bbedd5c6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
