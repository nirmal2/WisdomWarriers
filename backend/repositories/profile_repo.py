from typing import Optional, Sequence
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.profile import Profile
from backend.models.profile_snapshot import ProfileSnapshot


async def upsert_profile(db: AsyncSession, data: dict) -> Profile:
    profile = await db.get(Profile, data["id"])
    if profile is None:
        profile = Profile(**data)
        db.add(profile)
    else:
        for k, v in data.items():
            setattr(profile, k, v)
    await db.flush()
    return profile


async def get_profile_by_username(db: AsyncSession, username: str) -> Optional[Profile]:
    result = await db.execute(select(Profile).where(Profile.username == username))
    return result.scalar_one_or_none()


async def list_profiles(
    db: AsyncSession,
    search: Optional[str] = None,
    verified: Optional[bool] = None,
    business: Optional[bool] = None,
    followers_min: Optional[int] = None,
    followers_max: Optional[int] = None,
    category: Optional[str] = None,
    sort: str = "followers_count",
    limit: int = 50,
    offset: int = 0,
) -> tuple[Sequence[Profile], int]:
    q = select(Profile)
    if search:
        term = f"%{search}%"
        q = q.where(or_(Profile.username.ilike(term), Profile.full_name.ilike(term)))
    if verified is not None:
        q = q.where(Profile.is_verified == verified)
    if business is not None:
        q = q.where(Profile.is_business_account == business)
    if followers_min is not None:
        q = q.where(Profile.followers_count >= followers_min)
    if followers_max is not None:
        q = q.where(Profile.followers_count <= followers_max)
    if category:
        q = q.where(Profile.business_category == category)

    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar_one()

    sort_col = getattr(Profile, sort, Profile.followers_count)
    q = q.order_by(sort_col.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all(), total


async def get_snapshots(db: AsyncSession, profile_id: str) -> Sequence[ProfileSnapshot]:
    result = await db.execute(
        select(ProfileSnapshot)
        .where(ProfileSnapshot.profile_id == profile_id)
        .order_by(ProfileSnapshot.scraped_at)
    )
    return result.scalars().all()


async def insert_snapshot(db: AsyncSession, data: dict) -> ProfileSnapshot:
    snap = ProfileSnapshot(**data)
    db.add(snap)
    await db.flush()
    return snap
