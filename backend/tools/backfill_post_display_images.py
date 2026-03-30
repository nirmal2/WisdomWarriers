import argparse
import asyncio
import json
from typing import Optional

from sqlalchemy import or_, select, update

from backend.db.engine import AsyncSessionLocal
from backend.models.post import Post
from backend.models.post_snapshot import PostSnapshot
from backend.services.storage import upload_display_image_to_supabase


async def backfill(limit: Optional[int] = None, run_id: Optional[int] = None) -> dict:
    checked = 0
    uploaded = 0
    failed = 0
    skipped_no_result = 0

    async with AsyncSessionLocal() as db:
        query = (
            select(Post)
            .where(Post.display_url.is_not(None))
            .where(or_(Post.display_storage_url.is_(None), Post.display_storage_path.is_(None)))
            .order_by(Post.scraped_at.desc().nullslast(), Post.id.asc())
        )
        if run_id is not None:
            query = query.where(Post.run_id == run_id)
        if limit is not None and limit > 0:
            query = query.limit(limit)

        result = await db.execute(query)
        posts = result.scalars().all()

        for post in posts:
            checked += 1
            try:
                upload_result = await asyncio.to_thread(
                    upload_display_image_to_supabase,
                    post.display_url,
                    post.run_id or 0,
                    post.id,
                )
                if upload_result is None:
                    skipped_no_result += 1
                    continue

                post.display_storage_path = upload_result.path
                post.display_storage_url = upload_result.public_url

                await db.execute(
                    update(PostSnapshot)
                    .where(PostSnapshot.post_id == post.id)
                    .values(
                        display_storage_path=upload_result.path,
                        display_storage_url=upload_result.public_url,
                    )
                )
                uploaded += 1

                if uploaded % 25 == 0:
                    await db.commit()
            except Exception:
                failed += 1

        await db.commit()

    return {
        "checked": checked,
        "uploaded": uploaded,
        "failed": failed,
        "skipped_no_result": skipped_no_result,
        "run_id_filter": run_id,
        "limit": limit,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill post display images into Supabase storage.")
    parser.add_argument("--limit", type=int, default=None, help="Optional max number of posts to process")
    parser.add_argument("--run-id", type=int, default=None, help="Optional run_id filter")
    args = parser.parse_args()

    summary = asyncio.run(backfill(limit=args.limit, run_id=args.run_id))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
