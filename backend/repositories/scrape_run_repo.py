import json
from typing import Any, Optional, Sequence
from sqlalchemy import select, func, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.scrape_run import ScrapeRun
from backend.models.scrape_run_profile_progress import ScrapeRunProfileProgress
from datetime import datetime, timezone


def _load_json_array(raw_value: str | None) -> list[dict[str, Any]]:
    if not raw_value:
        return []
    try:
        loaded = json.loads(raw_value)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(loaded, list):
        return []
    return [row for row in loaded if isinstance(row, dict)]


def _to_iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed or None
    return None


async def append_apify_stage_history(
    db: AsyncSession,
    run_id: int,
    entry: dict[str, Any],
) -> Optional[ScrapeRun]:
    run = await db.get(ScrapeRun, run_id)
    if run is None:
        return None

    history = _load_json_array(run.apify_stage_history)
    history.append(entry)
    run.apify_stage_history = json.dumps(history)
    await db.flush()
    return run


async def update_apify_stage_metadata(
    db: AsyncSession,
    run_id: int,
    stage: str,
    metadata: dict[str, Any],
    event_type: str = "actor_call",
    extra: dict[str, Any] | None = None,
) -> Optional[ScrapeRun]:
    run = await db.get(ScrapeRun, run_id)
    if run is None:
        return None

    stage_key = stage.strip().lower()
    if stage_key not in {"posts", "profiles"}:
        raise ValueError(f"Unsupported stage: {stage}")

    prefix = f"apify_{stage_key}"
    actor_id = str(metadata.get("actor_id") or "").strip() or None
    run_external_id = str(metadata.get("run_id") or "").strip() or None
    dataset_id = str(metadata.get("dataset_id") or "").strip() or None
    status = str(metadata.get("status") or "").strip() or None

    setattr(run, f"{prefix}_actor_id", actor_id)
    setattr(run, f"{prefix}_run_id", run_external_id)
    setattr(run, f"{prefix}_dataset_id", dataset_id)
    setattr(run, f"{prefix}_status", status)

    started_at = metadata.get("started_at")
    finished_at = metadata.get("finished_at")
    if isinstance(started_at, datetime):
        setattr(run, f"{prefix}_started_at", started_at)
    if isinstance(finished_at, datetime):
        setattr(run, f"{prefix}_finished_at", finished_at)

    entry: dict[str, Any] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "stage": stage_key,
        "event_type": event_type,
        "actor_id": actor_id,
        "run_id": run_external_id,
        "dataset_id": dataset_id,
        "status": status,
        "started_at": _to_iso(started_at),
        "finished_at": _to_iso(finished_at),
    }
    if extra:
        entry["extra"] = extra

    history = _load_json_array(run.apify_stage_history)
    history.append(entry)
    run.apify_stage_history = json.dumps(history)
    await db.flush()
    return run


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


async def claim_incomplete_runs_for_resume(db: AsyncSession) -> list[ScrapeRun]:
    """Atomically claim running runs so only one process attempts auto-resume."""
    claim_result = await db.execute(
        update(ScrapeRun)
        .where(ScrapeRun.status == "running")
        .values(status="resuming", finished_at=None, error_message=None)
        .returning(ScrapeRun.id)
    )
    run_ids = [row[0] for row in claim_result.all()]
    if not run_ids:
        return []

    result = await db.execute(
        select(ScrapeRun)
        .where(ScrapeRun.id.in_(run_ids))
        .order_by(ScrapeRun.started_at.asc())
    )
    return result.scalars().all()


def _normalize_username(username: str) -> str:
    return (username or "").strip().lstrip("@").lower()


async def initialize_profile_progress(db: AsyncSession, run_id: int, usernames: list[str]) -> None:
    seen: set[str] = set()
    cleaned: list[str] = []
    for username in usernames:
        normalized = _normalize_username(username)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(normalized)

    for username in cleaned:
        existing = await db.execute(
            select(ScrapeRunProfileProgress)
            .where(ScrapeRunProfileProgress.run_id == run_id)
            .where(ScrapeRunProfileProgress.username == username)
            .limit(1)
        )
        row = existing.scalar_one_or_none()
        if row is not None:
            continue
        db.add(
            ScrapeRunProfileProgress(
                run_id=run_id,
                username=username,
                status="pending",
                attempt_count=0,
                items_fetched=0,
            )
        )
    await db.flush()


