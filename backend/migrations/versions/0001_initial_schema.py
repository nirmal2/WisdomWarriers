"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-27
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "profiles",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("username", sa.Text, nullable=False, unique=True),
        sa.Column("url", sa.Text),
        sa.Column("full_name", sa.Text),
        sa.Column("biography", sa.Text),
        sa.Column("followers_count", sa.Integer, default=0),
        sa.Column("follows_count", sa.Integer, default=0),
        sa.Column("posts_count", sa.Integer, default=0),
        sa.Column("igtv_video_count", sa.Integer, default=0),
        sa.Column("has_channel", sa.Boolean, default=False),
        sa.Column("highlight_reel_count", sa.Integer, default=0),
        sa.Column("is_business_account", sa.Boolean, default=False),
        sa.Column("joined_recently", sa.Boolean, default=False),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("is_private", sa.Boolean, default=False),
        sa.Column("business_category", sa.Text),
        sa.Column("profile_pic_url", sa.Text),
        sa.Column("profile_pic_url_hd", sa.Text),
        sa.Column("external_url", sa.Text),
        sa.Column("fbid", sa.Text),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("embedding", Vector(1536)),
    )

    op.create_table(
        "scrape_runs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("scraper_type", sa.Text, nullable=False),
        sa.Column("trigger", sa.Text, nullable=False),
        sa.Column("schedule_id", sa.Integer),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.Text, default="running"),
        sa.Column("embedding_status", sa.Text, default="pending"),
        sa.Column("profiles_requested", sa.Integer, default=0),
        sa.Column("items_fetched", sa.Integer, default=0),
        sa.Column("error_message", sa.Text),
        sa.Column("embedding_error_message", sa.Text),
    )

    op.create_table(
        "profile_snapshots",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Text, sa.ForeignKey("profiles.id"), nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("followers_count", sa.Integer, default=0),
        sa.Column("follows_count", sa.Integer, default=0),
        sa.Column("posts_count", sa.Integer, default=0),
        sa.Column("period_label", sa.Text, nullable=False),
        sa.Column("run_id", sa.Integer, sa.ForeignKey("scrape_runs.id")),
    )

    op.create_table(
        "posts",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("owner_username", sa.Text),
        sa.Column("owner_full_name", sa.Text),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True)),
        sa.Column("likes_count", sa.Integer, default=0),
        sa.Column("video_play_count", sa.Integer, default=0),
        sa.Column("input_url", sa.Text),
        sa.Column("hashtags", sa.dialects.postgresql.JSONB),
        sa.Column("coauthor_producers", sa.dialects.postgresql.JSONB),
        sa.Column("scraped_at", sa.DateTime(timezone=True)),
        sa.Column("period_label", sa.Text, nullable=False),
        sa.Column("run_id", sa.Integer, sa.ForeignKey("scrape_runs.id")),
        sa.Column("embedding", Vector(1536)),
        sa.UniqueConstraint("url", "period_label", name="uq_post_url_period"),
    )

    op.create_table(
        "schedules",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("scraper_type", sa.Text, nullable=False),
        sa.Column("frequency", sa.Text, nullable=False),
        sa.Column("cron_expr", sa.Text),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("batch_mode", sa.Boolean, default=False),
        sa.Column("results_limit", sa.Integer, default=27),
        sa.Column("only_posts_newer_than", sa.Text),
        sa.Column("actor_id", sa.Text),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("next_run_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("ix_profiles_username", "profiles", ["username"])
    op.create_index("ix_profile_snapshots_profile_id", "profile_snapshots", ["profile_id"])
    op.create_index("ix_profile_snapshots_period_label", "profile_snapshots", ["period_label"])
    op.create_index("ix_posts_owner_username", "posts", ["owner_username"])
    op.create_index("ix_posts_period_label", "posts", ["period_label"])


def downgrade() -> None:
    op.drop_table("schedules")
    op.drop_table("posts")
    op.drop_table("profile_snapshots")
    op.drop_table("scrape_runs")
    op.drop_table("profiles")
