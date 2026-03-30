import asyncio
import logging
from functools import partial

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.db.engine import get_db
from backend.models.profile import Profile
from backend.services.storage import upload_profile_image_to_supabase
from backend.schemas.profile import ProfileListResponse, ProfileDetail, SnapshotRead
from backend.repositories.profile_repo import list_profiles, get_profile_by_username, get_snapshots

router = APIRouter(prefix="/api/profiles", tags=["profiles"])
logger = logging.getLogger(__name__)


def _is_supabase_storage_url(url: str | None) -> bool:
    settings = get_settings()
    if not url or not settings.supabase_url:
        return False
    public_prefix = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/"
    return url.startswith(public_prefix)


async def _resolve_profile_picture_url(profile: Profile) -> str | None:
    source_urls = [profile.profile_pic_url_hd, profile.profile_pic_url]
    if not any(source_urls) or _is_supabase_storage_url(profile.profile_pic_url):
        return None
    try:
        loop = asyncio.get_running_loop()
        upload_result = await loop.run_in_executor(
            None,
            partial(upload_profile_image_to_supabase, source_urls, profile.id),
        )
        return upload_result.public_url if upload_result else None
    except Exception:
        logger.warning("Storage upload failed for profile %s during API backfill", profile.username, exc_info=True)
        return None


async def _backfill_profile_pictures(db: AsyncSession, profiles: list[Profile]) -> None:
    if not profiles:
        return

    updated = False
    resolved_urls = await asyncio.gather(*[_resolve_profile_picture_url(profile) for profile in profiles])
    for profile, public_url in zip(profiles, resolved_urls):
        if public_url:
            profile.profile_pic_url = public_url
            updated = True

    if updated:
        await db.commit()


@router.get("", response_model=ProfileListResponse)
async def get_profiles(
    search: str | None = None,
    verified: bool | None = None,
    business: bool | None = None,
    followers_min: int | None = None,
    followers_max: int | None = None,
    category: str | None = None,
    sort: str = "followers_count",
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> ProfileListResponse:
    items, total = await list_profiles(
        db, search, verified, business, followers_min, followers_max, category, sort, limit, offset
    )
    await _backfill_profile_pictures(db, list(items))
    return ProfileListResponse(items=items, total=total)


@router.get("/{username}", response_model=ProfileDetail)
async def get_profile(username: str, db: AsyncSession = Depends(get_db)) -> ProfileDetail:
    profile = await get_profile_by_username(db, username)
    if not profile:
        raise HTTPException(404)
    await _backfill_profile_pictures(db, [profile])
    snapshots = await get_snapshots(db, profile.id)
    return ProfileDetail.model_validate({**profile.__dict__, "snapshots": snapshots})
