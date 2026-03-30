"""profile FK cascade delete

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-28
"""
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # profile_snapshots: re-add FK with ON DELETE CASCADE so clearing profiles
    # also clears their snapshots (snapshots are re-created on next scrape run)
    op.drop_constraint("profile_snapshots_profile_id_fkey", "profile_snapshots", type_="foreignkey")
    op.create_foreign_key(
        None, "profile_snapshots", "profiles", ["profile_id"], ["id"], ondelete="CASCADE"
    )

    # profile_latest_posts: same – re-created each run anyway
    op.drop_constraint("profile_latest_posts_profile_id_fkey", "profile_latest_posts", type_="foreignkey")
    op.create_foreign_key(
        None, "profile_latest_posts", "profiles", ["profile_id"], ["id"], ondelete="CASCADE"
    )


def downgrade() -> None:
    op.drop_constraint(None, "profile_latest_posts", type_="foreignkey")
    op.create_foreign_key(
        "profile_latest_posts_profile_id_fkey", "profile_latest_posts", "profiles", ["profile_id"], ["id"]
    )

    op.drop_constraint(None, "profile_snapshots", type_="foreignkey")
    op.create_foreign_key(
        "profile_snapshots_profile_id_fkey", "profile_snapshots", "profiles", ["profile_id"], ["id"]
    )
