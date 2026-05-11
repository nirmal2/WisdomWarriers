"""add apify run metadata columns to scrape_runs

Revision ID: 0028
Revises: 0027
Create Date: 2026-05-11
"""
from alembic import op
import sqlalchemy as sa


revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scrape_runs", sa.Column("apify_posts_actor_id", sa.Text(), nullable=True))
    op.add_column("scrape_runs", sa.Column("apify_posts_run_id", sa.Text(), nullable=True))
    op.add_column("scrape_runs", sa.Column("apify_posts_dataset_id", sa.Text(), nullable=True))
    op.add_column("scrape_runs", sa.Column("apify_posts_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("scrape_runs", sa.Column("apify_posts_finished_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("scrape_runs", sa.Column("apify_posts_status", sa.Text(), nullable=True))

    op.add_column("scrape_runs", sa.Column("apify_profiles_actor_id", sa.Text(), nullable=True))
    op.add_column("scrape_runs", sa.Column("apify_profiles_run_id", sa.Text(), nullable=True))
    op.add_column("scrape_runs", sa.Column("apify_profiles_dataset_id", sa.Text(), nullable=True))
    op.add_column("scrape_runs", sa.Column("apify_profiles_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("scrape_runs", sa.Column("apify_profiles_finished_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("scrape_runs", sa.Column("apify_profiles_status", sa.Text(), nullable=True))

    op.add_column("scrape_runs", sa.Column("apify_stage_history", sa.Text(), nullable=True))

    op.execute(
        """
        CREATE OR REPLACE VIEW scrape_run_summary AS
        SELECT
            sr.id,
            sr.scraper_type,
            sr.trigger,
            sr.started_at,
            sr.finished_at,
            sr.status,
            sr.embedding_status,
            sr.items_fetched,
            sr.profiles_requested,
            sr.error_message,
            sr.embedding_error_message,
            s.name AS schedule_name,
            s.frequency AS schedule_frequency,
            extract(epoch from (sr.finished_at - sr.started_at)) AS duration_seconds,
            sr.apify_posts_run_id,
            sr.apify_posts_dataset_id,
            sr.apify_posts_status,
            sr.apify_profiles_run_id,
            sr.apify_profiles_dataset_id,
            sr.apify_profiles_status
        FROM scrape_runs sr
        LEFT JOIN schedules s ON s.id = sr.schedule_id
        ORDER BY sr.started_at DESC
        """
    )


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE VIEW scrape_run_summary AS
        SELECT
            sr.id,
            sr.scraper_type,
            sr.trigger,
            sr.started_at,
            sr.finished_at,
            sr.status,
            sr.embedding_status,
            sr.items_fetched,
            sr.profiles_requested,
            sr.error_message,
            sr.embedding_error_message,
            s.name AS schedule_name,
            s.frequency AS schedule_frequency,
            extract(epoch from (sr.finished_at - sr.started_at)) AS duration_seconds
        FROM scrape_runs sr
        LEFT JOIN schedules s ON s.id = sr.schedule_id
        ORDER BY sr.started_at DESC
        """
    )

    op.drop_column("scrape_runs", "apify_stage_history")

    op.drop_column("scrape_runs", "apify_profiles_status")
    op.drop_column("scrape_runs", "apify_profiles_finished_at")
    op.drop_column("scrape_runs", "apify_profiles_started_at")
    op.drop_column("scrape_runs", "apify_profiles_dataset_id")
    op.drop_column("scrape_runs", "apify_profiles_run_id")
    op.drop_column("scrape_runs", "apify_profiles_actor_id")

    op.drop_column("scrape_runs", "apify_posts_status")
    op.drop_column("scrape_runs", "apify_posts_finished_at")
    op.drop_column("scrape_runs", "apify_posts_started_at")
    op.drop_column("scrape_runs", "apify_posts_dataset_id")
    op.drop_column("scrape_runs", "apify_posts_run_id")
    op.drop_column("scrape_runs", "apify_posts_actor_id")
