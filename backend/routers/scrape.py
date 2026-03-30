import json
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.engine import get_db
from backend.models.post_snapshot import PostSnapshot
from backend.models.profile_snapshot import ProfileSnapshot
from backend.models.scrape_run import ScrapeRun
from backend.schemas.scrape import (
    InsightRead,
    RunComparisonRead,
    ProfilesSourceRead,
    ProfilesSourceUpdate,
    ScrapeProfileRead,
    ScrapeProfileCreate,
    ScrapeProfileUpdate,
    ScrapeDbUpdateStatus,
    ScrapeRequest,
    CombinedScrapeRequest,
    ScrapeStartRead,
    ScrapeStatusRead,
    ScrapeRunRead,
    ScrapeRunListResponse,
)
from backend.repositories.scrape_profile_repo import (
    list_scrape_profiles,
    replace_scrape_profiles,
    add_scrape_profile,
    update_scrape_profile_fields,
    delete_scrape_profile,
)
from backend.services.scrape_service import run_posts_scrape, run_profiles_scrape, run_combined_scrape, recover_posts_from_debug
from backend.repositories.scrape_run_repo import (
    create_run,
    get_latest_post_deltas,
    get_profile_deltas,
    get_run_compare_summary,
    get_runs_by_ids,
    list_runs,
)

router = APIRouter(prefix="/api/scrape", tags=["scrape"])


def _build_insights(summary: dict, profile_deltas: list[dict], latest_post_deltas: list[dict]) -> list[InsightRead]:
    insights: list[InsightRead] = []

    net_followers_delta = int(summary.get("net_followers_delta", 0) or 0)
    follower_tone = "positive" if net_followers_delta > 0 else "negative" if net_followers_delta < 0 else "neutral"
    insights.append(
        InsightRead(
            title="Net Followers Delta",
            value=f"{net_followers_delta:+,}",
            detail="Follower change across compared profile snapshot rows.",
            tone=follower_tone,
        )
    )

    top_profile = next((row for row in profile_deltas if row.get("change_type") == "common"), None)
    if top_profile:
        insights.append(
            InsightRead(
                title="Top Profile Move",
                value=f"{top_profile['profile_id']} ({int(top_profile.get('followers_delta', 0)):+,})",
                detail="Largest absolute follower shift among profiles present in both runs.",
                tone="positive" if int(top_profile.get("followers_delta", 0)) >= 0 else "negative",
            )
        )

    net_likes_delta = int(summary.get("net_likes_delta", 0) or 0)
    likes_tone = "positive" if net_likes_delta > 0 else "negative" if net_likes_delta < 0 else "neutral"
    insights.append(
        InsightRead(
            title="Net Likes Delta",
            value=f"{net_likes_delta:+,}",
            detail="Like change across latest-post snapshots.",
            tone=likes_tone,
        )
    )

    top_post = next((row for row in latest_post_deltas if row.get("change_type") == "common"), None)
    if top_post:
        owner = top_post.get("owner_username") or top_post.get("profile_id")
        insights.append(
            InsightRead(
                title="Top Post Move",
                value=f"{owner} ({int(top_post.get('likes_delta', 0)):+,} likes)",
                detail="Largest like change among posts visible in both runs.",
                tone="positive" if int(top_post.get("likes_delta", 0)) >= 0 else "negative",
            )
        )

    new_profiles = int(summary.get("new_profiles", 0) or 0)
    missing_profiles = int(summary.get("missing_profiles", 0) or 0)
    insights.append(
        InsightRead(
            title="Coverage Shift",
            value=f"+{new_profiles} / -{missing_profiles}",
            detail="Profiles that appeared in run B vs missing from run B.",
            tone="neutral",
        )
    )

    return insights


@router.get("/profiles-source", response_model=ProfilesSourceRead)
async def get_profiles_source(db: AsyncSession = Depends(get_db)) -> ProfilesSourceRead:
    rows = await list_scrape_profiles(db)
    return ProfilesSourceRead(usernames=[row.username for row in rows])


@router.put("/profiles-source", response_model=ProfilesSourceRead)
async def update_profiles_source(body: ProfilesSourceUpdate, db: AsyncSession = Depends(get_db)) -> ProfilesSourceRead:
    usernames = await replace_scrape_profiles(db, body.usernames)
    await db.commit()
    return ProfilesSourceRead(usernames=usernames)


