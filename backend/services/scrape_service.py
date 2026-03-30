import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from functools import partial

logger = logging.getLogger(__name__)

from sqlalchemy import delete, func, select

from backend.db.engine import AsyncSessionLocal
from backend.models.post import Post
from backend.models.post_snapshot import PostSnapshot
from backend.models.profile import Profile
from backend.models.profile_snapshot import ProfileSnapshot
from backend.models.scrape_profile import ScrapeProfile
from backend.repositories import post_repo, profile_repo, scrape_run_repo
from backend.services.apify.normalizer import normalize_post, normalize_profile
from backend.services.apify.posts_runner import run_posts_actor
from backend.services.apify.profiles_runner import run_profiles_actor
from backend.config import get_settings
from backend.services.embedding.indexer import embed_and_index_posts, embed_and_index_profiles
from backend.services.scheduler.period import derive_period_label
from backend.services.storage import upload_display_image_to_supabase, upload_profile_image_to_supabase


def _post_id(url: str, period_label: str) -> str:
    return hashlib.sha256(f"{url}:{period_label}".encode()).hexdigest()[:32]


def _is_supabase_storage_url(url: str | None) -> bool:
    settings = get_settings()
    if not url or not settings.supabase_url:
        return False
    public_prefix = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/"
    return url.startswith(public_prefix)


async def _purge_ignored_instagram_account(db) -> None:
    ignored_usernames = ("instagram", "@instagram")

    profile_ids_result = await db.execute(
        select(Profile.id).where(func.lower(Profile.username).in_(ignored_usernames))
    )
    profile_ids = [row[0] for row in profile_ids_result.all()]

    await db.execute(
        delete(ScrapeProfile).where(func.lower(ScrapeProfile.username).in_(ignored_usernames))
    )
    await db.execute(
        delete(Post).where(func.lower(Post.owner_username).in_(ignored_usernames))
    )
    await db.execute(
        delete(PostSnapshot).where(func.lower(PostSnapshot.owner_username).in_(ignored_usernames))
    )

    if profile_ids:
        await db.execute(delete(ProfileSnapshot).where(ProfileSnapshot.profile_id.in_(profile_ids)))
        await db.execute(delete(Profile).where(Profile.id.in_(profile_ids)))

    await db.commit()


_DEBUG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "debug_output")


