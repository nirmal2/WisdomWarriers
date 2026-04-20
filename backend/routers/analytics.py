import re
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.engine import get_db
from backend.repositories.analytics_repo import (
    get_account_monthly_summary,
    get_grade_benchmarks,
    get_overview,
    get_follower_growth,
    get_top_profiles,
    get_hashtag_frequency,
    get_hashtag_performance,
    get_engagement_by_profile,
    get_post_engagement_history,
    get_post_volume,
    get_posting_time_heatmap,
    get_scrape_run_summary,
    search_similar_posts,
    get_wisdom_warriors_monthly_views_filtered,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db)) -> dict:
    return await get_overview(db)


@router.get("/follower-growth")
async def follower_growth(username: str | None = None, db: AsyncSession = Depends(get_db)) -> list:
    return await get_follower_growth(db, username)


@router.get("/top-profiles")
async def top_profiles(
    metric: str = "followers_count", limit: int = 10, db: AsyncSession = Depends(get_db)
) -> list:
    return await get_top_profiles(db, metric, limit)


@router.get("/hashtag-frequency")
async def hashtag_frequency(limit: int = 20, db: AsyncSession = Depends(get_db)) -> list:
    return await get_hashtag_frequency(db, limit)


@router.get("/engagement-by-profile")
async def engagement(db: AsyncSession = Depends(get_db)) -> list:
    return await get_engagement_by_profile(db)


@router.get("/post-trends")
async def post_trends(db: AsyncSession = Depends(get_db)) -> list:
    return await get_post_volume(db)


@router.get("/account-summary")
async def account_summary(
    period_label: str | None = None,
    limit: int = 12,
    db: AsyncSession = Depends(get_db),
) -> list:
    return await get_account_monthly_summary(db, period_label, limit)


@router.get("/grade-benchmarks")
async def grade_benchmarks(
    period_label: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list:
    return await get_grade_benchmarks(db, period_label)


@router.get("/hashtag-performance")
async def hashtag_performance(
    period_label: str | None = None,
    username: str | None = None,
    limit: int = 15,
    db: AsyncSession = Depends(get_db),
) -> list:
    return await get_hashtag_performance(db, period_label, username, limit)


@router.get("/posting-time-heatmap")
async def posting_time_heatmap(
    username: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list:
    return await get_posting_time_heatmap(db, username)


@router.get("/scrape-run-summary")
async def scrape_run_summary(limit: int = 10, db: AsyncSession = Depends(get_db)) -> list:
    return await get_scrape_run_summary(db, limit)


@router.get("/post-engagement-history")
async def post_engagement_history(short_code: str, db: AsyncSession = Depends(get_db)) -> list:
    return await get_post_engagement_history(db, short_code)


@router.get("/semantic-post-search")
async def semantic_post_search(
    query: str,
    username: str | None = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
) -> list:
    query = query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    return await search_similar_posts(db, query=query, username=username, limit=limit)


@router.get("/wisdom-warriors/monthly-views")
async def wisdom_warriors_monthly_views(
    month: str,
    apply_filters: bool = True,
    category: str | None = None,
    hashtags: list[str] | None = Query(default=None),
    mentions: list[str] | None = Query(default=None),
    keywords: list[str] | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list:
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        raise HTTPException(status_code=400, detail="month must be in YYYY-MM format")
    return await get_wisdom_warriors_monthly_views_filtered(
        db=db,
        month=month,
        apply_filters=apply_filters,
        hashtags=hashtags,
        mentions=mentions,
        caption_keywords=keywords,
        category=category,
    )
