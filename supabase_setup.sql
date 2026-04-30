-- ============================================================
-- Supabase Setup Script for insta-analytics
-- Run this in the Supabase SQL Editor (supabase.com -> project -> SQL Editor)
-- ============================================================

-- 1. Enable pgvector extension (required for embeddings)
create extension if not exists vector;

-- ============================================================
-- 2. scrape_runs (no dependencies)
-- ============================================================
create table if not exists scrape_runs (
    id               serial primary key,
    scraper_type     text not null,          -- 'posts' | 'profiles'
    trigger          text not null,          -- 'manual' | 'scheduled'
    schedule_id      integer,
    started_at       timestamptz default now(),
    finished_at      timestamptz,
    status           text default 'running', -- 'running' | 'completed' | 'failed'
    embedding_status text default 'pending', -- 'pending' | 'completed' | 'failed' | 'skipped' | 'not_started'
    profiles_requested integer default 0,
    items_fetched    integer default 0,
    error_message    text,
    embedding_error_message text
);

-- ============================================================
-- 3. schedules (no dependencies)
-- ============================================================
create table if not exists schedules (
    id                    serial primary key,
    name                  text not null,
    scraper_type          text not null,      -- 'posts' | 'profiles'
    frequency             text not null,      -- 'daily' | 'weekly' | 'monthly' | 'on_demand'
    cron_expr             text,
    is_active             boolean default true,
    batch_mode            boolean default false,
    results_limit         integer default 27,
    only_posts_newer_than text,
    actor_id              text,
    last_run_at           timestamptz,
    next_run_at           timestamptz,
    created_at            timestamptz default now()
);

-- ============================================================
-- 4. profiles (no dependencies)
-- ============================================================
create table if not exists profiles (
    id                   text primary key,   -- Instagram numeric ID
    username             text unique not null,
    url                  text,
    full_name            text,
    biography            text,
    followers_count      integer default 0,
    follows_count        integer default 0,
    posts_count          integer default 0,
    igtv_video_count     integer default 0,
    has_channel          boolean default false,
    highlight_reel_count integer default 0,
    is_business_account  boolean default false,
    joined_recently      boolean default false,
    is_verified          boolean default false,
    is_private           boolean default false,
    business_category    text,
    profile_pic_url      text,
    profile_pic_url_hd   text,
    external_url         text,
    fbid                 text,
    first_seen_at        timestamptz default now(),
    last_updated_at      timestamptz default now(),
    embedding            vector(1536)
);

create index if not exists profiles_username_idx on profiles (username);

-- ============================================================
-- 5. posts (depends on scrape_runs)
-- ============================================================
create table if not exists posts (
    id                  text primary key,   -- sha256(url + period_label)
    source_post_id      text,
    short_code          text,
    owner_username      text,
    owner_full_name     text,
    owner_id            text,
    owner_profile_pic_url text,
    location_name       text,
    location_id         text,
    url                 text not null,
    timestamp           timestamptz,
    likes_count         integer default 0,
    video_play_count    integer default 0,
    video_view_count    integer default 0,
    type                text,
    video_url           text,
    audio_url           text,
    video_duration      double precision,
    display_url         text,
    display_storage_path text,
    display_storage_url text,
    dimensions_height   integer,
    dimensions_width    integer,
    is_comments_disabled boolean default false,
    alt                 text,
    caption             text,
    product_type        text,
    input_url           text,
    comments_count      integer default 0,
    first_comment       text,
    latest_comments     jsonb default '[]',
    images              jsonb default '[]',
    child_posts         jsonb default '[]',
    music_info          jsonb default '{}'::jsonb,
    hashtags            jsonb default '[]',
    mentions            jsonb default '[]',
    tagged_users        jsonb default '[]',
    coauthor_producers  jsonb default '[]',
    is_pinned           boolean default false,
    profile_id          text references profiles (id) on delete set null,
    scraped_at          timestamptz,
    period_label        text not null,
    run_id              integer references scrape_runs (id),
    embedding           vector(1536),
    constraint uq_post_url_period unique (url, period_label)
);

create index if not exists posts_owner_username_idx on posts (owner_username);
create index if not exists posts_profile_id_idx on posts (profile_id);
create index if not exists posts_period_label_idx   on posts (period_label);

-- ============================================================
-- 6. profile_snapshots (depends on profiles + scrape_runs)
-- ============================================================
create table if not exists profile_snapshots (
    id               serial primary key,
    profile_id       text not null,   -- soft ref, no FK so history survives profile rewrites
    scraped_at       timestamptz default now(),
    followers_count  integer default 0,
    follows_count    integer default 0,
    posts_count      integer default 0,
    period_label     text not null,
    run_id           integer references scrape_runs (id)
);

create index if not exists profile_snapshots_profile_id_idx  on profile_snapshots (profile_id);
create index if not exists profile_snapshots_period_label_idx on profile_snapshots (period_label);

