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
            cp.comments_count,
            cp.video_view_count,
            cp.video_play_count,
            cp.caption,
            cp.hashtags,
            cp.display_url,
            cp.display_storage_url,
            cp.url,
            cp.is_pinned,
            cp.run_id,
            cp.scraped_at,
            pr.followers_count,
            pr.is_verified,
            pr.is_business_account,
            sp.grade,
            sp.category,
            ROUND(
                (cp.likes_count + cp.comments_count)::numeric
                / NULLIF(pr.followers_count, 0) * 100,
                2
            ) AS engagement_rate,
            (cp.likes_count + cp.comments_count) AS total_interactions
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
    #    Note: This function now looks for embeddings on post_snapshots
    #    (future: may need dedicated embeddings table)
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
                    (cp.likes_count + cp.comments_count)::numeric
                    / NULLIF(pr.followers_count, 0) * 100,
                    2
                ) AS engagement_rate,
                1 - (ps.embedding <=> query_embedding) AS similarity
            FROM current_posts cp
            LEFT JOIN post_snapshots ps ON ps.url = cp.url
            LEFT JOIN profiles pr ON pr.username = cp.owner_username
            WHERE
                ps.embedding IS NOT NULL
                AND (filter_username IS NULL OR cp.owner_username = filter_username)
            ORDER BY ps.embedding <=> query_embedding
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