def _dump_posts_debug(run_id: int, usernames: list[str], raw_items: list[dict]) -> None:
    """Write raw + normalized post data to debug_output/posts_run_<id>.json for DB verification."""
    os.makedirs(_DEBUG_DIR, exist_ok=True)
    normalised = []
    error_items = 0
    valid_items = 0
    for raw in raw_items:
        if raw.get("error"):
            error_items += 1
        norm = normalize_post(raw)
        if norm.get("url"):
            valid_items += 1
        normalised.append({k: str(v) if hasattr(v, "isoformat") else v for k, v in norm.items()})
    payload = {
        "run_id": run_id,
        "usernames": usernames,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "total_items": len(raw_items),
        "valid_items": valid_items,
        "error_items": error_items,
        "raw": raw_items,
        "normalized": normalised,
    }
    path = os.path.join(_DEBUG_DIR, f"posts_run_{run_id}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)


async def run_posts_scrape(
    usernames: list[str],
    scraper_type: str = "posts",
    trigger: str = "manual",
    schedule_id: int | None = None,
    results_limit: int = 100,
    only_posts_newer_than: str | None = None,
    frequency: str = "on_demand",
    data_detail_level: str = "basicData",
    shared_scraped_at: datetime | None = None,
    enable_embeddings: bool = True,
) -> int:
    async with AsyncSessionLocal() as db:
        await _purge_ignored_instagram_account(db)
        run = await scrape_run_repo.create_run(db, {
            "scraper_type": scraper_type,
            "trigger": trigger,
            "schedule_id": schedule_id,
            "embedding_status": "pending" if enable_embeddings else "skipped",
            "profiles_requested": len(usernames),
        })
        await db.commit()

        scraped_at = shared_scraped_at or datetime.now(timezone.utc)

        period_label = derive_period_label(frequency)
        fetched = 0
        embedding_status = "pending" if enable_embeddings else "skipped"
        embedding_error_message: str | None = None
        try:
            # Run the synchronous Apify call in a thread so the event loop stays free
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, partial(run_posts_actor, usernames, results_limit, only_posts_newer_than, data_detail_level)
                ),
                timeout=max(60, int(get_settings().apify_actor_timeout_seconds)),
            )
            # Handle both old (list) and new (tuple) return types for backwards compatibility
            if isinstance(result, tuple):
                raw_items, raw_logs = result
            else:
                raw_items = result
                raw_logs = []
            
            # Store raw logs in the run
            if raw_logs:
                await scrape_run_repo.update_run(db, run.id, {"raw_logs": json.dumps(raw_logs)})
                await db.commit()

            # ── debug dump ────────────────────────────────────────────────
            _dump_posts_debug(run.id, usernames, raw_items)
            # ─────────────────────────────────────────────────────────────

            for raw in raw_items:
                norm = normalize_post(raw)
                url = norm.get("url", "")
                if not url:
                    continue
                norm["id"] = _post_id(url, period_label)

                display_url = norm.get("display_url")
                if display_url:
                    try:
                        upload_result = await asyncio.get_event_loop().run_in_executor(
                            None,
                            partial(upload_display_image_to_supabase, display_url, run.id, norm["id"]),
                        )
                        if upload_result:
                            norm["display_storage_path"] = upload_result.path
                            norm["display_storage_url"] = upload_result.public_url
                    except Exception:
                        logger.warning("Storage upload failed for post %s", norm["id"], exc_info=True)

                norm["period_label"] = period_label
                norm["scraped_at"] = scraped_at
                norm["run_id"] = run.id
                await post_repo.upsert_post(db, norm)
                await post_repo.insert_snapshot(db, {
                    "post_id": norm["id"],
                    "run_id": run.id,
                    "owner_username": norm.get("owner_username"),
                    "url": norm["url"],
                    "timestamp": norm.get("timestamp"),
                    "likes_count": norm.get("likes_count", 0) or 0,
                    "video_play_count": norm.get("video_play_count", 0) or 0,
                    "type": norm.get("type"),
                    "video_url": norm.get("video_url"),
                    "display_url": norm.get("display_url"),
                    "display_storage_path": norm.get("display_storage_path"),
                    "display_storage_url": norm.get("display_storage_url"),
                    "caption": norm.get("caption"),
                    "product_type": norm.get("product_type"),
                    "input_url": norm.get("input_url"),
                    "hashtags": norm.get("hashtags") or [],
                    "coauthor_producers": norm.get("coauthor_producers") or [],
                    "period_label": period_label,
                    "scraped_at": scraped_at,
                })
                fetched += 1
                await scrape_run_repo.update_run(db, run.id, {"items_fetched": fetched})
            await db.commit()
            if not enable_embeddings:
                embedding_status = "skipped"
            elif fetched == 0:
                embedding_status = "skipped"
            else:
                # Re-read from DB in case the user killed embeddings via the API
                await db.refresh(run)
                if run.embedding_status == "skipped":
                    embedding_status = "skipped"
                else:
                    try:
                        await embed_and_index_posts(db, period_label)
                        embedding_status = "completed"
                    except Exception as exc:
                        embedding_status = "failed"
                        embedding_error_message = str(exc)
            await scrape_run_repo.update_run(db, run.id, {
                "status": "completed",
                "embedding_status": embedding_status,
                "finished_at": datetime.now(timezone.utc),
                "items_fetched": fetched,
                "embedding_error_message": embedding_error_message,
            })
        except Exception as exc:
            await scrape_run_repo.update_run(db, run.id, {
                "status": "failed",
                "embedding_status": "not_started" if fetched == 0 else embedding_status,
                "finished_at": datetime.now(timezone.utc),
                "items_fetched": fetched,
                "error_message": str(exc),
                "embedding_error_message": embedding_error_message,
            })
        await db.commit()
        await _purge_ignored_instagram_account(db)
    return fetched


