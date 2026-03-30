from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.chat import SourceItem


async def retrieve_similar(
    db: AsyncSession,
    query_embedding: list[float],
    top_k: int = 10,
) -> tuple[list[dict], list[SourceItem]]:
    vec_str = f"[{','.join(str(x) for x in query_embedding)}]"

    profile_result = await db.execute(text(f"""
        SELECT username, full_name, biography, followers_count,
               1 - (embedding <=> '{vec_str}'::vector) AS score
        FROM profiles
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> '{vec_str}'::vector
        LIMIT 5
    """))
    profiles = [dict(r) for r in profile_result.mappings().all()]

    post_result = await db.execute(text(f"""
        SELECT owner_username, url, hashtags, likes_count,
               1 - (embedding <=> '{vec_str}'::vector) AS score
        FROM posts
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> '{vec_str}'::vector
        LIMIT 5
    """))
    posts = [dict(r) for r in post_result.mappings().all()]

    sources = [
        SourceItem(type="profile", username=p["username"], score=float(p["score"]))
        for p in profiles
    ] + [
        SourceItem(type="post", url=p["url"], username=p["owner_username"], score=float(p["score"]))
        for p in posts
    ]

    context_parts = []
    for p in profiles:
        context_parts.append(
            f"Profile: @{p['username']} ({p['full_name']}) — {p['followers_count']:,} followers. Bio: {p['biography'] or 'N/A'}"
        )
    for p in posts:
        tags = ", ".join(p["hashtags"] or [])[:100]
        context_parts.append(
            f"Post by @{p['owner_username']} — {p['likes_count']:,} likes. Tags: {tags}"
        )

    return context_parts, sources


def build_system_prompt(context_parts: list[str]) -> str:
    context_text = "\n".join(context_parts) if context_parts else "No matching data found."
    return (
        "You are an Instagram analytics assistant. "
        "Answer questions about Instagram profiles and posts using the data below. "
        "Be concise. Use numbers. Refer to accounts with @username.\n\n"
        f"RELEVANT DATA:\n{context_text}"
    )