-- ============================================================
-- 7. scrape_profiles (manual/scheduled scrape input source)
-- ============================================================
create table if not exists scrape_profiles (
    id         serial primary key,
    username   text not null unique,
    category   text,
    grade      text,
    position   integer not null,
    created_at timestamptz default now()
);

alter table if exists scrape_profiles
    add column if not exists category text,
    add column if not exists grade text;

alter table if exists scrape_profiles
    drop constraint if exists scrape_profiles_category_check;

alter table if exists scrape_profiles
    add constraint scrape_profiles_category_check
    check (category is null or category in ('Dedicated', 'In-house influencer'));

alter table if exists scrape_profiles
    drop constraint if exists scrape_profiles_grade_check;

alter table if exists scrape_profiles
    add constraint scrape_profiles_grade_check
    check (grade is null or grade in ('A', 'B', 'C', 'D', 'E', 'Inactive'));

create index if not exists scrape_profiles_username_idx on scrape_profiles (username);

-- ============================================================
-- 8. profile_latest_posts (from Apify profile latestPosts[])
-- ============================================================
create table if not exists profile_latest_posts (
    id                   serial primary key,
    profile_id           text not null,   -- soft ref, no FK so rows survive profile rewrites
    run_id               integer references scrape_runs (id),
    position             integer not null,
    post_id              text,
    short_code           text,
    post_type            text,
    product_type         text,
    url                  text not null,
    caption              text,
    hashtags             jsonb default '[]',
    mentions             jsonb default '[]',
    comments_count       integer default 0,
    likes_count          integer default 0,
    video_view_count     integer default 0,
    timestamp            timestamptz,
    owner_username       text,
    owner_id             text,
    is_pinned            boolean default false,
    is_comments_disabled boolean default false,
    raw_payload          jsonb default '{}'::jsonb,
    scraped_at           timestamptz default now()
);

create index if not exists profile_latest_posts_profile_id_idx on profile_latest_posts (profile_id);
create index if not exists profile_latest_posts_run_id_idx on profile_latest_posts (run_id);
create index if not exists profile_latest_posts_timestamp_idx on profile_latest_posts (timestamp);

-- ============================================================
-- 9. post_snapshots (historical post data per scrape run)
-- ============================================================
create table if not exists post_snapshots (
    id                   serial primary key,
    post_id              text not null,
    run_id               integer references scrape_runs (id),
    owner_username       text,
    url                  text not null,
    timestamp            timestamptz,
    likes_count          integer default 0,
    video_play_count     integer default 0,
    type                 text,
    video_url            text,
    display_url          text,
    display_storage_path text,
    display_storage_url  text,
    caption              text,
    product_type         text,
    input_url            text,
    hashtags             jsonb default '[]',
    mentions             jsonb default '[]',
    tagged_users         jsonb default '[]',
    coauthor_producers   jsonb default '[]',
    period_label         text not null,
    scraped_at           timestamptz default now()
);

create index if not exists post_snapshots_post_id_idx on post_snapshots (post_id);
create index if not exists post_snapshots_run_id_idx on post_snapshots (run_id);
create index if not exists post_snapshots_owner_username_idx on post_snapshots (owner_username);
create index if not exists post_snapshots_url_idx on post_snapshots (url);
create index if not exists post_snapshots_period_label_idx on post_snapshots (period_label);

-- ============================================================
-- 10. post_snapshot_hashtags (normalized hashtags per snapshot)
-- ============================================================
create table if not exists post_snapshot_hashtags (
    id             serial primary key,
    snapshot_id    integer not null references post_snapshots (id) on delete cascade,
    post_id        text not null,
    run_id         integer references scrape_runs (id),
    period_label   text not null,
    owner_username text,
    hashtag_raw    text not null,
    hashtag_norm   text not null,
    created_at     timestamptz default now(),
    constraint uq_post_snapshot_hashtag unique (snapshot_id, hashtag_norm)
);

create index if not exists post_snapshot_hashtags_snapshot_id_idx on post_snapshot_hashtags (snapshot_id);
create index if not exists post_snapshot_hashtags_post_id_idx on post_snapshot_hashtags (post_id);
create index if not exists post_snapshot_hashtags_run_id_idx on post_snapshot_hashtags (run_id);
create index if not exists post_snapshot_hashtags_period_label_idx on post_snapshot_hashtags (period_label);
create index if not exists post_snapshot_hashtags_owner_username_idx on post_snapshot_hashtags (owner_username);
create index if not exists post_snapshot_hashtags_hashtag_norm_idx on post_snapshot_hashtags (hashtag_norm);

-- ============================================================
-- 11. post_snapshot_mentions (normalized mentions per snapshot)
-- ============================================================
create table if not exists post_snapshot_mentions (
    id             serial primary key,
    snapshot_id    integer not null references post_snapshots (id) on delete cascade,
    post_id        text not null,
    run_id         integer references scrape_runs (id),
    period_label   text not null,
    owner_username text,
    mention_raw    text not null,
    mention_norm   text not null,
    created_at     timestamptz default now(),
    constraint uq_post_snapshot_mention unique (snapshot_id, mention_norm)
);

