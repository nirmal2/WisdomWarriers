"""drop legacy posts and normalized post tables

Revision ID: 0024
Revises: 0023
Create Date: 2026-04-30
"""
from alembic import op

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS post_tagged_users")
    op.execute("DROP TABLE IF EXISTS post_mentions")
    op.execute("DROP TABLE IF EXISTS post_hashtags")
    op.execute("DROP TABLE IF EXISTS posts")


def downgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id text primary key,
            source_post_id text,
            short_code text,
            owner_username text,
            owner_full_name text,
            owner_id text,
            owner_profile_pic_url text,
            location_name text,
            location_id text,
            url text not null,
            timestamp timestamptz,
            likes_count integer default 0,
            video_play_count integer default 0,
            video_view_count integer default 0,
            type text,
            video_url text,
            audio_url text,
            video_duration double precision,
            display_url text,
            display_storage_path text,
            display_storage_url text,
            dimensions_height integer,
            dimensions_width integer,
            is_comments_disabled boolean default false,
            alt text,
            caption text,
            product_type text,
            input_url text,
            comments_count integer default 0,
            first_comment text,
            latest_comments jsonb default '[]'::jsonb,
            images jsonb default '[]'::jsonb,
            child_posts jsonb default '[]'::jsonb,
            music_info jsonb default '{}'::jsonb,
            hashtags jsonb default '[]'::jsonb,
            mentions jsonb default '[]'::jsonb,
            tagged_users jsonb default '[]'::jsonb,
            coauthor_producers jsonb default '[]'::jsonb,
            is_pinned boolean default false,
            profile_id text,
            scraped_at timestamptz,
            period_label text not null,
            run_id integer,
            embedding vector(1536)
        )
        """
    )

    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_post_url_period ON posts (url, period_label)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_posts_owner_username ON posts (owner_username)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_posts_profile_id ON posts (profile_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_posts_period_label ON posts (period_label)")

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
