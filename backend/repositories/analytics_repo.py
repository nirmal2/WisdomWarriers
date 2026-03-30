from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.post import Post
from backend.models.scrape_profile import ScrapeProfile


WISDOM_WARRIOR_ALLOWED_MENTIONS = [
    "ishafoundation",
    "adiyogi.official",
    "sadhguru",
    "sadhgurutamil",
    "sadhgurutelugu",
    "sadhguru.hindiofficial",
    "sadhguru.malayalam",
    "sadhguru_marathi_official",
    "sadhgurubangla",
    "sadhguru_kannada_official",
]

WISDOM_WARRIOR_ALLOWED_HASHTAGS = [
    "Isha",
    "Ishafoundation",
    "Ishayogacenter",
    "Sadhguru",
    "Sadhgurujaggivasudev",
    "Jaggi",
    "Adiyogi",
    "Linga Bhairavi",
    "Adiyogishiva",
    "ஈஷா",
]

WISDOM_WARRIOR_ALLOWED_CAPTION_KEYWORDS = [
    "Isha",
    "Ishafoundation",
    "Ishayogacenter",
    "Sadhguru",
    "Sadhgurujaggivasudev",
    "Jaggi",
    "Adiyogi",
    "Linga Bhairavi",
    "Adiyogishiva",
    "ஈஷா",
    "ईशा",
    "ఇషా",
    "ഇഷ",
    "ಇಶಾ",
    "சத்குரு",
    "సద్గురు",
    "ಸದ್ಗುರು",
    "സദ്‍ഗുരു",
    "सद्गुरु",
]


def _normalize_hashtag(value: str) -> str:
    return "".join((value or "").strip().lstrip("#").casefold().split())


def _normalize_mention(value: str) -> str:
    return (value or "").strip().lstrip("@").casefold()


ALLOWED_HASHTAG_MAP = {
    _normalize_hashtag(value): value for value in WISDOM_WARRIOR_ALLOWED_HASHTAGS
}
ALLOWED_MENTION_MAP = {
    _normalize_mention(value): value for value in WISDOM_WARRIOR_ALLOWED_MENTIONS
}
ALLOWED_CAPTION_KEYWORDS = [value.casefold() for value in WISDOM_WARRIOR_ALLOWED_CAPTION_KEYWORDS]


async def get_overview(db: AsyncSession) -> dict:
    result = await db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM profiles) AS total_profiles,
            (SELECT COUNT(*) FROM posts) AS total_posts,
            (SELECT COALESCE(AVG(followers_count), 0) FROM profiles) AS avg_followers,
            (SELECT username FROM profiles ORDER BY followers_count DESC LIMIT 1) AS top_profile
    """))
    row = result.mappings().first()
    return dict(row) if row else {}


async def get_follower_growth(db: AsyncSession, username: str | None = None) -> list[dict]:
    if username:
        result = await db.execute(text("""
            SELECT ps.period_label, ps.followers_count, p.username
            FROM profile_snapshots ps
            JOIN profiles p ON p.id = ps.profile_id
            WHERE p.username = :username
            ORDER BY ps.scraped_at
        """), {"username": username})
    else:
        result = await db.execute(text("""
            SELECT ps.period_label, SUM(ps.followers_count) AS followers_count, 'all' AS username
            FROM profile_snapshots ps
            GROUP BY ps.period_label
            ORDER BY ps.period_label
        """))
    return [dict(r) for r in result.mappings().all()]


async def get_top_profiles(db: AsyncSession, metric: str = "followers_count", limit: int = 10) -> list[dict]:
    allowed = {"followers_count", "follows_count", "posts_count"}
    col = metric if metric in allowed else "followers_count"
    result = await db.execute(
        text(f"SELECT username, {col} AS value FROM profiles ORDER BY {col} DESC LIMIT :limit"),
        {"limit": limit},
    )
    return [dict(r) for r in result.mappings().all()]


async def get_hashtag_frequency(db: AsyncSession, limit: int = 20) -> list[dict]:
    result = await db.execute(text("""
        SELECT tag, COUNT(*) AS count
        FROM posts, jsonb_array_elements_text(hashtags) AS tag
        GROUP BY tag
        ORDER BY count DESC
        LIMIT :limit
    """), {"limit": limit})
    return [dict(r) for r in result.mappings().all()]


async def get_engagement_by_profile(db: AsyncSession) -> list[dict]:
    result = await db.execute(text("""
        SELECT owner_username,
               ROUND(AVG(likes_count), 0)::int AS avg_likes,
               ROUND(AVG(video_play_count), 0)::int AS avg_plays,
               COUNT(*) AS post_count
        FROM posts
        GROUP BY owner_username
        ORDER BY avg_likes DESC
        LIMIT 20
    """))
    return [dict(r) for r in result.mappings().all()]


async def get_post_volume(db: AsyncSession) -> list[dict]:
    result = await db.execute(text("""
        SELECT period_label, COUNT(*) AS post_count
        FROM posts
        GROUP BY period_label
        ORDER BY period_label
    """))
    return [dict(r) for r in result.mappings().all()]


async def get_wisdom_warriors_monthly_views(db: AsyncSession, month: str) -> list[dict]:
    profile_result = await db.execute(select(ScrapeProfile).order_by(ScrapeProfile.position, ScrapeProfile.id))
    profiles = profile_result.scalars().all()
    if not profiles:
        return []

    usernames = [profile.username.casefold() for profile in profiles]
    post_result = await db.execute(
        select(Post)
        .where(Post.owner_username.is_not(None))
        .where(Post.timestamp.is_not(None))
        .where(func.lower(Post.owner_username).in_(usernames))
    )
    posts = post_result.scalars().all()

    summary_by_username: dict[str, dict] = {
        profile.username.casefold(): {
            "username": profile.username,
            "month": month,
            "total_views": 0.0,
            "matched_hashtags": [],
            "matched_mentions": [],
        }
        for profile in profiles
    }

    for post in posts:
        if not post.timestamp or post.timestamp.strftime("%Y-%m") != month:
            continue

        username_key = (post.owner_username or "").casefold()
        summary = summary_by_username.get(username_key)
        if summary is None:
            continue

        hashtags = post.hashtags or []
        mentions = post.mentions or []
        caption_text = (post.caption or "").casefold()

        matched_hashtags = sorted(
            {
                ALLOWED_HASHTAG_MAP[normalized]
                for normalized in (_normalize_hashtag(value) for value in hashtags)
                if normalized in ALLOWED_HASHTAG_MAP
            }
        )
        matched_mentions = sorted(
            {
                ALLOWED_MENTION_MAP[normalized]
                for normalized in (_normalize_mention(value) for value in mentions)
                if normalized in ALLOWED_MENTION_MAP
            }
        )
        caption_match = any(keyword in caption_text for keyword in ALLOWED_CAPTION_KEYWORDS)

        if not matched_hashtags and not matched_mentions and not caption_match:
            continue

        coauthor_count = len(post.coauthor_producers or [])
        summary["total_views"] += float(post.video_view_count or 0) / max(1, coauthor_count + 1)
        summary["matched_hashtags"] = sorted(set(summary["matched_hashtags"]) | set(matched_hashtags))
        summary["matched_mentions"] = sorted(set(summary["matched_mentions"]) | set(matched_mentions))

    return [summary_by_username[profile.username.casefold()] for profile in profiles]
