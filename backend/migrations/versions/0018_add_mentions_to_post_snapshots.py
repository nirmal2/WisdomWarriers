"""add mentions to post_snapshots

Revision ID: 0018
Revises: 0017
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE post_snapshots
        ADD COLUMN IF NOT EXISTS mentions jsonb DEFAULT '[]'::jsonb
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE post_snapshots DROP COLUMN IF EXISTS mentions")
