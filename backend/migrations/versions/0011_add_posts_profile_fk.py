"""add profile_id fk to posts

Revision ID: 0011
Revises: 0010
Create Date: 2026-03-28
"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("profile_id", sa.Text(), nullable=True))
    op.create_index("posts_profile_id_idx", "posts", ["profile_id"], unique=False)
    op.create_foreign_key(
        "posts_profile_id_fkey",
        "posts",
        "profiles",
        ["profile_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Backfill existing rows by owner_username when profile exists.
    op.execute(
        """
        UPDATE posts p
        SET profile_id = pr.id
        FROM profiles pr
        WHERE lower(pr.username) = lower(p.owner_username)
        """
    )


def downgrade() -> None:
    op.drop_constraint("posts_profile_id_fkey", "posts", type_="foreignkey")
    op.drop_index("posts_profile_id_idx", table_name="posts")
    op.drop_column("posts", "profile_id")
