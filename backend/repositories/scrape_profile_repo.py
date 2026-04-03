import re
from collections.abc import Iterable, Sequence
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.scrape_profile import ScrapeProfile


def _normalize_username(value: str) -> str:
    cleaned = value.strip().lstrip("@").rstrip("/")
    cleaned = re.sub(r"\?.*$", "", cleaned)
    if not cleaned:
        return ""
    return cleaned.split("/")[-1] if "/" in cleaned else cleaned


def _normalize_usernames(usernames: Iterable[str]) -> list[str]:
    cleaned: list[str] = []
    for line in usernames:
        value = _normalize_username(line)
        if value:
            cleaned.append(value)
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
    profile = ScrapeProfile(username=_normalize_username(username), category=category, grade=grade, position=max_pos + 1)
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return profile


async def add_scrape_profiles_bulk(
    db: AsyncSession,
    profiles: Iterable[dict[str, str | None]],
) -> tuple[list[ScrapeProfile], list[str]]:
    normalized_entries: list[tuple[str, str | None, str | None]] = []
    seen: set[str] = set()

    for item in profiles:
        username = _normalize_username(str(item.get("username", "")))
        if not username:
            continue
        key = username.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized_entries.append((username, item.get("category"), item.get("grade")))

    if not normalized_entries:
        return [], []

    usernames_lower = [username.lower() for username, _, _ in normalized_entries]
    existing_result = await db.execute(
        select(ScrapeProfile.username).where(func.lower(ScrapeProfile.username).in_(usernames_lower))
    )
    existing_usernames = {username.lower() for (username,) in existing_result.all()}

    result = await db.execute(select(func.max(ScrapeProfile.position)))
    max_pos: int = result.scalar() or 0

    created: list[ScrapeProfile] = []
    skipped_existing: list[str] = []

    for username, category, grade in normalized_entries:
        if username.lower() in existing_usernames:
            skipped_existing.append(username)
            continue

        max_pos += 1
        profile = ScrapeProfile(username=username, category=category, grade=grade, position=max_pos)
        db.add(profile)
        created.append(profile)
        existing_usernames.add(username.lower())

    await db.flush()
    for profile in created:
        await db.refresh(profile)

    return created, skipped_existing


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