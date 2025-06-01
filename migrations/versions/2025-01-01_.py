"""change user id to bigint

Revision ID: 70a785983b12
Revises: 70a785983b11
Create Date: 2024-05-15 02:26:29.045980

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70a785983b12'
down_revision: Union[str, None] = '70a785983b11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert the id column from string to bigint
    op.execute('ALTER TABLE users ALTER COLUMN id TYPE BIGINT USING id::BIGINT')


def downgrade() -> None:
    # Convert the id column back to string
    op.execute('ALTER TABLE users ALTER COLUMN id TYPE VARCHAR USING id::VARCHAR')