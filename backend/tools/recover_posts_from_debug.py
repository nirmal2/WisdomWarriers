import argparse
import asyncio
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import func, select

from backend.db.engine import AsyncSessionLocal
from backend.models.post_snapshot import PostSnapshot
from backend.models.scrape_run import ScrapeRun
from backend.repositories import post_repo, scrape_run_repo


def looks_like_post_url(url: str) -> bool:
    u = (url or "").lower()
    return "/p/" in u or "/reel/" in u or "/tv/" in u


def parse_dt(value):
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            # Support both Z and +00:00 formats.
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


async def recover(debug_file: Path) -> dict:
    payload = json.loads(debug_file.read_text(encoding="utf-8"))
    run_id = int(payload.get("run_id"))
    normalized = payload.get("normalized") or []

    imported = 0
    skipped_non_post_url = 0

    async with AsyncSessionLocal() as db:
        run = await db.get(ScrapeRun, run_id)
        if run is None:
            raise RuntimeError(f"Run {run_id} not found")

        ref_date = run.started_at.date() if run.started_at else date.today()
        period_label = ref_date.strftime("%Y-%m-%d")
        scraped_at = run.started_at or datetime.now(timezone.utc)

        snapshot_columns = set(PostSnapshot.__table__.columns.keys())

        for item in normalized:
            url = item.get("url")
            if not url or not looks_like_post_url(url):
                skipped_non_post_url += 1
                continue

            row = dict(item)
            row["id"] = hashlib.sha256(f"{url}:{period_label}".encode()).hexdigest()[:32]
            row["period_label"] = period_label
            row["run_id"] = run_id
            row["scraped_at"] = scraped_at
            row["timestamp"] = parse_dt(row.get("timestamp"))

            snapshot_data = {
                "post_id": row["id"],
                "run_id": run_id,
                "owner_username": row.get("owner_username"),
                "url": row["url"],
                "timestamp": row.get("timestamp"),
                "likes_count": row.get("likes_count", 0) or 0,
                "video_play_count": row.get("video_play_count", 0) or 0,
                "type": row.get("type"),
                "video_url": row.get("video_url"),
                "display_url": row.get("display_url"),
                "display_storage_path": row.get("display_storage_path"),
                "display_storage_url": row.get("display_storage_url"),
                "caption": row.get("caption"),
                "product_type": row.get("product_type"),
                "input_url": row.get("input_url"),
                "hashtags": row.get("hashtags") or [],
                "coauthor_producers": row.get("coauthor_producers") or [],
                "period_label": period_label,
                "scraped_at": scraped_at,
            }
            snapshot_data = {k: v for k, v in snapshot_data.items() if k in snapshot_columns}
            await post_repo.insert_snapshot(db, snapshot_data)

            imported += 1

        await scrape_run_repo.update_run(
            db,
            run_id,
            {
                "status": "completed",
                "embedding_status": "skipped",
                "items_fetched": imported,
                "error_message": None,
                "embedding_error_message": None,
                "finished_at": datetime.now(timezone.utc),
            },
        )
        await db.commit()

    async with AsyncSessionLocal() as db:
        snapshot_rows = await db.scalar(select(func.count()).select_from(PostSnapshot).where(PostSnapshot.run_id == run_id))

    return {
        "run_id": run_id,
        "period_label": period_label,
        "imported_posts": imported,
        "skipped_non_post_urls": skipped_non_post_url,
        "snapshot_rows_for_run": int(snapshot_rows or 0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Recover posts and snapshots for a failed run from debug_output JSON.")
    parser.add_argument("--file", required=True, help="Path to debug_output/posts_run_<id>.json")
    args = parser.parse_args()

    result = asyncio.run(recover(Path(args.file)))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
