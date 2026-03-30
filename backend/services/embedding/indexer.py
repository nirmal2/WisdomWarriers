from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.post import Post
from backend.models.profile import Profile
from backend.services.embedding.client import embed_texts

BATCH_SIZE = 100


async def embed_and_index_posts(db: AsyncSession, period_label: str) -> None:
    result = await db.execute(
        select(Post).where(Post.period_label == period_label, Post.embedding.is_(None))
    )
    posts = result.scalars().all()
    if not posts:
        return
    for i in range(0, len(posts), BATCH_SIZE):
        batch = posts[i : i + BATCH_SIZE]
        texts = [
            f"{p.owner_username} {' '.join(p.hashtags or [])}"
            for p in batch
        ]
        vectors = await embed_texts(texts)
        for post, vec in zip(batch, vectors):
            post.embedding = vec
    await db.flush()


async def embed_and_index_profiles(db: AsyncSession) -> None:
    result = await db.execute(select(Profile).where(Profile.embedding.is_(None)))
    profiles = result.scalars().all()
    if not profiles:
        return
    for i in range(0, len(profiles), BATCH_SIZE):
        batch = profiles[i : i + BATCH_SIZE]
        texts = [
            " ".join(filter(None, [p.username, p.full_name, p.biography, p.business_category]))
            for p in batch
        ]
        vectors = await embed_texts(texts)
        for profile, vec in zip(batch, vectors):
            profile.embedding = vec
    await db.flush()
