import asyncio
import json

from sqlalchemy import func, or_, select

from backend.db.engine import AsyncSessionLocal
from backend.models.post import Post


async def main() -> None:
    async with AsyncSessionLocal() as db:
        total = await db.scalar(select(func.count()).select_from(Post))
        with_display_url = await db.scalar(
            select(func.count()).select_from(Post).where(Post.display_url.is_not(None))
        )
        missing_storage = await db.scalar(
            select(func.count())
            .select_from(Post)
            .where(Post.display_url.is_not(None))
            .where(or_(Post.display_storage_url.is_(None), Post.display_storage_path.is_(None)))
        )
        print(
            json.dumps(
                {
                    "total_posts": int(total or 0),
                    "with_display_url": int(with_display_url or 0),
                    "missing_storage": int(missing_storage or 0),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