async def mark_running_profiles_failed(db: AsyncSession, run_id: int, reason: str) -> None:
    await db.execute(
        update(ScrapeRunProfileProgress)
        .where(ScrapeRunProfileProgress.run_id == run_id)
        .where(ScrapeRunProfileProgress.status == "running")
        .values(
            status="failed",
            finished_at=datetime.now(timezone.utc),
            error_message=reason,
            last_checkpoint_at=datetime.now(timezone.utc),
        )
    )
    await db.flush()


async def get_usernames_for_resume(
    db: AsyncSession,
    run_id: int,
    max_attempts: int | None = None,
) -> list[str]:
    q = (
        select(ScrapeRunProfileProgress.username)
        .where(ScrapeRunProfileProgress.run_id == run_id)
        .where(ScrapeRunProfileProgress.status.in_(["pending", "failed", "running"]))
    )
    if max_attempts is not None and max_attempts > 0:
        q = q.where(
            (ScrapeRunProfileProgress.status != "failed")
            | (ScrapeRunProfileProgress.attempt_count < max_attempts)
        )
    result = await db.execute(q.order_by(ScrapeRunProfileProgress.id.asc()))
    return [row[0] for row in result.all()]


async def get_profile_progress_rows(db: AsyncSession, run_id: int) -> list[ScrapeRunProfileProgress]:
    result = await db.execute(
        select(ScrapeRunProfileProgress)
        .where(ScrapeRunProfileProgress.run_id == run_id)
        .order_by(ScrapeRunProfileProgress.id.asc())
    )
    return result.scalars().all()


async def list_profile_progress_rows(
    db: AsyncSession,
    run_id: int,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[Sequence[ScrapeRunProfileProgress], int]:
    q = select(ScrapeRunProfileProgress).where(ScrapeRunProfileProgress.run_id == run_id)
    if status:
        q = q.where(ScrapeRunProfileProgress.status == status)

    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = int(count_result.scalar_one() or 0)
    result = await db.execute(
        q.order_by(ScrapeRunProfileProgress.id.asc()).limit(limit).offset(offset)
    )
    return result.scalars().all(), total


async def reset_profile_progress(db: AsyncSession, run_id: int) -> None:
    await db.execute(
        text("DELETE FROM scrape_run_profile_progress WHERE run_id = :run_id"),
        {"run_id": run_id},
    )
    await db.flush()


async def mark_profile_running(db: AsyncSession, run_id: int, username: str) -> None:
    normalized = _normalize_username(username)
    now = datetime.now(timezone.utc)
    row_result = await db.execute(
        select(ScrapeRunProfileProgress)
        .where(ScrapeRunProfileProgress.run_id == run_id)
        .where(ScrapeRunProfileProgress.username == normalized)
        .limit(1)
    )
    row = row_result.scalar_one_or_none()
    if row is None:
        row = ScrapeRunProfileProgress(run_id=run_id, username=normalized)
        db.add(row)
    row.status = "running"
    row.attempt_count = int(row.attempt_count or 0) + 1
    row.started_at = now
    row.finished_at = None
    row.error_message = None
    row.last_checkpoint_at = now
    await db.flush()


async def mark_profile_success(db: AsyncSession, run_id: int, username: str, items_fetched: int) -> None:
    normalized = _normalize_username(username)
    now = datetime.now(timezone.utc)
    row_result = await db.execute(
        select(ScrapeRunProfileProgress)
        .where(ScrapeRunProfileProgress.run_id == run_id)
        .where(ScrapeRunProfileProgress.username == normalized)
        .limit(1)
    )
    row = row_result.scalar_one_or_none()
    if row is None:
        row = ScrapeRunProfileProgress(run_id=run_id, username=normalized)
        db.add(row)
    row.status = "success"
    row.items_fetched = max(0, int(items_fetched or 0))
    row.finished_at = now
    row.error_message = None
    row.last_checkpoint_at = now
    await db.flush()


async def mark_profile_failed(db: AsyncSession, run_id: int, username: str, error_message: str) -> None:
    normalized = _normalize_username(username)
    now = datetime.now(timezone.utc)
    row_result = await db.execute(
        select(ScrapeRunProfileProgress)
        .where(ScrapeRunProfileProgress.run_id == run_id)
        .where(ScrapeRunProfileProgress.username == normalized)
        .limit(1)
    )
    row = row_result.scalar_one_or_none()
    if row is None:
        row = ScrapeRunProfileProgress(run_id=run_id, username=normalized)
        db.add(row)
    row.status = "failed"
    row.finished_at = now
    row.error_message = error_message
    row.last_checkpoint_at = now
    await db.flush()


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
