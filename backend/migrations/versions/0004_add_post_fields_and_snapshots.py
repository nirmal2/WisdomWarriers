"""add post fields and post snapshots table

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("type", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("video_url", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("display_url", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("caption", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("product_type", sa.Text(), nullable=True))

    op.create_table(
        "post_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.Text(), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("scrape_runs.id"), nullable=True),
        sa.Column("owner_username", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("likes_count", sa.Integer(), nullable=True),
        sa.Column("video_play_count", sa.Integer(), nullable=True),
        sa.Column("type", sa.Text(), nullable=True),
        sa.Column("video_url", sa.Text(), nullable=True),
        sa.Column("display_url", sa.Text(), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("product_type", sa.Text(), nullable=True),
        sa.Column("input_url", sa.Text(), nullable=True),
        sa.Column("hashtags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("coauthor_producers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("period_label", sa.Text(), nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index("ix_post_snapshots_post_id", "post_snapshots", ["post_id"])
    op.create_index("ix_post_snapshots_run_id", "post_snapshots", ["run_id"])
    op.create_index("ix_post_snapshots_owner_username", "post_snapshots", ["owner_username"])
    op.create_index("ix_post_snapshots_url", "post_snapshots", ["url"])
    op.create_index("ix_post_snapshots_period_label", "post_snapshots", ["period_label"])


def downgrade() -> None:
    op.drop_index("ix_post_snapshots_period_label", table_name="post_snapshots")
    op.drop_index("ix_post_snapshots_url", table_name="post_snapshots")
    op.drop_index("ix_post_snapshots_owner_username", table_name="post_snapshots")
    op.drop_index("ix_post_snapshots_run_id", table_name="post_snapshots")
    op.drop_index("ix_post_snapshots_post_id", table_name="post_snapshots")
    op.drop_table("post_snapshots")

    op.drop_column("posts", "product_type")
    op.drop_column("posts", "caption")
    op.drop_column("posts", "display_url")
    op.drop_column("posts", "video_url")
    op.drop_column("posts", "type")
