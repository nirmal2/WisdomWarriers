import re
from collections.abc import Iterable, Sequence
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.scrape_profile import ScrapeProfile


def _normalize_usernames(usernames: Iterable[str]) -> list[str]:
    cleaned: list[str] = []
    for line in usernames:
        value = line.strip().rstrip("/")
        value = re.sub(r"\?.*$", "", value)
        if value:
            cleaned.append(value.split("/")[-1] if "/" in value else value)
    return list(dict.fromkeys(cleaned))


async def list_scrape_profiles(db: AsyncSession) -> Sequence[ScrapeProfile]:
    result = await db.execute(select(ScrapeProfile).order_by(ScrapeProfile.position, ScrapeProfile.id))
    return result.scalars().all()


async def replace_scrape_profiles(db: AsyncSession, usernames: Iterable[str]) -> list[str]:
    normalized = _normalize_usernames(usernames)
    await db.execute(delete(ScrapeProfile))
    for index, username in enumerate(normalized):
        db.add(ScrapeProfile(username=username, position=index))
    await db.flush()
    return normalized


async def ensure_scrape_profiles_seeded(db: AsyncSession, usernames: Iterable[str]) -> list[str]:
    existing = await list_scrape_profiles(db)
    if existing:
        return [item.username for item in existing]
    return await replace_scrape_profiles(db, usernames)


async def add_scrape_profile(
    db: AsyncSession,
    username: str,
    category: str | None = None,
    grade: str | None = None,
) -> ScrapeProfile:
    result = await db.execute(select(func.max(ScrapeProfile.position)))
    max_pos: int = result.scalar() or 0
    profile = ScrapeProfile(username=username.strip(), category=category, grade=grade, position=max_pos + 1)
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return profile


async def update_scrape_profile_fields(
    db: AsyncSession,
    profile_id: int,
    username: str | None = None,
    category: str | None = None,
    grade: str | None = None,
    set_fields: set[str] | None = None,
) -> ScrapeProfile | None:
    profile = await db.get(ScrapeProfile, profile_id)
    if profile is None:
        return None
    explicitly_set = set_fields or set()
    if "username" in explicitly_set and username is not None:
        profile.username = username.strip()
    if "category" in explicitly_set:
        profile.category = category
    if "grade" in explicitly_set:
        profile.grade = grade
    await db.flush()
    await db.refresh(profile)
    return profile


async def delete_scrape_profile(db: AsyncSession, profile_id: int) -> bool:
    profile = await db.get(ScrapeProfile, profile_id)
    if profile is None:
        return False
    await db.delete(profile)
    await db.flush()
    return True