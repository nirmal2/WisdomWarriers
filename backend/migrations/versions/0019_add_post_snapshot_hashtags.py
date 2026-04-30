"""add post_snapshot_hashtags table

Revision ID: 0019
Revises: 0018
Create Date: 2026-04-28
"""
from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS post_snapshot_hashtags (
            id serial primary key,
            snapshot_id integer not null references post_snapshots (id) on delete cascade,
            post_id text not null,
            run_id integer references scrape_runs (id),
            period_label text not null,
            owner_username text,
            hashtag_raw text not null,
            hashtag_norm text not null,
            created_at timestamptz default now(),
            constraint uq_post_snapshot_hashtag unique (snapshot_id, hashtag_norm)
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_hashtags_snapshot_id_idx ON post_snapshot_hashtags (snapshot_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_hashtags_post_id_idx ON post_snapshot_hashtags (post_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_hashtags_run_id_idx ON post_snapshot_hashtags (run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_hashtags_period_label_idx ON post_snapshot_hashtags (period_label)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_hashtags_owner_username_idx ON post_snapshot_hashtags (owner_username)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_hashtags_hashtag_norm_idx ON post_snapshot_hashtags (hashtag_norm)")

    op.execute(
        """
        INSERT INTO post_snapshot_hashtags (
            snapshot_id,
            post_id,
            run_id,
            period_label,
            owner_username,
            hashtag_raw,
            hashtag_norm
        )
        WITH expanded AS (
            SELECT
                ps.id AS snapshot_id,
                ps.post_id,
                ps.run_id,
                ps.period_label,
                ps.owner_username,
                trim(h.tag) AS hashtag_raw,
                lower(ltrim(trim(h.tag), '#')) AS hashtag_norm
            FROM post_snapshots ps
            CROSS JOIN LATERAL jsonb_array_elements_text(coalesce(ps.hashtags, '[]'::jsonb)) AS h(tag)
            WHERE trim(h.tag) <> ''
        ), dedup AS (
            SELECT
                snapshot_id,
                post_id,
                run_id,
                period_label,
                owner_username,
                hashtag_norm,
                min(hashtag_raw) AS hashtag_raw
            FROM expanded
            WHERE hashtag_norm <> ''
            GROUP BY snapshot_id, post_id, run_id, period_label, owner_username, hashtag_norm
        )
        SELECT
            snapshot_id,
            post_id,
            run_id,
            period_label,
            owner_username,
            hashtag_raw,
            hashtag_norm
        FROM dedup
        ON CONFLICT (snapshot_id, hashtag_norm)
        DO UPDATE SET hashtag_raw = EXCLUDED.hashtag_raw
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS post_snapshot_hashtags")
