from datetime import datetime
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.profile_latest_post import ProfileLatestPost


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        parsed = value.strip()
        if parsed.endswith("Z"):
            parsed = parsed[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(parsed)
        except ValueError:
            return None
    return None


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


async def replace_profile_latest_posts(
    db: AsyncSession,
    profile_id: str,
    run_id: int,
    latest_posts: list[dict[str, Any]],
    scraped_at: datetime | None = None,
) -> int:
    # Do NOT delete — rows accumulate as a snapshot log per run_id.

    rows: list[ProfileLatestPost] = []
    for position, raw in enumerate(latest_posts or []):
        url = raw.get("url")
        if not url:
            continue
        rows.append(
            ProfileLatestPost(
                profile_id=profile_id,
                run_id=run_id,
                position=position,
                post_id=str(raw.get("id")) if raw.get("id") is not None else None,
                short_code=raw.get("shortCode"),
                post_type=raw.get("type"),
                product_type=raw.get("productType"),
                url=url,
                caption=raw.get("caption"),
                hashtags=raw.get("hashtags") or [],
                mentions=raw.get("mentions") or [],
                comments_count=_as_int(raw.get("commentsCount"), 0),
                likes_count=_as_int(raw.get("likesCount"), 0),
                video_view_count=_as_int(raw.get("videoViewCount"), 0),
                timestamp=_parse_timestamp(raw.get("timestamp")),
                owner_username=raw.get("ownerUsername"),
                owner_id=str(raw.get("ownerId")) if raw.get("ownerId") is not None else None,
                is_pinned=bool(raw.get("isPinned", False)),
                is_comments_disabled=bool(raw.get("isCommentsDisabled", False)),
                raw_payload=raw,
                scraped_at=scraped_at,
            )
        )

    if rows:
        db.add_all(rows)
        await db.flush()
    return len(rows)