@router.post("/run", response_model=dict)
async def trigger_scrape(
    req: ScrapeRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    usernames = req.usernames or [row.username for row in await list_scrape_profiles(db)]
    if req.scraper_type == "profiles":
        background.add_task(
            run_profiles_scrape,
            usernames,
            "manual",
            None,
            "on_demand",
            None,
            req.batch_mode,
            req.enable_embeddings,
        )
    else:
        background.add_task(
            run_posts_scrape, usernames, "posts", "manual", None,
            req.results_limit, req.only_posts_newer_than, "on_demand",
            req.data_detail_level, None, req.enable_embeddings,
        )
    return {"status": "started", "profiles_count": len(usernames)}


@router.post("/run/combined", response_model=ScrapeStartRead)
async def trigger_combined_scrape(
    req: CombinedScrapeRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Trigger a combined profile + post scrape.
    Profiles are scraped first, then posts, using the same scraped_at timestamp for all records.
    """
    usernames = req.usernames or [row.username for row in await list_scrape_profiles(db)]
    run = await create_run(db, {
        "scraper_type": "combined",
        "trigger": "manual",
        "schedule_id": None,
        "embedding_status": "pending" if req.enable_embeddings else "skipped",
        "profiles_requested": len(usernames),
        "raw_logs": json.dumps([
            f"Combined scrape queued for {len(usernames)} profile(s).",
            "Preparing profiles stage...",
        ]),
    })
    await db.commit()
    background.add_task(
        run_combined_scrape,
        usernames,
        req.results_limit,
        req.only_posts_newer_than,
        req.data_detail_level,
        req.enable_embeddings,
        req.batch_mode,
        "manual",
        None,
        "on_demand",
        run.id,
    )
    return {"status": "started", "profiles_count": len(usernames), "action": "combined_scrape", "run_id": run.id}


@router.get("/runs", response_model=ScrapeRunListResponse)
async def get_runs(
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> ScrapeRunListResponse:
    items, total = await list_runs(db, status, limit, offset)
    return ScrapeRunListResponse(items=items, total=total)


@router.get("/status", response_model=ScrapeStatusRead)
async def get_scrape_status(
    run_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> ScrapeStatusRead:
    if run_id is not None:
        run = await db.get(ScrapeRun, run_id)
    else:
        running_result = await db.execute(
            select(ScrapeRun)
            .where(ScrapeRun.status == "running")
            .order_by(ScrapeRun.started_at.desc())
            .limit(1)
        )
        run = running_result.scalar_one_or_none()
        if run is None:
            latest_result = await db.execute(select(ScrapeRun).order_by(ScrapeRun.started_at.desc()).limit(1))
            run = latest_result.scalar_one_or_none()

    if run is None:
        return ScrapeStatusRead(run=None, progress_pct=0, db_updates=ScrapeDbUpdateStatus(), logs=["No scrape run found yet."])

    # Use immutable snapshot rows for per-run counts so values do not drop
    # when canonical Post rows are updated by later runs.
    posts_rows = await db.scalar(select(func.count()).select_from(PostSnapshot).where(PostSnapshot.run_id == run.id))
    snapshots_rows = await db.scalar(select(func.count()).select_from(ProfileSnapshot).where(ProfileSnapshot.run_id == run.id))
    profiles_touched = await db.scalar(
        select(func.count(func.distinct(ProfileSnapshot.profile_id))).where(ProfileSnapshot.run_id == run.id)
    )
    missing_usernames: list[str] = []
    aggregated_raw_logs: list[str] = []

    if run.missing_usernames:
        try:
            missing_usernames = json.loads(run.missing_usernames)
        except (json.JSONDecodeError, TypeError):
            missing_usernames = []
    if run.raw_logs:
        try:
            aggregated_raw_logs.extend(json.loads(run.raw_logs))
        except (json.JSONDecodeError, TypeError):
            pass

    # Combined profile->posts flow writes profile rows in a different run_id but shares
    # the same scraped_at timestamp. For posts runs, merge related profile counts by timestamp.
    if run.scraper_type == "posts":
        shared_scraped_at = await db.scalar(
            select(func.max(PostSnapshot.scraped_at)).where(PostSnapshot.run_id == run.id)
        )
        if shared_scraped_at is not None:
            snapshots_rows = await db.scalar(
                select(func.count())
                .select_from(ProfileSnapshot)
                .where(ProfileSnapshot.scraped_at == shared_scraped_at)
            )
            profiles_touched = await db.scalar(
                select(func.count(func.distinct(ProfileSnapshot.profile_id)))
                .where(ProfileSnapshot.scraped_at == shared_scraped_at)
            )
            profile_run_id = await db.scalar(
                select(ProfileSnapshot.run_id)
                .where(ProfileSnapshot.scraped_at == shared_scraped_at)
                .limit(1)
            )
            if profile_run_id is not None:
                profile_run = await db.get(ScrapeRun, profile_run_id)
                if profile_run and profile_run.missing_usernames:
                    try:
                        missing_usernames = json.loads(profile_run.missing_usernames)
                    except (json.JSONDecodeError, TypeError):
                        missing_usernames = []
                if profile_run and profile_run.raw_logs:
                    try:
                        aggregated_raw_logs = json.loads(profile_run.raw_logs) + aggregated_raw_logs
                    except (json.JSONDecodeError, TypeError):
                        pass

        # For a still-running posts scrape with no PostSnapshot rows yet (Apify call in progress),
        # show the most recently completed profiles run logs so the live log isn't blank.
        if run.status == "running" and posts_rows == 0 and not aggregated_raw_logs:
            prev_profile_run_result = await db.execute(
                select(ScrapeRun)
                .where(ScrapeRun.scraper_type == "profiles")
                .where(ScrapeRun.status == "completed")
                .where(ScrapeRun.started_at <= run.started_at)
                .order_by(ScrapeRun.finished_at.desc())
                .limit(1)
            )
            prev_profile_run = prev_profile_run_result.scalar_one_or_none()
            if prev_profile_run:
                if prev_profile_run.missing_usernames and not missing_usernames:
                    try:
                        missing_usernames = json.loads(prev_profile_run.missing_usernames)
                    except (json.JSONDecodeError, TypeError):
                        pass
                if prev_profile_run.raw_logs:
                    try:
                        aggregated_raw_logs = json.loads(prev_profile_run.raw_logs)
                    except (json.JSONDecodeError, TypeError):
                        pass

    processed_count = run.items_fetched
    if run.scraper_type == "profiles":
        # For profile runs, missing/private users are still processed attempts.
        processed_count = min(run.profiles_requested, run.items_fetched + len(missing_usernames))

    if run.scraper_type == "combined":
        if run.status == "completed":
            progress_pct = 100
        elif posts_rows > 0 or run.items_fetched > 0:
            progress_pct = min(99, 70 + min(run.items_fetched, 29))
        elif profiles_touched > 0:
            progress_pct = min(69, max(10, int((profiles_touched / max(run.profiles_requested, 1)) * 60)))
        else:
            progress_pct = 5
    elif run.status == "completed":
        progress_pct = 100
    elif run.profiles_requested > 0:
        progress_pct = min(99, int((processed_count / max(run.profiles_requested, 1)) * 100))
    else:
        progress_pct = 0

    logs = [
        f"Run #{run.id} started ({run.scraper_type}, {run.trigger}).",
        f"Progress: {processed_count}/{run.profiles_requested} processed.",
        f"DB updates: posts={posts_rows}, snapshots={snapshots_rows}.",
    ]
    if run.embedding_status:
        logs.append(f"Embedding status: {run.embedding_status}.")
    if run.status == "completed":
        logs.append("Run completed.")
    elif run.status == "failed":
        logs.append(f"Run failed: {run.error_message or 'unknown error'}")
    elif run.scraper_type == "combined":
        if posts_rows > 0:
            logs.append(f"Posts stage is in progress. Persisted {posts_rows} post snapshot row(s) so far.")
        elif profiles_touched > 0:
            logs.append(f"Profiles stage is in progress. Persisted {profiles_touched}/{run.profiles_requested} profile(s) so far.")
        else:
            logs.append("Combined scrape is initializing...")
    else:
        profile_fetch_finished = False
        if run.scraper_type == "profiles" and aggregated_raw_logs:
            profile_fetch_finished = any(
                isinstance(line, str)
                and (
                    "Status: SUCCEEDED" in line
                    or "[Status message]: Scraper finished" in line
                    or "CheerioCrawler: Finished!" in line
                )
                for line in aggregated_raw_logs
            )
        if run.scraper_type == "profiles" and processed_count >= run.profiles_requested:
            logs.append("Profile scrape finished. Finalizing embedding/indexing...")
        elif run.scraper_type == "profiles" and profile_fetch_finished:
            logs.append(
                f"Profile fetch is done at Apify. Backend is persisting results to DB ({processed_count}/{run.profiles_requested})..."
            )
        elif run.scraper_type == "posts" and run.items_fetched == 0:
            logs.append("Posts scraper: waiting for Apify actor to return results (this may take a few minutes)...")
        else:
            logs.append("Run still in progress...")
    if run.embedding_error_message:
        logs.append(f"Embedding error: {run.embedding_error_message}")
    if missing_usernames:
        logs.append(f"Missing profiles ({len(missing_usernames)}): {', '.join(missing_usernames)}")
    
    # Include raw scraper logs if available.
    if aggregated_raw_logs:
        logs.extend(aggregated_raw_logs)

    return ScrapeStatusRead(
        run=run,
        progress_pct=progress_pct,
        db_updates=ScrapeDbUpdateStatus(
            posts_rows=posts_rows or 0,
            profile_snapshots_rows=snapshots_rows or 0,
            profiles_touched=profiles_touched or 0,
            missing_usernames=missing_usernames,
        ),
        logs=logs,
    )


@router.patch("/runs/{run_id}/skip-embedding", response_model=ScrapeRunRead)
async def skip_embedding(run_id: int, db: AsyncSession = Depends(get_db)) -> ScrapeRun:
    run = await db.get(ScrapeRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.embedding_status not in ("pending",):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot skip: embedding status is already '{run.embedding_status}'",
        )
    run.embedding_status = "skipped"
    await db.commit()
    await db.refresh(run)
    return run


@router.post("/runs/{run_id}/recover-debug")
async def recover_run_from_debug(run_id: int) -> dict:
    return await recover_posts_from_debug(run_id)


@router.get("/runs/compare", response_model=RunComparisonRead)
async def compare_runs(
    run_a_id: int,
    run_b_id: int,
    profile_limit: int = 50,
    latest_post_limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> RunComparisonRead:
    if run_a_id == run_b_id:
        raise HTTPException(status_code=400, detail="Please choose two different runs")

    runs = await get_runs_by_ids(db, [run_a_id, run_b_id])
    run_map = {run.id: run for run in runs}
    run_a = run_map.get(run_a_id)
    run_b = run_map.get(run_b_id)
    if run_a is None or run_b is None:
        raise HTTPException(status_code=404, detail="One or both runs were not found")
    if run_a.status != "completed" or run_b.status != "completed":
        raise HTTPException(status_code=409, detail="Run comparison is available only for completed runs")

    summary = await get_run_compare_summary(db, run_a_id, run_b_id)
    profile_deltas = await get_profile_deltas(db, run_a_id, run_b_id, limit=profile_limit)
    latest_post_deltas = await get_latest_post_deltas(db, run_a_id, run_b_id, limit=latest_post_limit)
    insights = _build_insights(summary, profile_deltas, latest_post_deltas)

    return RunComparisonRead(
        run_a=run_a,
        run_b=run_b,
        summary=summary,
        profile_deltas=profile_deltas,
        latest_post_deltas=latest_post_deltas,
        insights=insights,
    )


# ── Wisdom Warriors influencer management ─────────────────────────────────────

@router.get("/wisdom-warriors", response_model=list[ScrapeProfileRead])
async def list_wisdom_warriors(db: AsyncSession = Depends(get_db)) -> list[ScrapeProfileRead]:
    rows = await list_scrape_profiles(db)
    if not rows:
        return []
    usernames_lower = [r.username.lower() for r in rows]
    pic_result = await db.execute(
        text("SELECT lower(username), profile_pic_url FROM profiles WHERE lower(username) = ANY(:u)"),
        {"u": usernames_lower},
    )
    pic_map: dict[str, str | None] = {row[0]: row[1] for row in pic_result.fetchall()}
    return [
        ScrapeProfileRead(
            id=r.id,
            username=r.username,
            category=r.category,
            grade=r.grade,
            position=r.position,
            profile_pic_url=pic_map.get(r.username.lower()),
        )
        for r in rows
    ]


@router.post("/wisdom-warriors", response_model=ScrapeProfileRead, status_code=201)
async def create_wisdom_warrior(body: ScrapeProfileCreate, db: AsyncSession = Depends(get_db)) -> ScrapeProfileRead:
    profile = await add_scrape_profile(db, body.username, body.category, body.grade)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.patch("/wisdom-warriors/{profile_id}", response_model=ScrapeProfileRead)
async def update_wisdom_warrior(
    profile_id: int,
    body: ScrapeProfileUpdate,
    db: AsyncSession = Depends(get_db),
) -> ScrapeProfileRead:
    profile = await update_scrape_profile_fields(
        db, profile_id,
        username=body.username if "username" in body.model_fields_set else None,
        category=body.category if "category" in body.model_fields_set else None,
        grade=body.grade if "grade" in body.model_fields_set else None,
        set_fields=body.model_fields_set,
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    await db.commit()
    await db.refresh(profile)
    return profile


@router.delete("/wisdom-warriors/{profile_id}", status_code=204)
async def delete_wisdom_warrior(profile_id: int, db: AsyncSession = Depends(get_db)) -> None:
    deleted = await delete_scrape_profile(db, profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Profile not found")
    await db.commit()
