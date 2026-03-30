"""remove FK from profile_snapshots - preserve history across profile rewrites

profile_snapshots is an append-only audit log. The FK to profiles.id was
causing all snapshot history to be CASCADE-deleted whenever the profiles
table is wiped and rewritten each scrape run.

profile_latest_posts keeps its CASCADE FK since it is throwaway data that
is fully re-created on every run.

Revision ID: 0007
Revises: 0006
Create Date: 2026-03-28
"""
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the CASCADE FK on profile_snapshots — make profile_id a plain
    # text column so snapshot rows survive when profiles are cleared/rewritten.
    # The column still holds the Instagram user ID for manual joins.
    op.drop_constraint(
        "profile_snapshots_profile_id_fkey",
        "profile_snapshots",
        type_="foreignkey",
    )


def downgrade() -> None:
    op.create_foreign_key(
        None, "profile_snapshots", "profiles", ["profile_id"], ["id"], ondelete="CASCADE"
    )
