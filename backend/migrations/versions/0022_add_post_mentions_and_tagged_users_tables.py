"""add post_hashtags, post_mentions and post_tagged_users tables

Revision ID: 0022
Revises: 0021
Create Date: 2026-04-28
"""
from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS post_hashtags (
            id serial primary key,
            post_id text not null references posts (id) on delete cascade,
            run_id integer references scrape_runs (id),
            period_label text not null,
            owner_username text,
            hashtag_raw text not null,
            hashtag_norm text not null,
            created_at timestamptz default now(),
            constraint uq_post_hashtag unique (post_id, hashtag_norm)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS post_mentions (
            id serial primary key,
            post_id text not null references posts (id) on delete cascade,
            run_id integer references scrape_runs (id),
            period_label text not null,
            owner_username text,
            mention_raw text not null,
            mention_norm text not null,
            created_at timestamptz default now(),
            constraint uq_post_mention unique (post_id, mention_norm)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS post_tagged_users (
            id serial primary key,
            post_id text not null references posts (id) on delete cascade,
            run_id integer references scrape_runs (id),
            period_label text not null,
            owner_username text,
            tagged_user_raw text not null,
            tagged_user_norm text not null,
            created_at timestamptz default now(),
            constraint uq_post_tagged_user unique (post_id, tagged_user_norm)
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS post_hashtags_post_id_idx ON post_hashtags (post_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_hashtags_run_id_idx ON post_hashtags (run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_hashtags_period_label_idx ON post_hashtags (period_label)")
    op.execute("CREATE INDEX IF NOT EXISTS post_hashtags_owner_username_idx ON post_hashtags (owner_username)")
    op.execute("CREATE INDEX IF NOT EXISTS post_hashtags_hashtag_norm_idx ON post_hashtags (hashtag_norm)")

    op.execute("CREATE INDEX IF NOT EXISTS post_mentions_post_id_idx ON post_mentions (post_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_mentions_run_id_idx ON post_mentions (run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_mentions_period_label_idx ON post_mentions (period_label)")
    op.execute("CREATE INDEX IF NOT EXISTS post_mentions_owner_username_idx ON post_mentions (owner_username)")
    op.execute("CREATE INDEX IF NOT EXISTS post_mentions_mention_norm_idx ON post_mentions (mention_norm)")

    op.execute("CREATE INDEX IF NOT EXISTS post_tagged_users_post_id_idx ON post_tagged_users (post_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_tagged_users_run_id_idx ON post_tagged_users (run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_tagged_users_period_label_idx ON post_tagged_users (period_label)")
    op.execute("CREATE INDEX IF NOT EXISTS post_tagged_users_owner_username_idx ON post_tagged_users (owner_username)")
    op.execute("CREATE INDEX IF NOT EXISTS post_tagged_users_tagged_user_norm_idx ON post_tagged_users (tagged_user_norm)")

    op.execute(
        """
        INSERT INTO post_hashtags (
            post_id,
            run_id,
            period_label,
            owner_username,
            hashtag_raw,
            hashtag_norm
        )
        WITH expanded AS (
            SELECT
                p.id AS post_id,
                p.run_id,
                p.period_label,
                p.owner_username,
                trim(h.tag) AS hashtag_raw,
                lower(ltrim(trim(h.tag), '#')) AS hashtag_norm
            FROM posts p
            CROSS JOIN LATERAL jsonb_array_elements_text(coalesce(p.hashtags, '[]'::jsonb)) AS h(tag)
            WHERE trim(h.tag) <> ''
        ), dedup AS (
            SELECT
                post_id,
                run_id,
                period_label,
                owner_username,
                hashtag_norm,
                min(hashtag_raw) AS hashtag_raw
            FROM expanded
            WHERE hashtag_norm <> ''
            GROUP BY post_id, run_id, period_label, owner_username, hashtag_norm
        )
        SELECT post_id, run_id, period_label, owner_username, hashtag_raw, hashtag_norm
        FROM dedup
        ON CONFLICT (post_id, hashtag_norm)
        DO UPDATE SET hashtag_raw = EXCLUDED.hashtag_raw
        """
    )

    op.execute(
        """
        INSERT INTO post_mentions (
            post_id,
            run_id,
            period_label,
            owner_username,
            mention_raw,
            mention_norm
        )
        WITH expanded AS (
            SELECT
                p.id AS post_id,
                p.run_id,
                p.period_label,
                p.owner_username,
                trim(m.tag) AS mention_raw,
                lower(ltrim(trim(m.tag), '@')) AS mention_norm
            FROM posts p
            CROSS JOIN LATERAL jsonb_array_elements_text(coalesce(p.mentions, '[]'::jsonb)) AS m(tag)
            WHERE trim(m.tag) <> ''
        ), dedup AS (
            SELECT
                post_id,
                run_id,
                period_label,
                owner_username,
                mention_norm,
                min(mention_raw) AS mention_raw
            FROM expanded
            WHERE mention_norm <> ''
            GROUP BY post_id, run_id, period_label, owner_username, mention_norm
        )
        SELECT post_id, run_id, period_label, owner_username, mention_raw, mention_norm
        FROM dedup
        ON CONFLICT (post_id, mention_norm)
        DO UPDATE SET mention_raw = EXCLUDED.mention_raw
        """
    )

    op.execute(
        """
        INSERT INTO post_tagged_users (
            post_id,
            run_id,
            period_label,
            owner_username,
            tagged_user_raw,
            tagged_user_norm
        )
        WITH expanded AS (
            SELECT
                p.id AS post_id,
                p.run_id,
                p.period_label,
                p.owner_username,
                trim(
                    coalesce(
                        t.item ->> 'username',
                        t.item ->> 'userName',
                        t.item ->> 'ownerUsername',
                        t.item ->> 'handle',
                        t.item #>> '{}'
                    )
                ) AS tagged_user_raw,
                lower(
                    ltrim(
                        trim(
                            coalesce(
                                t.item ->> 'username',
                                t.item ->> 'userName',
                                t.item ->> 'ownerUsername',
                                t.item ->> 'handle',
                                t.item #>> '{}'
                            )
                        ),
                        '@'
                    )
                ) AS tagged_user_norm
            FROM posts p
            CROSS JOIN LATERAL jsonb_array_elements(coalesce(p.tagged_users, '[]'::jsonb)) AS t(item)
        ), dedup AS (
            SELECT
                post_id,
                run_id,
                period_label,
                owner_username,
                tagged_user_norm,
                min(tagged_user_raw) AS tagged_user_raw
            FROM expanded
            WHERE tagged_user_raw <> ''
              AND tagged_user_norm <> ''
            GROUP BY post_id, run_id, period_label, owner_username, tagged_user_norm
        )
        SELECT post_id, run_id, period_label, owner_username, tagged_user_raw, tagged_user_norm
        FROM dedup
        ON CONFLICT (post_id, tagged_user_norm)
        DO UPDATE SET tagged_user_raw = EXCLUDED.tagged_user_raw
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS post_tagged_users")
    op.execute("DROP TABLE IF EXISTS post_mentions")
    op.execute("DROP TABLE IF EXISTS post_hashtags")
