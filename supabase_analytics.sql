-- ============================================================
-- Supabase Analytics Layer for insta-analytics
-- Run this in the Supabase SQL Editor after supabase_setup.sql
-- ============================================================


-- ============================================================
-- 1. post_engagement VIEW
--    Joins posts + profiles to compute engagement rate.
--    Use this as the base for all post-level analytics queries.
-- ============================================================
create or replace view post_engagement as
select
  p.id,
  p.short_code,
  p.owner_username,
  p.owner_id,
  p.timestamp,
  p.period_label,
  p.type,
  p.product_type,
  p.likes_count,
  p.comments_count,
  p.video_view_count,
  p.video_play_count,
  p.caption,
  p.hashtags,
  p.display_url,
  p.display_storage_url,
  p.url,
  p.is_pinned,
  p.run_id,
  p.scraped_at,
  pr.followers_count,
  pr.is_verified,
  pr.is_business_account,
  sp.grade,
  sp.category,
  round(
    (p.likes_count + p.comments_count)::numeric
    / nullif(pr.followers_count, 0) * 100,
    2
  ) as engagement_rate,
  (p.likes_count + p.comments_count) as total_interactions
from posts p
left join profiles pr on pr.id = p.profile_id
left join scrape_profiles sp on sp.username = p.owner_username;


-- ============================================================
-- 2. profile_follower_growth VIEW
--    Month-over-month follower delta per profile.
--    Use for the follower growth chart in the Profiles page.
-- ============================================================
create or replace view profile_follower_growth as
select
  ps.profile_id,
  pr.username,
  pr.full_name,
  sp.grade,
  sp.category,
  ps.period_label,
  ps.scraped_at,
  ps.followers_count,
  ps.follows_count,
  ps.posts_count,
  ps.followers_count - lag(ps.followers_count) over (
    partition by ps.profile_id order by ps.scraped_at
  ) as follower_delta,
  round(
    (ps.followers_count - lag(ps.followers_count) over (
      partition by ps.profile_id order by ps.scraped_at
    ))::numeric
    / nullif(lag(ps.followers_count) over (
      partition by ps.profile_id order by ps.scraped_at
    ), 0) * 100,
    2
  ) as follower_delta_pct
from profile_snapshots ps
left join profiles pr on pr.id = ps.profile_id
left join scrape_profiles sp on sp.username = pr.username;


-- ============================================================
-- 3. post_engagement_history VIEW
--    Tracks how a single post's engagement changed across scrape runs.
--    Join on short_code (stable identity) not posts.id (per-period).
--    Use for engagement-over-time charts per post.
-- ============================================================
create or replace view post_engagement_history as
select
  ps.post_id,
  p.short_code,
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
  round(
    ps.likes_count::numeric / nullif(pr.followers_count, 0) * 100,
    2
  ) as likes_rate
from post_snapshots ps
join posts p on p.id = ps.post_id
left join profiles pr on pr.username = ps.owner_username
order by ps.scraped_at;


-- ============================================================
-- 4. account_monthly_summary VIEW
--    Per-account per-period aggregate stats.
--    Use for overview cards and trend charts.
-- ============================================================
create or replace view account_monthly_summary as
select
  owner_username,
  period_label,
  grade,
  category,
  count(*) as posts_count,
  round(avg(likes_count)) as avg_likes,
  round(avg(comments_count)) as avg_comments,
  round(avg(video_view_count)) as avg_video_views,
  sum(likes_count) as total_likes,
  sum(comments_count) as total_comments,
  max(likes_count) as peak_likes,
  max(comments_count) as peak_comments,
  round(avg(engagement_rate), 2) as avg_engagement_rate,
  max(engagement_rate) as peak_engagement_rate,
  count(*) filter (where type = 'Image') as image_count,
  count(*) filter (where type = 'Video') as video_count,
  count(*) filter (where type = 'Sidecar') as carousel_count,
  mode() within group (order by to_char(timestamp, 'Day')) as most_active_day
from post_engagement
group by owner_username, period_label, grade, category;


-- ============================================================
-- 5. hashtag_performance MATERIALIZED VIEW
--    Unnests jsonb hashtag arrays for aggregated hashtag analytics.
--    Refresh after each scrape run completes.
-- ============================================================
drop materialized view if exists hashtag_performance;

create materialized view hashtag_performance as
select
  lower(h.tag) as tag,
  pe.owner_username,
  pe.period_label,
  pe.grade,
  pe.category,
  count(*) as post_count,
  round(avg(pe.likes_count)) as avg_likes,
  round(avg(pe.comments_count)) as avg_comments,
  round(avg(pe.engagement_rate), 2) as avg_engagement_rate,
  sum(pe.likes_count) as total_likes,
  max(pe.engagement_rate) as peak_engagement_rate
from post_engagement pe,
  jsonb_array_elements_text(pe.hashtags) as h(tag)
