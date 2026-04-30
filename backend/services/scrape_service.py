import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
from datetime import date, datetime, timezone
from functools import partial

logger = logging.getLogger(__name__)

from sqlalchemy import delete, func, select

from backend.db.engine import AsyncSessionLocal
from backend.models.post import Post
from backend.models.post_snapshot import PostSnapshot
from backend.models.profile import Profile
from backend.models.profile_snapshot import ProfileSnapshot
from backend.models.scrape_run import ScrapeRun
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


async def _reset_posts_table(db) -> int:
    result = await db.execute(delete(Post))
    await db.flush()
    return result.rowcount or 0


def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _is_timestamp_within_range(timestamp: datetime | None, date_from: str | None, date_to: str | None) -> bool:
    start = _parse_iso_date(date_from)
    end = _parse_iso_date(date_to)

    if start is None and end is None:
        return True
    if timestamp is None:
        return False

    post_date = timestamp.date()
    if start is not None and post_date < start:
        return False
    if end is not None and post_date > end:
        return False
    return True


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


def _load_json_log_lines(raw_logs: str | None) -> list[str]:
    if not raw_logs:
        return []
    try:
        loaded = json.loads(raw_logs)
        return [line for line in loaded if isinstance(line, str)]
    except (json.JSONDecodeError, TypeError):
        return []


async def _append_run_log(db, run_id: int, message: str) -> None:
    run = await db.get(ScrapeRun, run_id)
    if run is None:
        return
    lines = _load_json_log_lines(run.raw_logs)
    lines.append(message)
    run.raw_logs = json.dumps(lines)
    await db.flush()


async def _extend_run_logs(db, run_id: int, messages: list[str]) -> None:
    if not messages:
        return
    run = await db.get(ScrapeRun, run_id)
    if run is None:
        return
    lines = _load_json_log_lines(run.raw_logs)
    lines.extend([message for message in messages if isinstance(message, str)])
    run.raw_logs = json.dumps(lines)
    await db.flush()


