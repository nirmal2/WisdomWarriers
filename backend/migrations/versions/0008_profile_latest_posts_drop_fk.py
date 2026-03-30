"""remove FK from profile_latest_posts - accumulate as snapshots per run

profile_latest_posts is now an append-only snapshot log keyed by run_id.
Rows are never deleted — each scrape run appends its data.
Removing the FK to profiles.id lets these rows survive profile table rewrites.

Revision ID: 0008
Revises: 0007
Create Date: 2026-03-28
"""
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the CASCADE FK — profile_latest_posts rows must survive
    # when the profiles table is wiped and rewritten each scrape run.
    # profile_id is kept as a plain text column for manual joins.
    op.drop_constraint(
        "profile_latest_posts_profile_id_fkey",
        "profile_latest_posts",
        type_="foreignkey",
    )


def downgrade() -> None:
    op.create_foreign_key(
        "profile_latest_posts_profile_id_fkey",
        "profile_latest_posts", "profiles",
        ["profile_id"], ["id"],
        ondelete="CASCADE",
    )
