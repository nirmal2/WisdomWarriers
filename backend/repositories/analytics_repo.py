from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_overview(db: AsyncSession) -> dict:
    result = await db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM profiles) AS total_profiles,
            (SELECT COUNT(*) FROM posts) AS total_posts,
            (SELECT COALESCE(AVG(followers_count), 0) FROM profiles) AS avg_followers,
            (SELECT username FROM profiles ORDER BY followers_count DESC LIMIT 1) AS top_profile
    """))
    row = result.mappings().first()
    return dict(row) if row else {}


async def get_follower_growth(db: AsyncSession, username: str | None = None) -> list[dict]:
    if username:
        result = await db.execute(text("""
            SELECT ps.period_label, ps.followers_count, p.username
            FROM profile_snapshots ps
            JOIN profiles p ON p.id = ps.profile_id
            WHERE p.username = :username
            ORDER BY ps.scraped_at
        """), {"username": username})
    else:
        result = await db.execute(text("""
            SELECT ps.period_label, SUM(ps.followers_count) AS followers_count, 'all' AS username
            FROM profile_snapshots ps
            GROUP BY ps.period_label
            ORDER BY ps.period_label
        """))
    return [dict(r) for r in result.mappings().all()]


async def get_top_profiles(db: AsyncSession, metric: str = "followers_count", limit: int = 10) -> list[dict]:
    allowed = {"followers_count", "follows_count", "posts_count"}
    col = metric if metric in allowed else "followers_count"
    result = await db.execute(
        text(f"SELECT username, {col} AS value FROM profiles ORDER BY {col} DESC LIMIT :limit"),
        {"limit": limit},
    )
    return [dict(r) for r in result.mappings().all()]


async def get_hashtag_frequency(db: AsyncSession, limit: int = 20) -> list[dict]:
    result = await db.execute(text("""
        SELECT tag, COUNT(*) AS count
        FROM posts, jsonb_array_elements_text(hashtags) AS tag
        GROUP BY tag
        ORDER BY count DESC
        LIMIT :limit
    """), {"limit": limit})
    return [dict(r) for r in result.mappings().all()]


async def get_engagement_by_profile(db: AsyncSession) -> list[dict]:
    result = await db.execute(text("""
        SELECT owner_username,
               ROUND(AVG(likes_count), 0)::int AS avg_likes,
               ROUND(AVG(video_play_count), 0)::int AS avg_plays,
               COUNT(*) AS post_count
        FROM posts
        GROUP BY owner_username
        ORDER BY avg_likes DESC
        LIMIT 20
    """))
    return [dict(r) for r in result.mappings().all()]


async def get_post_volume(db: AsyncSession) -> list[dict]:
    result = await db.execute(text("""
        SELECT period_label, COUNT(*) AS post_count
        FROM posts
        GROUP BY period_label
        ORDER BY period_label
    """))
    return [dict(r) for r in result.mappings().all()]


async def get_wisdom_warriors_monthly_views(db: AsyncSession, month: str) -> list[dict]:
    result = await db.execute(text("""
        SELECT
            sp.username,
            :month AS month,
            COALESCE(
                SUM(
                    COALESCE(p.video_view_count, 0)::double precision /
                    GREATEST(1, COALESCE(jsonb_array_length(p.coauthor_producers), 0) + 1)
                ),
                0
            )::double precision AS total_views
        FROM scrape_profiles sp
        LEFT JOIN posts p
            ON lower(p.owner_username) = lower(sp.username)
            AND to_char(p.timestamp AT TIME ZONE 'UTC', 'YYYY-MM') = :month
        GROUP BY sp.id, sp.username, sp.position
        ORDER BY sp.position, sp.id
    """), {"month": month})
    return [dict(r) for r in result.mappings().all()]