async def run_profiles_scrape(
    usernames: list[str],
    trigger: str = "manual",
    schedule_id: int | None = None,
    frequency: str = "on_demand",
    shared_scraped_at: datetime | None = None,
    batch_mode: bool = False,
    enable_embeddings: bool = True,
) -> int:
    async with AsyncSessionLocal() as db:
        await _purge_ignored_instagram_account(db)
        run = await scrape_run_repo.create_run(db, {
            "scraper_type": "profiles",
            "trigger": trigger,
            "schedule_id": schedule_id,
            "embedding_status": "pending" if enable_embeddings else "skipped",
            "profiles_requested": len(usernames),
        })
        await db.commit()

        # Keep profiles and upsert in place so posts can maintain a stable FK to profiles.
        logger.info("Starting profile upsert flow for run %d", run.id)

        # Use provided timestamp or generate new one
        scraped_at = shared_scraped_at or datetime.now(timezone.utc)

        period_label = derive_period_label(frequency)
        fetched = 0
        embedding_status = "pending" if enable_embeddings else "skipped"
        embedding_error_message: str | None = None
        requested_usernames: list[str] = []
        requested_keys: list[str] = []
        fetched_username_keys: set[str] = set()
        seen_requested: set[str] = set()
        for username in usernames:
            normalized = (username or "").strip().lstrip("@")
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen_requested:
                continue
            seen_requested.add(key)
            requested_keys.append(key)
            requested_usernames.append(normalized)
        try:
            # Scrape either one profile at a time or all profiles in one Apify call.
            all_raw_logs = []
            if batch_mode:
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, partial(run_profiles_actor, usernames)
                    ),
                    timeout=max(60, int(get_settings().apify_actor_timeout_seconds)),
                )
                if isinstance(result, tuple):
                    profile_batches = [result]
                else:
                    profile_batches = [(result, [])]
            else:
                profile_batches = []

                async def _fetch_profile_batch(username: str):
                    return await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, partial(run_profiles_actor, [username])
                        ),
                        timeout=max(60, int(get_settings().apify_actor_timeout_seconds)),
                    )

                parallelism = max(1, int(get_settings().profile_scrape_parallelism))
                semaphore = asyncio.Semaphore(parallelism)

                async def _bounded_fetch(username: str):
                    async with semaphore:
                        return await _fetch_profile_batch(username)

                tasks = [asyncio.create_task(_bounded_fetch(username)) for username in requested_usernames]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for username, result in zip(requested_usernames, results):
                    if isinstance(result, Exception):
                        logger.warning("Profile scrape failed for %s", username, exc_info=result)
                        continue
                    if isinstance(result, tuple):
                        profile_batches.append(result)
                    else:
                        profile_batches.append((result, []))

            for raw_items, raw_logs in profile_batches:
                all_raw_logs.extend(raw_logs)
                for raw in raw_items:
                    norm = normalize_profile(raw)
                    if not norm["id"] or not norm["username"]:
                        continue
                    fetched_username_keys.add(norm["username"].strip().lstrip("@").lower())

                    existing_profile = await db.get(Profile, norm["id"])
                    profile_image_urls = [norm.get("profile_pic_url_hd"), norm.get("profile_pic_url")]
                    should_upload_profile_pic = any(profile_image_urls)
                    if existing_profile and _is_supabase_storage_url(existing_profile.profile_pic_url):
                        # Reuse already-uploaded storage URL instead of uploading each scrape run.
                        norm["profile_pic_url"] = existing_profile.profile_pic_url
                        should_upload_profile_pic = False

                    if should_upload_profile_pic:
                        try:
                            upload_result = await asyncio.get_event_loop().run_in_executor(
                                None,
                                partial(upload_profile_image_to_supabase, profile_image_urls, norm["id"]),
                            )
                            if upload_result:
                                norm["profile_pic_url"] = upload_result.public_url
                            else:
                                logger.warning("Storage upload skipped for profile %s: no reachable image URL", norm["username"])
                        except Exception:
                            logger.warning("Storage upload failed for profile %s", norm["username"], exc_info=True)

                    profile = await profile_repo.upsert_profile(db, norm)
                    await profile_repo.insert_snapshot(db, {
                        "profile_id": profile.id,
                        "followers_count": norm["followers_count"],
                        "follows_count": norm["follows_count"],
                        "posts_count": norm["posts_count"],
                        "period_label": period_label,
                        "run_id": run.id,
                        "scraped_at": scraped_at,
                    })
                    fetched += 1
                    await scrape_run_repo.update_run(db, run.id, {"items_fetched": fetched})
                    await db.commit()

            missing_usernames = [
                requested_usernames[index]
                for index, key in enumerate(requested_keys)
                if key not in fetched_username_keys
            ]
            await scrape_run_repo.update_run(db, run.id, {"missing_usernames": json.dumps(missing_usernames)})
            await db.commit()
            
            # Store raw logs in the run
            if all_raw_logs:
                await scrape_run_repo.update_run(db, run.id, {"raw_logs": json.dumps(all_raw_logs)})
                await db.commit()
                
            await db.commit()
            if not enable_embeddings:
                embedding_status = "skipped"
            elif fetched == 0:
                embedding_status = "skipped"
            else:
                # Re-read from DB in case the user killed embeddings via the API
                await db.refresh(run)
                if run.embedding_status == "skipped":
                    embedding_status = "skipped"
                else:
                    try:
                        await embed_and_index_profiles(db)
                        embedding_status = "completed"
                    except Exception as exc:
                        embedding_status = "failed"
                        embedding_error_message = str(exc)
            await scrape_run_repo.update_run(db, run.id, {
                "status": "completed",
                "embedding_status": embedding_status,
                "finished_at": datetime.now(timezone.utc),
                "items_fetched": fetched,
                "embedding_error_message": embedding_error_message,
            })
        except Exception as exc:
            await scrape_run_repo.update_run(db, run.id, {
                "status": "failed",
                "embedding_status": "not_started" if fetched == 0 else embedding_status,
                "finished_at": datetime.now(timezone.utc),
                "items_fetched": fetched,
                "error_message": str(exc),
                "embedding_error_message": embedding_error_message,
            })
        await db.commit()
        await _purge_ignored_instagram_account(db)
    return fetched


