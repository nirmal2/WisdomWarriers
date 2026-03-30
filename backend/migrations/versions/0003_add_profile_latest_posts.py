"""add profile_latest_posts table

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profile_latest_posts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Text(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("scrape_runs.id"), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("post_id", sa.Text(), nullable=True),
        sa.Column("short_code", sa.Text(), nullable=True),
        sa.Column("post_type", sa.Text(), nullable=True),
        sa.Column("product_type", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("hashtags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("mentions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("comments_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("video_view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_username", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.Text(), nullable=True),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_comments_disabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index("ix_profile_latest_posts_profile_id", "profile_latest_posts", ["profile_id"])
    op.create_index("ix_profile_latest_posts_run_id", "profile_latest_posts", ["run_id"])
    op.create_index("ix_profile_latest_posts_timestamp", "profile_latest_posts", ["timestamp"])


def downgrade() -> None:
    op.drop_index("ix_profile_latest_posts_timestamp", table_name="profile_latest_posts")
    op.drop_index("ix_profile_latest_posts_run_id", table_name="profile_latest_posts")
    op.drop_index("ix_profile_latest_posts_profile_id", table_name="profile_latest_posts")
    op.drop_table("profile_latest_posts")