where pe.hashtags != '[]'::jsonb
group by lower(h.tag), pe.owner_username, pe.period_label, pe.grade, pe.category;

create index if not exists hashtag_performance_tag_idx on hashtag_performance (tag);
create index if not exists hashtag_performance_owner_username_idx on hashtag_performance (owner_username);
create index if not exists hashtag_performance_period_label_idx on hashtag_performance (period_label);
create index if not exists hashtag_performance_avg_engagement_rate_idx on hashtag_performance (avg_engagement_rate desc);


-- ============================================================
-- 6. posting_time_heatmap MATERIALIZED VIEW
--    Day-of-week x hour-of-day grid with avg engagement.
--    Use for the best-time-to-post heatmap UI.
--    Refresh after each scrape run completes.
-- ============================================================
drop materialized view if exists posting_time_heatmap;

create materialized view posting_time_heatmap as
select
  owner_username,
  grade,
  category,
  extract(dow from timestamp) as day_of_week,
  to_char(timestamp, 'Dy') as day_name,
  extract(hour from timestamp) as hour_of_day,
  count(*) as post_count,
  round(avg(likes_count)) as avg_likes,
  round(avg(comments_count)) as avg_comments,
  round(avg(engagement_rate), 2) as avg_engagement_rate
from post_engagement
where timestamp is not null
group by
  owner_username,
  grade,
  category,
  extract(dow from timestamp),
  to_char(timestamp, 'Dy'),
  extract(hour from timestamp);

create index if not exists posting_time_heatmap_owner_username_idx on posting_time_heatmap (owner_username);
create index if not exists posting_time_heatmap_avg_engagement_rate_idx on posting_time_heatmap (avg_engagement_rate desc);


-- ============================================================
-- 7. grade_benchmarks VIEW
--    Compares avg engagement across scrape_profiles grades.
--    Use for grade benchmarking panels.
-- ============================================================
create or replace view grade_benchmarks as
select
  sp.grade,
  sp.category,
  count(distinct pe.owner_username) as account_count,
  round(avg(pe.engagement_rate), 2) as avg_engagement_rate,
  round(avg(pe.likes_count)) as avg_likes,
  round(avg(pe.comments_count)) as avg_comments,
  round(avg(pr.followers_count)) as avg_followers,
  pe.period_label
from post_engagement pe
join scrape_profiles sp on sp.username = pe.owner_username
join profiles pr on pr.username = pe.owner_username
group by sp.grade, sp.category, pe.period_label;


-- ============================================================
-- 8. scrape_run_summary VIEW
--    Enriches scrape_runs with schedule name for monitoring pages.
-- ============================================================
create or replace view scrape_run_summary as
select
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
  s.name as schedule_name,
  s.frequency as schedule_frequency,
  extract(epoch from (sr.finished_at - sr.started_at)) as duration_seconds
from scrape_runs sr
left join schedules s on s.id = sr.schedule_id
order by sr.started_at desc;


-- ============================================================
-- 9. Helper: refresh all materialized views
--    Call this at the end of every scrape pipeline run.
--    Use non-concurrent refresh here because Postgres functions
--    execute inside a transaction block.
-- ============================================================
create or replace function refresh_analytics_views()
returns void
language plpgsql
security definer
as $$
begin
  refresh materialized view hashtag_performance;
  refresh materialized view posting_time_heatmap;
end;
$$;

grant execute on function refresh_analytics_views() to service_role;


-- ============================================================
-- 10. Helper: semantic post search
--     Call from the app with:
--     select * from search_similar_posts($1, $2, $3)
-- ============================================================
create or replace function search_similar_posts(
  query_embedding vector(1536),
  filter_username text default null,
  result_limit int default 10
)
returns table (
  id text,
  short_code text,
  owner_username text,
  caption text,
  display_url text,
  likes_count int,
  engagement_rate numeric,
  similarity float
)
language sql stable
as $$
  select
    p.id,
    p.short_code,
    p.owner_username,
    p.caption,
    p.display_storage_url,
    p.likes_count,
    round(
      (p.likes_count + p.comments_count)::numeric
      / nullif(pr.followers_count, 0) * 100,
      2
    ) as engagement_rate,
    1 - (p.embedding <=> query_embedding) as similarity
  from posts p
  left join profiles pr on pr.id = p.profile_id
  where
    p.embedding is not null
    and (filter_username is null or p.owner_username = filter_username)
  order by p.embedding <=> query_embedding
  limit result_limit;
$$;


-- ============================================================
-- 11. Unique indexes for safe concurrent manual refreshes
--     These are not required for the helper function above,
--     but keep the materialized views eligible for direct
--     REFRESH MATERIALIZED VIEW CONCURRENTLY when needed.
-- ============================================================
create unique index if not exists hashtag_performance_pk
  on hashtag_performance (tag, owner_username, period_label);

create unique index if not exists posting_time_heatmap_pk
  on posting_time_heatmap (owner_username, day_of_week, hour_of_day);
