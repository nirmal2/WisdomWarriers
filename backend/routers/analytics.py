import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.engine import get_db
from backend.repositories.analytics_repo import (
    get_overview,
    get_follower_growth,
    get_top_profiles,
    get_hashtag_frequency,
    get_engagement_by_profile,
    get_post_volume,
    get_wisdom_warriors_monthly_views,
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


@router.get("/wisdom-warriors/monthly-views")
async def wisdom_warriors_monthly_views(
    month: str,
    db: AsyncSession = Depends(get_db),
) -> list:
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        raise HTTPException(status_code=400, detail="month must be in YYYY-MM format")
    return await get_wisdom_warriors_monthly_views(db, month)