async def run_posts_scrape(
    usernames: list[str],
    scraper_type: str = "posts",
    trigger: str = "manual",
    schedule_id: int | None = None,
    results_limit: int = 100,
    only_posts_newer_than: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    frequency: str = "on_demand",
    data_detail_level: str = "basicData",
    shared_scraped_at: datetime | None = None,
    enable_embeddings: bool = True,
    batch_mode: bool = False,
    existing_run_id: int | None = None,
    finalize_run: bool = True,
    apify_token: str | None = None,
) -> int:
    async with AsyncSessionLocal() as db:
        await _purge_ignored_instagram_account(db)
        if existing_run_id is not None:
            run = await db.get(ScrapeRun, existing_run_id)
            if run is None:
                raise ValueError(f"Run {existing_run_id} not found")
            await scrape_run_repo.update_run(db, run.id, {
                "status": "running",
                "embedding_status": "pending" if enable_embeddings else "skipped",
                "profiles_requested": len(usernames),
                "error_message": None,
                "embedding_error_message": None,
            })
        else:
            run = await scrape_run_repo.create_run(db, {
                "scraper_type": scraper_type,
                "trigger": trigger,
                "schedule_id": schedule_id,
                "embedding_status": "pending" if enable_embeddings else "skipped",
                "profiles_requested": len(usernames),
            })
        scraped_at = shared_scraped_at or datetime.now(timezone.utc)

        period_label = derive_period_label(frequency)
        fetched = 0
        skipped_outside_range = 0
        deleted_posts = 0
        embedding_status = "pending" if enable_embeddings else "skipped"
        embedding_error_message: str | None = None
        try:
            await _append_run_log(db, run.id, f"Posts stage started for {len(usernames)} profile(s).")
            deleted_posts = await _reset_posts_table(db)
            await _append_run_log(
                db,
                run.id,
                f"Posts stage reset canonical posts table and removed {deleted_posts} existing row(s).",
            )
            await db.commit()
            if date_from or date_to:
                requested_window = f"{date_from or 'any'} → {date_to or 'any'}"
                await _append_run_log(db, run.id, f"Posts stage date filter applied: {requested_window}.")
                await db.commit()
            await _append_run_log(db, run.id, "Posts stage: waiting for Apify actor to return results..." if batch_mode else "Posts stage: fetching post batches from Apify...")
            await db.commit()
            
            # Scrape either all profiles' posts in one batch or one profile at a time.
            all_raw_items = []
            all_raw_logs = []
            
            if batch_mode:
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        partial(run_posts_actor, usernames, results_limit, only_posts_newer_than, data_detail_level, apify_token),
                    ),
                    timeout=max(60, int(get_settings().apify_actor_timeout_seconds)),
                )
                # Handle both old (list) and new (tuple) return types for backwards compatibility
                if isinstance(result, tuple):
                    raw_items, raw_logs = result
                else:
                    raw_items = result
                    raw_logs = []
                all_raw_items.extend(raw_items)
                all_raw_logs.extend(raw_logs)
            else:
                async def _fetch_posts_batch(username: str):
                    return await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, partial(run_posts_actor, [username], results_limit, only_posts_newer_than, data_detail_level, apify_token)
                        ),
                        timeout=max(60, int(get_settings().apify_actor_timeout_seconds)),
                    )

                parallelism = max(1, int(get_settings().profile_scrape_parallelism))
                semaphore = asyncio.Semaphore(parallelism)

                async def _bounded_fetch(username: str):
                    async with semaphore:
                        return await _fetch_posts_batch(username)

                tasks = [asyncio.create_task(_bounded_fetch(username)) for username in usernames]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for username, result in zip(usernames, results):
                    if isinstance(result, Exception):
                        logger.warning("Posts scrape failed for %s", username, exc_info=result)
                        continue
                    # Handle both old (list) and new (tuple) return types for backwards compatibility
                    if isinstance(result, tuple):
                        raw_items, raw_logs = result
                    else:
                        raw_items = result
                        raw_logs = []
                    all_raw_items.extend(raw_items)
                    all_raw_logs.extend(raw_logs)
            
            raw_items = all_raw_items
            raw_logs = all_raw_logs
            if raw_logs:
                await _extend_run_logs(db, run.id, raw_logs)
                await db.commit()

            # ── debug dump ────────────────────────────────────────────────
            _dump_posts_debug(run.id, usernames, raw_items)
            # ─────────────────────────────────────────────────────────────

            for raw in raw_items:
                norm = normalize_post(raw)
                url = norm.get("url", "")
                if not url:
                    continue
                if not _is_timestamp_within_range(norm.get("timestamp"), date_from, date_to):
                    skipped_outside_range += 1
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
                snap = await post_repo.insert_snapshot(db, {
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
                    "mentions": norm.get("mentions") or [],
                    "tagged_users": norm.get("tagged_users") or [],
                    "coauthor_producers": norm.get("coauthor_producers") or [],
                    "period_label": period_label,
                    "scraped_at": scraped_at,
                })
                await post_repo.replace_snapshot_hashtags(
                    db,
                    snapshot_id=snap.id,
                    post_id=norm["id"],
                    run_id=run.id,
                    period_label=period_label,
                    owner_username=norm.get("owner_username"),
                    hashtags=norm.get("hashtags") or [],
                )
                await post_repo.replace_snapshot_mentions(
                    db,
                    snapshot_id=snap.id,
                    post_id=norm["id"],
                    run_id=run.id,
                    period_label=period_label,
                    owner_username=norm.get("owner_username"),
                    mentions=norm.get("mentions") or [],
                )
                await post_repo.replace_snapshot_tagged_users(
                    db,
                    snapshot_id=snap.id,
                    post_id=norm["id"],
                    run_id=run.id,
                    period_label=period_label,
                    owner_username=norm.get("owner_username"),
                    tagged_users=norm.get("tagged_users") or [],
                )
                fetched += 1
                await scrape_run_repo.update_run(db, run.id, {"items_fetched": fetched})
                if fetched == 1 or fetched % 25 == 0:
                    await _append_run_log(db, run.id, f"Posts stage: persisted {fetched} post(s) so far.")
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
                        await _append_run_log(db, run.id, "Posts stage: generating embeddings...")
                        await db.commit()
                        await embed_and_index_posts(db, period_label)
                        embedding_status = "completed"
                    except Exception as exc:
                        embedding_status = "failed"
                        embedding_error_message = str(exc)
            status_update = {
                "embedding_status": embedding_status,
                "items_fetched": fetched,
                "embedding_error_message": embedding_error_message,
            }
            if finalize_run:
                status_update.update({
                    "status": "completed",
                    "finished_at": datetime.now(timezone.utc),
                })
                await _append_run_log(db, run.id, "Posts stage completed.")
            await scrape_run_repo.update_run(db, run.id, status_update)
        except Exception as exc:
            await _append_run_log(db, run.id, f"Posts stage failed: {exc}")
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
    existing_run_id: int | None = None,
    finalize_run: bool = True,
    apify_token: str | None = None,
) -> int:
    async with AsyncSessionLocal() as db:
        await _purge_ignored_instagram_account(db)
        if existing_run_id is not None:
            run = await db.get(ScrapeRun, existing_run_id)
            if run is None:
                raise ValueError(f"Run {existing_run_id} not found")
            await scrape_run_repo.update_run(db, run.id, {
                "status": "running",
                "embedding_status": "pending" if enable_embeddings else "skipped",
                "profiles_requested": len(usernames),
                "error_message": None,
                "embedding_error_message": None,
            })
        else:
            run = await scrape_run_repo.create_run(db, {
                "scraper_type": "profiles",
                "trigger": trigger,
                "schedule_id": schedule_id,
                "embedding_status": "pending" if enable_embeddings else "skipped",
                "profiles_requested": len(usernames),
            })
        await _append_run_log(db, run.id, f"Profiles stage started for {len(usernames)} profile(s).")
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
            await _append_run_log(
                db,
                run.id,
                "Profiles stage: waiting for Apify actor results..." if batch_mode else "Profiles stage: fetching profile batches from Apify...",
            )
            await db.commit()
            if batch_mode:
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, partial(run_profiles_actor, usernames, apify_token)
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
                            None, partial(run_profiles_actor, [username], apify_token)
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
                    if fetched == 1 or fetched % 10 == 0 or fetched == len(requested_usernames):
                        await _append_run_log(
                            db,
                            run.id,
                            f"Profiles stage: persisted {fetched}/{len(requested_usernames)} profile(s).",
                        )
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
                await _extend_run_logs(db, run.id, all_raw_logs)
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
                        await _append_run_log(db, run.id, "Profiles stage: generating embeddings...")
                        await db.commit()
                        await embed_and_index_profiles(db)
                        embedding_status = "completed"
                    except Exception as exc:
                        embedding_status = "failed"
                        embedding_error_message = str(exc)
            status_update = {
                "embedding_status": embedding_status,
                "items_fetched": fetched,
                "embedding_error_message": embedding_error_message,
            }
            if finalize_run:
                status_update.update({
                    "status": "completed",
                    "finished_at": datetime.now(timezone.utc),
                })
                await _append_run_log(db, run.id, "Profiles stage completed.")
            else:
                await _append_run_log(db, run.id, "Profiles stage completed. Handing off to posts stage...")
            await scrape_run_repo.update_run(db, run.id, status_update)
        except Exception as exc:
            await _append_run_log(db, run.id, f"Profiles stage failed: {exc}")
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
    date_from: str | None = None,
    date_to: str | None = None,
    data_detail_level: str = "basicData",
    enable_embeddings: bool = True,
    batch_mode: bool = False,
    trigger: str = "manual",
    schedule_id: int | None = None,
    frequency: str = "on_demand",
    combined_run_id: int | None = None,
    apify_token: str | None = None,
) -> None:
    """
    Orchestrates a combined profile + post scrape in sequence using a shared timestamp.
    - First scrapes profiles
    - Then scrapes posts
    - Both use the same scraped_at timestamp for all records
    """
    # Generate a shared timestamp for both scrapers
    shared_scraped_at = datetime.now(timezone.utc)

    if combined_run_id is not None:
        async with AsyncSessionLocal() as db:
            await _append_run_log(db, combined_run_id, "Combined scrape started.")
            await db.commit()

    # Run profiles scrape first
    await run_profiles_scrape(
        usernames,
        trigger=trigger,
        schedule_id=schedule_id,
        frequency=frequency,
        shared_scraped_at=shared_scraped_at,
        batch_mode=batch_mode,
        enable_embeddings=enable_embeddings,
        existing_run_id=combined_run_id,
        finalize_run=False,
        apify_token=apify_token,
    )

    if combined_run_id is not None:
        async with AsyncSessionLocal() as db:
            await _append_run_log(db, combined_run_id, "Starting posts stage...")
            await db.commit()

    # Then run posts scrape with the same timestamp
    await run_posts_scrape(
        usernames,
        scraper_type="posts",
        trigger=trigger,
        schedule_id=schedule_id,
        results_limit=results_limit,
        only_posts_newer_than=only_posts_newer_than,
        date_from=date_from,
        date_to=date_to,
        frequency=frequency,
        data_detail_level=data_detail_level,
        shared_scraped_at=shared_scraped_at,
        batch_mode=batch_mode,
        enable_embeddings=enable_embeddings,
        existing_run_id=combined_run_id,
        finalize_run=True,
        apify_token=apify_token,
    )


