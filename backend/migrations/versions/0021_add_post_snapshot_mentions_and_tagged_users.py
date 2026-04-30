"""add post_snapshot_mentions and post_snapshot_tagged_users tables

Revision ID: 0021
Revises: 0020
Create Date: 2026-04-28
"""
from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS post_snapshot_mentions (
            id serial primary key,
            snapshot_id integer not null references post_snapshots (id) on delete cascade,
            post_id text not null,
            run_id integer references scrape_runs (id),
            period_label text not null,
            owner_username text,
            mention_raw text not null,
            mention_norm text not null,
            created_at timestamptz default now(),
            constraint uq_post_snapshot_mention unique (snapshot_id, mention_norm)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS post_snapshot_tagged_users (
            id serial primary key,
            snapshot_id integer not null references post_snapshots (id) on delete cascade,
            post_id text not null,
            run_id integer references scrape_runs (id),
            period_label text not null,
            owner_username text,
            tagged_user_raw text not null,
            tagged_user_norm text not null,
            created_at timestamptz default now(),
            constraint uq_post_snapshot_tagged_user unique (snapshot_id, tagged_user_norm)
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_mentions_snapshot_id_idx ON post_snapshot_mentions (snapshot_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_mentions_post_id_idx ON post_snapshot_mentions (post_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_mentions_run_id_idx ON post_snapshot_mentions (run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_mentions_period_label_idx ON post_snapshot_mentions (period_label)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_mentions_owner_username_idx ON post_snapshot_mentions (owner_username)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_mentions_mention_norm_idx ON post_snapshot_mentions (mention_norm)")

    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_tagged_users_snapshot_id_idx ON post_snapshot_tagged_users (snapshot_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_tagged_users_post_id_idx ON post_snapshot_tagged_users (post_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_tagged_users_run_id_idx ON post_snapshot_tagged_users (run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_tagged_users_period_label_idx ON post_snapshot_tagged_users (period_label)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_tagged_users_owner_username_idx ON post_snapshot_tagged_users (owner_username)")
    op.execute("CREATE INDEX IF NOT EXISTS post_snapshot_tagged_users_tagged_user_norm_idx ON post_snapshot_tagged_users (tagged_user_norm)")

    op.execute(
        """
        INSERT INTO post_snapshot_mentions (
            snapshot_id,
            post_id,
            run_id,
            period_label,
            owner_username,
            mention_raw,
            mention_norm
        )
        WITH expanded AS (
            SELECT
                ps.id AS snapshot_id,
                ps.post_id,
                ps.run_id,
                ps.period_label,
                ps.owner_username,
                trim(m.tag) AS mention_raw,
                lower(ltrim(trim(m.tag), '@')) AS mention_norm
            FROM post_snapshots ps
            CROSS JOIN LATERAL jsonb_array_elements_text(coalesce(ps.mentions, '[]'::jsonb)) AS m(tag)
            WHERE trim(m.tag) <> ''
        ), dedup AS (
            SELECT
                snapshot_id,
                post_id,
                run_id,
                period_label,
                owner_username,
                mention_norm,
                min(mention_raw) AS mention_raw
            FROM expanded
            WHERE mention_norm <> ''
            GROUP BY snapshot_id, post_id, run_id, period_label, owner_username, mention_norm
        )
        SELECT snapshot_id, post_id, run_id, period_label, owner_username, mention_raw, mention_norm
        FROM dedup
        ON CONFLICT (snapshot_id, mention_norm)
        DO UPDATE SET mention_raw = EXCLUDED.mention_raw
        """
    )

    op.execute(
        """
        INSERT INTO post_snapshot_tagged_users (
            snapshot_id,
            post_id,
            run_id,
            period_label,
            owner_username,
            tagged_user_raw,
            tagged_user_norm
        )
        WITH expanded AS (
            SELECT
                ps.id AS snapshot_id,
                ps.post_id,
                ps.run_id,
                ps.period_label,
                ps.owner_username,
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
            FROM post_snapshots ps
            LEFT JOIN posts p ON p.id = ps.post_id
            CROSS JOIN LATERAL jsonb_array_elements(
                coalesce(
                    nullif(ps.tagged_users, '[]'::jsonb),
                    p.tagged_users,
                    '[]'::jsonb
                )
            ) AS t(item)
        ), dedup AS (
            SELECT
                snapshot_id,
                post_id,
                run_id,
                period_label,
                owner_username,
                tagged_user_norm,
                min(tagged_user_raw) AS tagged_user_raw
            FROM expanded
            WHERE tagged_user_raw <> ''
              AND tagged_user_norm <> ''
            GROUP BY snapshot_id, post_id, run_id, period_label, owner_username, tagged_user_norm
        )
        SELECT snapshot_id, post_id, run_id, period_label, owner_username, tagged_user_raw, tagged_user_norm
        FROM dedup
        ON CONFLICT (snapshot_id, tagged_user_norm)
        DO UPDATE SET tagged_user_raw = EXCLUDED.tagged_user_raw
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS post_snapshot_tagged_users")
    op.execute("DROP TABLE IF EXISTS post_snapshot_mentions")