async def run_combined_scrape(
    usernames: list[str],
    results_limit: int = 100,
    only_posts_newer_than: str | None = None,
    data_detail_level: str = "basicData",
    enable_embeddings: bool = True,
    batch_mode: bool = False,
    trigger: str = "manual",
    schedule_id: int | None = None,
    frequency: str = "on_demand",
) -> None:
    """
    Orchestrates a combined profile + post scrape in sequence using a shared timestamp.
    - First scrapes profiles
    - Then scrapes posts
    - Both use the same scraped_at timestamp for all records
    """
    # Generate a shared timestamp for both scrapers
    shared_scraped_at = datetime.now(timezone.utc)

    # Run profiles scrape first
    await run_profiles_scrape(
        usernames,
        trigger=trigger,
        schedule_id=schedule_id,
        frequency=frequency,
        shared_scraped_at=shared_scraped_at,
        batch_mode=batch_mode,
        enable_embeddings=enable_embeddings,
    )

    # Then run posts scrape with the same timestamp
    await run_posts_scrape(
        usernames,
        scraper_type="posts",
        trigger=trigger,
        schedule_id=schedule_id,
        results_limit=results_limit,
        only_posts_newer_than=only_posts_newer_than,
        frequency=frequency,
        data_detail_level=data_detail_level,
        shared_scraped_at=shared_scraped_at,
        enable_embeddings=enable_embeddings,
    )
