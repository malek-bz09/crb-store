"""soft delete products

Revision ID: b7e1c2d9a4f3
Revises: f347e64bea25
Create Date: 2026-10-31 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b7e1c2d9a4f3'
down_revision: str | Sequence[str] | None = 'f347e64bea25'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('products', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('products', 'deleted_at')