create index if not exists post_snapshot_mentions_snapshot_id_idx on post_snapshot_mentions (snapshot_id);
create index if not exists post_snapshot_mentions_post_id_idx on post_snapshot_mentions (post_id);
create index if not exists post_snapshot_mentions_run_id_idx on post_snapshot_mentions (run_id);
create index if not exists post_snapshot_mentions_period_label_idx on post_snapshot_mentions (period_label);
create index if not exists post_snapshot_mentions_owner_username_idx on post_snapshot_mentions (owner_username);
create index if not exists post_snapshot_mentions_mention_norm_idx on post_snapshot_mentions (mention_norm);

-- ============================================================
-- 12. post_snapshot_tagged_users (normalized tagged users)
-- ============================================================
create table if not exists post_snapshot_tagged_users (
    id               serial primary key,
    snapshot_id      integer not null references post_snapshots (id) on delete cascade,
    post_id          text not null,
    run_id           integer references scrape_runs (id),
    period_label     text not null,
    owner_username   text,
    tagged_user_raw  text not null,
    tagged_user_norm text not null,
    created_at       timestamptz default now(),
    constraint uq_post_snapshot_tagged_user unique (snapshot_id, tagged_user_norm)
);

create index if not exists post_snapshot_tagged_users_snapshot_id_idx on post_snapshot_tagged_users (snapshot_id);
create index if not exists post_snapshot_tagged_users_post_id_idx on post_snapshot_tagged_users (post_id);
create index if not exists post_snapshot_tagged_users_run_id_idx on post_snapshot_tagged_users (run_id);
create index if not exists post_snapshot_tagged_users_period_label_idx on post_snapshot_tagged_users (period_label);
create index if not exists post_snapshot_tagged_users_owner_username_idx on post_snapshot_tagged_users (owner_username);
create index if not exists post_snapshot_tagged_users_tagged_user_norm_idx on post_snapshot_tagged_users (tagged_user_norm);

-- ============================================================
-- 13. post_hashtags (normalized hashtags per current post)
-- ============================================================
create table if not exists post_hashtags (
    id             serial primary key,
    post_id        text not null references posts (id) on delete cascade,
    run_id         integer references scrape_runs (id),
    period_label   text not null,
    owner_username text,
    hashtag_raw    text not null,
    hashtag_norm   text not null,
    created_at     timestamptz default now(),
    constraint uq_post_hashtag unique (post_id, hashtag_norm)
);

create index if not exists post_hashtags_post_id_idx on post_hashtags (post_id);
create index if not exists post_hashtags_run_id_idx on post_hashtags (run_id);
create index if not exists post_hashtags_period_label_idx on post_hashtags (period_label);
create index if not exists post_hashtags_owner_username_idx on post_hashtags (owner_username);
create index if not exists post_hashtags_hashtag_norm_idx on post_hashtags (hashtag_norm);

-- ============================================================
-- 14. post_mentions (normalized mentions per current post)
-- ============================================================
create table if not exists post_mentions (
    id             serial primary key,
    post_id        text not null references posts (id) on delete cascade,
    run_id         integer references scrape_runs (id),
    period_label   text not null,
    owner_username text,
    mention_raw    text not null,
    mention_norm   text not null,
    created_at     timestamptz default now(),
    constraint uq_post_mention unique (post_id, mention_norm)
);

create index if not exists post_mentions_post_id_idx on post_mentions (post_id);
create index if not exists post_mentions_run_id_idx on post_mentions (run_id);
create index if not exists post_mentions_period_label_idx on post_mentions (period_label);
create index if not exists post_mentions_owner_username_idx on post_mentions (owner_username);
create index if not exists post_mentions_mention_norm_idx on post_mentions (mention_norm);

-- ============================================================
-- 15. post_tagged_users (normalized tagged users per current post)
-- ============================================================
create table if not exists post_tagged_users (
    id               serial primary key,
    post_id          text not null references posts (id) on delete cascade,
    run_id           integer references scrape_runs (id),
    period_label     text not null,
    owner_username   text,
    tagged_user_raw  text not null,
    tagged_user_norm text not null,
    created_at       timestamptz default now(),
    constraint uq_post_tagged_user unique (post_id, tagged_user_norm)
);

create index if not exists post_tagged_users_post_id_idx on post_tagged_users (post_id);
create index if not exists post_tagged_users_run_id_idx on post_tagged_users (run_id);
create index if not exists post_tagged_users_period_label_idx on post_tagged_users (period_label);
create index if not exists post_tagged_users_owner_username_idx on post_tagged_users (owner_username);
create index if not exists post_tagged_users_tagged_user_norm_idx on post_tagged_users (tagged_user_norm);
