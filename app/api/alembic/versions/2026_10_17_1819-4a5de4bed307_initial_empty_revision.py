"""Initial empty revision: the starting point later migrations build on.

Creates no tables. Running it adds Alembic's own "alembic_version" table,
which records which migration the database is at.

Revision ID: 4a5de4bed307
Revises: 
Create Date: 2026-10-17 18:19:31.642099

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '4a5de4bed307'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
