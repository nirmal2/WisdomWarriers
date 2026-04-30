"""add tagged_users to post_snapshots

Revision ID: 0020
Revises: 0019
Create Date: 2026-04-28
"""
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE post_snapshots
        ADD COLUMN IF NOT EXISTS tagged_users jsonb DEFAULT '[]'::jsonb
        """
    )


#def downgrade() -> None:
  #  op.execute("ALTER TABLE post_snapshots DROP COLUMN IF EXISTS tagged_users")
