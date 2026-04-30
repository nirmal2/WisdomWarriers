"""create current_posts view derived from latest post snapshots

Revision ID: 0023
Revises: 0022
Create Date: 2026-04-30
"""
from alembic import op

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE VIEW current_posts AS
        SELECT
            ranked.post_id AS id,
            ranked.run_id,
            ranked.owner_username,
            ranked.url,
            ranked.timestamp,
            ranked.likes_count,
            ranked.video_play_count,
            ranked.type,
            ranked.video_url,
            ranked.display_url,
            ranked.display_storage_path,
            ranked.display_storage_url,
            ranked.caption,
            ranked.product_type,
            ranked.input_url,
            ranked.hashtags,
            ranked.mentions,
            ranked.tagged_users,
            ranked.coauthor_producers,
            ranked.period_label,
            ranked.scraped_at,
            ranked.id AS snapshot_id
        FROM (
            SELECT
                ps.*,
                row_number() OVER (
                    PARTITION BY ps.url
                    ORDER BY ps.scraped_at DESC NULLS LAST, ps.id DESC
                ) AS rn
            FROM post_snapshots ps
        ) AS ranked
        WHERE ranked.rn = 1
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS current_posts")