def _looks_like_post_url(url: str) -> bool:
    value = (url or "").lower()
    return "/p/" in value or "/reel/" in value or "/tv/" in value


def _parse_dt(value):
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


async def recover_posts_from_debug(run_id: int) -> dict:
    debug_path = Path(_DEBUG_DIR) / f"posts_run_{run_id}.json"
    if not debug_path.exists():
        raise FileNotFoundError(f"Debug file not found: {debug_path}")

    payload = json.loads(debug_path.read_text(encoding="utf-8"))
    normalized = payload.get("normalized") or []
    imported = 0
    skipped_non_post_url = 0

    async with AsyncSessionLocal() as db:
        run = await db.get(ScrapeRun, run_id)
        if run is None:
            raise ValueError(f"Run {run_id} not found")

        period_label = (run.started_at or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
        scraped_at = run.started_at or datetime.now(timezone.utc)
        post_columns = set(Post.__table__.columns.keys())
        snapshot_columns = set(PostSnapshot.__table__.columns.keys())

        for item in normalized:
            url = item.get("url")
            if not url or not _looks_like_post_url(url):
                skipped_non_post_url += 1
                continue

            row = dict(item)
            row["id"] = _post_id(url, period_label)
            row["period_label"] = period_label
            row["run_id"] = run_id
            row["scraped_at"] = scraped_at
            row["timestamp"] = _parse_dt(row.get("timestamp"))

            post_data = {k: v for k, v in row.items() if k in post_columns}
            await post_repo.upsert_post(db, post_data)

            snap_data = {
                "post_id": post_data["id"],
                "run_id": run_id,
                "owner_username": post_data.get("owner_username"),
                "url": post_data["url"],
                "timestamp": post_data.get("timestamp"),
                "likes_count": post_data.get("likes_count", 0) or 0,
                "video_play_count": post_data.get("video_play_count", 0) or 0,
                "type": post_data.get("type"),
                "video_url": post_data.get("video_url"),
                "display_url": post_data.get("display_url"),
                "display_storage_path": post_data.get("display_storage_path"),
                "display_storage_url": post_data.get("display_storage_url"),
                "caption": post_data.get("caption"),
                "product_type": post_data.get("product_type"),
                "input_url": post_data.get("input_url"),
                "hashtags": post_data.get("hashtags") or [],
                "mentions": post_data.get("mentions") or [],
                "tagged_users": post_data.get("tagged_users") or [],
                "coauthor_producers": post_data.get("coauthor_producers") or [],
                "period_label": period_label,
                "scraped_at": scraped_at,
            }
            snap_data = {k: v for k, v in snap_data.items() if k in snapshot_columns}
            snap = await post_repo.insert_snapshot(db, snap_data)
            await post_repo.replace_snapshot_hashtags(
                db,
                snapshot_id=snap.id,
                post_id=post_data["id"],
                run_id=run_id,
                period_label=period_label,
                owner_username=post_data.get("owner_username"),
                hashtags=post_data.get("hashtags") or [],
            )
            await post_repo.replace_snapshot_mentions(
                db,
                snapshot_id=snap.id,
                post_id=post_data["id"],
                run_id=run_id,
                period_label=period_label,
                owner_username=post_data.get("owner_username"),
                mentions=post_data.get("mentions") or [],
            )
            await post_repo.replace_snapshot_tagged_users(
                db,
                snapshot_id=snap.id,
                post_id=post_data["id"],
                run_id=run_id,
                period_label=period_label,
                owner_username=post_data.get("owner_username"),
                tagged_users=post_data.get("tagged_users") or [],
            )
            imported += 1

        await scrape_run_repo.update_run(db, run_id, {
            "status": "completed",
            "embedding_status": "skipped",
            "items_fetched": imported,
            "error_message": None,
            "embedding_error_message": None,
            "finished_at": datetime.now(timezone.utc),
        })
        await db.commit()

        posts_rows = await db.scalar(select(func.count()).select_from(PostSnapshot).where(PostSnapshot.run_id == run_id))

    return {
        "run_id": run_id,
        "imported_posts": imported,
        "skipped_non_post_urls": skipped_non_post_url,
        "post_snapshot_rows": int(posts_rows or 0),
    }
