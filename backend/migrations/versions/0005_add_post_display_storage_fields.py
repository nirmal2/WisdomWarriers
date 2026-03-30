"""add post display storage fields

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-28
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("display_storage_path", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("display_storage_url", sa.Text(), nullable=True))

    op.add_column("post_snapshots", sa.Column("display_storage_path", sa.Text(), nullable=True))
    op.add_column("post_snapshots", sa.Column("display_storage_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("post_snapshots", "display_storage_url")
    op.drop_column("post_snapshots", "display_storage_path")

    op.drop_column("posts", "display_storage_url")
    op.drop_column("posts", "display_storage_path")
