"""add_content_to_posts

Revision ID: b17a83991380
Revises: 7e1815261c52
Create Date: 2026-03-28 20:19:07.035122

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b17a83991380'
down_revision: Union[str, Sequence[str], None] = '7e1815261c52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('posts', sa.Column('content', sa.String(), nullable=False))
    pass


def downgrade() -> None:
    op.drop_column('posts', 'content')
    pass
