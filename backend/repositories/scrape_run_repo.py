from typing import Any, Optional, Sequence
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.scrape_run import ScrapeRun
from datetime import datetime, timezone


async def create_run(db: AsyncSession, data: dict) -> ScrapeRun:
    run = ScrapeRun(**data)
    db.add(run)
    await db.flush()
    return run


async def update_run(db: AsyncSession, run_id: int, data: dict) -> Optional[ScrapeRun]:
    run = await db.get(ScrapeRun, run_id)
    if run is None:
        return None
    for k, v in data.items():
        setattr(run, k, v)
    await db.flush()
    return run


async def fail_incomplete_runs(db: AsyncSession, reason: str) -> int:
    result = await db.execute(select(ScrapeRun).where(ScrapeRun.status == "running"))
    runs = result.scalars().all()
    for run in runs:
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = reason
        if run.embedding_status == "pending":
            run.embedding_status = "failed"
            if not run.embedding_error_message:
                run.embedding_error_message = reason
    await db.flush()
    return len(runs)


async def list_runs(
    db: AsyncSession,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[Sequence[ScrapeRun], int]:
    q = select(ScrapeRun)
    if status:
        q = q.where(ScrapeRun.status == status)
    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar_one()
    q = q.order_by(ScrapeRun.started_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all(), total


async def get_runs_by_ids(db: AsyncSession, run_ids: list[int]) -> list[ScrapeRun]:
    result = await db.execute(select(ScrapeRun).where(ScrapeRun.id.in_(run_ids)))
    return result.scalars().all()


async def get_run_compare_summary(db: AsyncSession, run_a_id: int, run_b_id: int) -> dict[str, Any]:
    result = await db.execute(
        text(
            """
            WITH profile_a AS (
                SELECT DISTINCT ON (profile_id)
                    profile_id,
                    followers_count,
                    follows_count,
                    posts_count
                FROM profile_snapshots
                WHERE run_id = :run_a_id
                ORDER BY profile_id, scraped_at DESC
            ),
            profile_b AS (
                SELECT DISTINCT ON (profile_id)
                    profile_id,
                    followers_count,
                    follows_count,
                    posts_count
                FROM profile_snapshots
                WHERE run_id = :run_b_id
                ORDER BY profile_id, scraped_at DESC
            ),
            profile_joined AS (
                SELECT
                    COALESCE(a.profile_id, b.profile_id) AS profile_id,
                    a.followers_count AS followers_a,
                    b.followers_count AS followers_b
                FROM profile_a a
                FULL OUTER JOIN profile_b b ON a.profile_id = b.profile_id
            ),
            latest_a AS (
                SELECT DISTINCT ON (profile_id, url)
                    profile_id,
                    url,
                    likes_count,
                    comments_count,
                    video_view_count
                FROM profile_latest_posts
                WHERE run_id = :run_a_id
                ORDER BY profile_id, url, scraped_at DESC
            ),
            latest_b AS (
                SELECT DISTINCT ON (profile_id, url)
                    profile_id,
                    url,
                    likes_count,
                    comments_count,
                    video_view_count
                FROM profile_latest_posts
                WHERE run_id = :run_b_id
                ORDER BY profile_id, url, scraped_at DESC
            ),
            latest_joined AS (
                SELECT
                    COALESCE(a.profile_id, b.profile_id) AS profile_id,
                    COALESCE(a.url, b.url) AS url,
                    a.likes_count AS likes_a,
                    b.likes_count AS likes_b,
                    a.comments_count AS comments_a,
                    b.comments_count AS comments_b,
                    a.video_view_count AS views_a,
                    b.video_view_count AS views_b
                FROM latest_a a
                FULL OUTER JOIN latest_b b
                    ON a.profile_id = b.profile_id AND a.url = b.url
            )
            SELECT
                (SELECT COUNT(*) FROM profile_snapshots WHERE run_id = :run_a_id) AS run_a_profile_snapshot_rows,
                (SELECT COUNT(*) FROM profile_snapshots WHERE run_id = :run_b_id) AS run_b_profile_snapshot_rows,
                (SELECT COUNT(*) FROM profile_latest_posts WHERE run_id = :run_a_id) AS run_a_latest_posts_rows,
                (SELECT COUNT(*) FROM profile_latest_posts WHERE run_id = :run_b_id) AS run_b_latest_posts_rows,
                COUNT(*) FILTER (WHERE followers_a IS NOT NULL AND followers_b IS NOT NULL) AS common_profiles,
                COUNT(*) FILTER (WHERE followers_a IS NULL AND followers_b IS NOT NULL) AS new_profiles,
                COUNT(*) FILTER (WHERE followers_a IS NOT NULL AND followers_b IS NULL) AS missing_profiles,
                COALESCE(SUM(COALESCE(followers_b, 0) - COALESCE(followers_a, 0)), 0) AS net_followers_delta,
                (SELECT COUNT(*) FROM latest_joined WHERE likes_a IS NOT NULL AND likes_b IS NOT NULL) AS common_latest_posts,
                (SELECT COUNT(*) FROM latest_joined WHERE likes_a IS NULL AND likes_b IS NOT NULL) AS new_latest_posts,
                (SELECT COUNT(*) FROM latest_joined WHERE likes_a IS NOT NULL AND likes_b IS NULL) AS missing_latest_posts,
                (SELECT COALESCE(SUM(COALESCE(likes_b, 0) - COALESCE(likes_a, 0)), 0) FROM latest_joined) AS net_likes_delta
            FROM profile_joined
            """
        ),
        {"run_a_id": run_a_id, "run_b_id": run_b_id},
    )
    row = result.mappings().first()
    return dict(row) if row else {}


async def get_profile_deltas(db: AsyncSession, run_a_id: int, run_b_id: int, limit: int = 50) -> list[dict[str, Any]]:
    result = await db.execute(
        text(
            """
            WITH a AS (
                SELECT DISTINCT ON (profile_id)
                    profile_id,
                    followers_count,
                    follows_count,
                    posts_count,
                    scraped_at
                FROM profile_snapshots
                WHERE run_id = :run_a_id
                ORDER BY profile_id, scraped_at DESC
            ),
            b AS (
                SELECT DISTINCT ON (profile_id)
                    profile_id,
                    followers_count,
                    follows_count,
                    posts_count,
                    scraped_at
                FROM profile_snapshots
                WHERE run_id = :run_b_id
                ORDER BY profile_id, scraped_at DESC
            ),
            joined AS (
                SELECT
                    COALESCE(a.profile_id, b.profile_id) AS profile_id,
                    a.followers_count AS followers_run_a,
                    b.followers_count AS followers_run_b,
                    a.follows_count AS follows_run_a,
                    b.follows_count AS follows_run_b,
                    a.posts_count AS posts_run_a,
                    b.posts_count AS posts_run_b
                FROM a
                FULL OUTER JOIN b ON a.profile_id = b.profile_id
            )
            SELECT
                profile_id,
                followers_run_a,
                followers_run_b,
                follows_run_a,
                follows_run_b,
                posts_run_a,
                posts_run_b,
                COALESCE(followers_run_b, 0) - COALESCE(followers_run_a, 0) AS followers_delta,
                COALESCE(follows_run_b, 0) - COALESCE(follows_run_a, 0) AS follows_delta,
                COALESCE(posts_run_b, 0) - COALESCE(posts_run_a, 0) AS posts_delta,
                CASE
                    WHEN followers_run_a IS NULL THEN 'new'
                    WHEN followers_run_b IS NULL THEN 'missing'
                    ELSE 'common'
                END AS change_type
            FROM joined
            ORDER BY ABS(COALESCE(followers_run_b, 0) - COALESCE(followers_run_a, 0)) DESC, profile_id
            LIMIT :limit
            """
        ),
        {"run_a_id": run_a_id, "run_b_id": run_b_id, "limit": limit},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_latest_post_deltas(db: AsyncSession, run_a_id: int, run_b_id: int, limit: int = 50) -> list[dict[str, Any]]:
    result = await db.execute(
        text(
            """
            WITH a AS (
                SELECT DISTINCT ON (profile_id, url)
                    profile_id,
                    owner_username,
                    url,
                    likes_count,
                    comments_count,
                    video_view_count,
                    scraped_at
                FROM profile_latest_posts
                WHERE run_id = :run_a_id
                ORDER BY profile_id, url, scraped_at DESC
            ),
            b AS (
                SELECT DISTINCT ON (profile_id, url)
                    profile_id,
                    owner_username,
                    url,
                    likes_count,
                    comments_count,
                    video_view_count,
                    scraped_at
                FROM profile_latest_posts
                WHERE run_id = :run_b_id
                ORDER BY profile_id, url, scraped_at DESC
            ),
            joined AS (
                SELECT
                    COALESCE(a.profile_id, b.profile_id) AS profile_id,
                    COALESCE(a.owner_username, b.owner_username) AS owner_username,
                    COALESCE(a.url, b.url) AS url,
                    a.likes_count AS likes_run_a,
                    b.likes_count AS likes_run_b,
                    a.comments_count AS comments_run_a,
                    b.comments_count AS comments_run_b,
                    a.video_view_count AS views_run_a,
                    b.video_view_count AS views_run_b
                FROM a
                FULL OUTER JOIN b
                    ON a.profile_id = b.profile_id AND a.url = b.url
            )
            SELECT
                profile_id,
                owner_username,
                url,
                likes_run_a,
                likes_run_b,
                comments_run_a,
                comments_run_b,
                views_run_a,
                views_run_b,
                COALESCE(likes_run_b, 0) - COALESCE(likes_run_a, 0) AS likes_delta,
                COALESCE(comments_run_b, 0) - COALESCE(comments_run_a, 0) AS comments_delta,
                COALESCE(views_run_b, 0) - COALESCE(views_run_a, 0) AS views_delta,
                CASE
                    WHEN likes_run_a IS NULL THEN 'new'
                    WHEN likes_run_b IS NULL THEN 'missing'
                    ELSE 'common'
                END AS change_type
            FROM joined
            ORDER BY ABS(COALESCE(likes_run_b, 0) - COALESCE(likes_run_a, 0)) DESC, profile_id
            LIMIT :limit
            """
        ),
        {"run_a_id": run_a_id, "run_b_id": run_b_id, "limit": limit},
    )
    return [dict(row) for row in result.mappings().all()]
