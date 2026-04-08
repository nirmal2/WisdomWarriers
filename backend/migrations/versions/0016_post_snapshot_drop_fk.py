"""remove FK from post_snapshots - preserve history across post table resets

post_snapshots is an append-only audit log. The FK to posts.id prevents the
canonical posts table from being cleared before each scrape run, which blocks
fresh post ingestion even though snapshot history should be retained.

Revision ID: 0016
Revises: 0015
Create Date: 2026-04-08
"""
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "post_snapshots_post_id_fkey",
        "post_snapshots",
        type_="foreignkey",
    )


def downgrade() -> None:
    op.create_foreign_key(
        "post_snapshots_post_id_fkey",
        "post_snapshots",
        "posts",
        ["post_id"],
        ["id"],
    )
