"""cleanup_tech_latlon

Revision ID: 8e8f896e85e4
Revises: 9813f0662005
Create Date: 2025-11-29 14:26:30.934337

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e8f896e85e4'
down_revision: Union[str, Sequence[str], None] = '9813f0662005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
