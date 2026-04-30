"""rebuild analytics views to use post_snapshots instead of posts table

Revision ID: 0025
Revises: 0024
Create Date: 2026-04-30
"""
from alembic import op

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================================
    # 0. Add missing columns to post_snapshots (if they don't exist)
    # ============================================================
    op.execute(
        """
        ALTER TABLE post_snapshots
        ADD COLUMN IF NOT EXISTS comments_count INT DEFAULT 0,
        ADD COLUMN IF NOT EXISTS video_view_count INT DEFAULT 0,
        ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS embedding vector(1536) DEFAULT NULL;
        """
    )

    # ============================================================
    # 0.5. Rebuild current_posts view to include new columns from post_snapshots
    # ============================================================
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
            ranked.comments_count,
            ranked.video_view_count,
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
            ranked.is_pinned,
            ranked.embedding,
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

    # ============================================================
    # 1. Rebuild post_engagement VIEW to use post_snapshots + current_posts
    # ============================================================
    op.execute(
        """
        CREATE OR REPLACE VIEW post_engagement AS
        SELECT
            cp.id,
            cp.url AS short_code,
            cp.owner_username,
            pr.id AS owner_id,
            cp.timestamp,
            cp.period_label,
            cp.type,
            cp.product_type,
            cp.likes_count,
            COALESCE(cp.comments_count, 0) AS comments_count,
            COALESCE(cp.video_view_count, 0) AS video_view_count,
            cp.video_play_count,
            cp.caption,
            cp.hashtags,
            cp.display_url,
            cp.display_storage_url,
            cp.url,
            COALESCE(cp.is_pinned, FALSE) AS is_pinned,
            cp.run_id,
            cp.scraped_at,
            pr.followers_count,
            pr.is_verified,
            pr.is_business_account,
            sp.grade,
            sp.category,
            ROUND(
                (cp.likes_count + COALESCE(cp.comments_count, 0))::numeric
                / NULLIF(pr.followers_count, 0) * 100,
                2
            ) AS engagement_rate,
            (cp.likes_count + COALESCE(cp.comments_count, 0)) AS total_interactions
        FROM current_posts cp
        LEFT JOIN profiles pr ON pr.username = cp.owner_username
        LEFT JOIN scrape_profiles sp ON sp.username = cp.owner_username
        """
    )

    # ============================================================
    # 2. Rebuild post_engagement_history VIEW to use post_snapshots
    # ============================================================
    op.execute(
        """
        CREATE OR REPLACE VIEW post_engagement_history AS
        SELECT
            ps.post_id,
            ps.url AS short_code,
            ps.owner_username,
            ps.period_label,
            ps.scraped_at,
            ps.likes_count,
            ps.type,
            ps.display_storage_url,
            ps.caption,
            ps.hashtags,
            ps.run_id,
            pr.followers_count,
            ROUND(
                ps.likes_count::numeric / NULLIF(pr.followers_count, 0) * 100,
                2
            ) AS likes_rate
        FROM post_snapshots ps
        LEFT JOIN profiles pr ON pr.username = ps.owner_username
        ORDER BY ps.scraped_at
        """
    )

    # ============================================================
    # 3. Rebuild search_similar_posts function to use current_posts
    # ============================================================
    op.execute(
        """
        CREATE OR REPLACE FUNCTION search_similar_posts(
            query_embedding vector(1536),
            filter_username text DEFAULT NULL,
            result_limit int DEFAULT 10
        )
        RETURNS TABLE (
            id text,
            short_code text,
            owner_username text,
            caption text,
            display_url text,
            likes_count int,
            engagement_rate numeric,
            similarity float
        )
        LANGUAGE sql STABLE
        AS $$
            SELECT
                cp.id,
                cp.url AS short_code,
                cp.owner_username,
                cp.caption,
                cp.display_storage_url,
                cp.likes_count,
                ROUND(
                    (cp.likes_count + COALESCE(cp.comments_count, 0))::numeric
                    / NULLIF(pr.followers_count, 0) * 100,
                    2
                ) AS engagement_rate,
                (1 - (cp.embedding <=> query_embedding))::float AS similarity
            FROM current_posts cp
            LEFT JOIN profiles pr ON pr.username = cp.owner_username
            WHERE
                cp.embedding IS NOT NULL
                AND (filter_username IS NULL OR cp.owner_username = filter_username)
            ORDER BY cp.embedding <=> query_embedding
            LIMIT result_limit
        $$
        """
    )

    # ============================================================
    # 4. Now safe to drop posts table (views have been rebuilt)
    # ============================================================
    op.execute(
        """
        DROP TABLE IF EXISTS posts CASCADE
        """
    )


def downgrade() -> None:
    # Downgrade would require recreating the posts table and views
    # For now, we'll just document that downgrade is not supported
    # as we've migrated to a snapshot-first architecture
    pass
