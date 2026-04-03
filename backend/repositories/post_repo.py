from datetime import date
from typing import Optional, Sequence
from sqlalchemy import Date, Text, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.post import Post
from backend.models.post_snapshot import PostSnapshot
from backend.models.profile import Profile


TAGGED_GROUP_TERMS = {
    "isha": [
        "ishafoundation",
        "savesoil",
        "sadhguru",
        "soilhealth",
        "climateaction",
        "sustainability",
        "sadhgurumargam",
        "mysticsmusings",
        "dhyanalinga",
        "devi",
        "lingabhairavi",
        "bhairavi",
        "adhiyogi",
    ]
}


async def upsert_post(db: AsyncSession, data: dict) -> Post:
    owner_username = (data.get("owner_username") or "").strip()
    if owner_username and not data.get("profile_id"):
        profile_id = await db.scalar(
            select(Profile.id).where(func.lower(Profile.username) == owner_username.lower()).limit(1)
        )
        if profile_id is not None:
            data["profile_id"] = profile_id

    post = await db.get(Post, data["id"])
    if post is None:
        post = Post(**data)
        db.add(post)
    else:
        for k, v in data.items():
            setattr(post, k, v)
    await db.flush()
    return post


async def get_post_by_id(db: AsyncSession, post_id: str) -> Optional[Post]:
    return await db.get(Post, post_id)


async def get_snapshots_by_url(db: AsyncSession, post_url: str) -> Sequence[PostSnapshot]:
    result = await db.execute(
        select(PostSnapshot)
        .where(PostSnapshot.url == post_url)
        .order_by(PostSnapshot.scraped_at)
    )
    return result.scalars().all()


async def insert_snapshot(db: AsyncSession, data: dict) -> PostSnapshot:
    snap = PostSnapshot(**data)
    db.add(snap)
    await db.flush()
    return snap


def _clean_filter_values(values: Sequence[str] | None) -> list[str]:
    if not values:
        return []
    return list(dict.fromkeys(value.strip() for value in values if value and value.strip()))


def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


async def list_posts(
    db: AsyncSession,
    username: Optional[str] = None,
    post_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    likes_min: Optional[int] = None,
    hashtag: Optional[str] = None,
    hashtags: Sequence[str] | None = None,
    mentions: Sequence[str] | None = None,
    keywords: Sequence[str] | None = None,
    tagged_group: Optional[str] = None,
    period_label: Optional[str] = None,
    sort: str = "likes_count",
    limit: int = 50,
    offset: int = 0,
) -> tuple[Sequence[Post], int]:
    q = select(Post)
    parsed_date_from = _parse_iso_date(date_from)
    parsed_date_to = _parse_iso_date(date_to)

    if username:
        q = q.where(Post.owner_username == username)
    if post_type:
        q = q.where(func.lower(func.coalesce(Post.type, "")).like(f"%{post_type.lower()}%"))
    if parsed_date_from:
        q = q.where(cast(Post.timestamp, Date) >= parsed_date_from)
    if parsed_date_to:
        q = q.where(cast(Post.timestamp, Date) <= parsed_date_to)
    if likes_min is not None:
        q = q.where(Post.likes_count >= likes_min)

    hashtag_terms = _clean_filter_values([*(hashtags or []), hashtag] if hashtag else hashtags)
    mention_terms = _clean_filter_values(mentions)
    keyword_terms = _clean_filter_values(keywords)

    content_filters = []
    if hashtag_terms:
        hashtag_text = func.lower(func.coalesce(cast(Post.hashtags, Text), ""))
        content_filters.extend(hashtag_text.like(f"%{term.lower()}%") for term in hashtag_terms)
    if mention_terms:
        mention_text = func.lower(func.coalesce(cast(Post.mentions, Text), ""))
        content_filters.extend(mention_text.like(f"%{term.lower()}%") for term in mention_terms)
    if keyword_terms:
        caption_text = func.lower(func.coalesce(Post.caption, ""))
        content_filters.extend(caption_text.like(f"%{term.lower()}%") for term in keyword_terms)
    if content_filters:
        q = q.where(or_(*content_filters))

    if tagged_group:
        terms = TAGGED_GROUP_TERMS.get(tagged_group.lower(), [])
        if terms:
            q = q.where(
                or_(
                    *[
                        or_(
                            func.lower(func.coalesce(Post.caption, "")).like(f"%{term}%"),
                            func.lower(func.coalesce(Post.owner_username, "")).like(f"%{term}%"),
                            func.lower(func.coalesce(cast(Post.hashtags, Text), "")).like(f"%{term}%"),
                            func.lower(func.coalesce(cast(Post.coauthor_producers, Text), "")).like(f"%{term}%"),
                        )
                        for term in terms
                    ]
                )
            )
    if period_label:
        q = q.where(Post.period_label == period_label)

    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar_one()

    sort_col = getattr(Post, sort, Post.likes_count)
    q = q.order_by(sort_col.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all(), total
