"""update_posts_table

Revision ID: 5ad2da6c8b04
Revises: e71a163f2858
Create Date: 2026-03-28 20:31:36.227914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '5ad2da6c8b04'
down_revision: Union[str, Sequence[str], None] = 'e71a163f2858'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'posts',
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    op.add_column(
        'posts',
        sa.Column('published', sa.Boolean(), server_default=sa.text('TRUE'), nullable=False)
    )
    op.add_column(
        'posts',
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False,)
    )
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('posts', 'published')
    op.drop_column('posts', 'created_at')
    op.drop_column('posts', 'owner_id')
    
    pass
