from apscheduler.triggers.cron import CronTrigger
from backend.services.scheduler.setup import get_scheduler
from backend.db.engine import AsyncSessionLocal
from backend.repositories.scrape_profile_repo import list_scrape_profiles
from backend.repositories.schedule_repo import get_active_schedules, update_schedule
from backend.services.scrape_service import run_posts_scrape, run_profiles_scrape
from datetime import datetime, timezone


async def run_scheduled_job(schedule_id: int) -> None:
    async with AsyncSessionLocal() as db:
        from backend.repositories.schedule_repo import get_schedule
        schedule = await get_schedule(db, schedule_id)
        if not schedule or not schedule.is_active:
            return
        usernames = [row.username for row in await list_scrape_profiles(db)]
        if schedule.scraper_type == "profiles":
            await run_profiles_scrape(usernames, "scheduled", schedule_id, schedule.frequency)
        else:
            await run_posts_scrape(
                usernames=usernames,
                scraper_type="posts",
                trigger="scheduled",
                schedule_id=schedule_id,
                results_limit=schedule.results_limit,
                only_posts_newer_than=schedule.only_posts_newer_than,
                frequency=schedule.frequency,
            )
        await update_schedule(db, schedule_id, {"last_run_at": datetime.now(timezone.utc)})
        await db.commit()


async def register_schedule(schedule_id: int, cron_expr: str) -> None:
    scheduler = get_scheduler()
    job_id = f"schedule_{schedule_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(
        run_scheduled_job,
        CronTrigger.from_crontab(cron_expr),
        id=job_id,
        args=[schedule_id],
        replace_existing=True,
    )


async def unregister_schedule(schedule_id: int) -> None:
    scheduler = get_scheduler()
    job_id = f"schedule_{schedule_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


async def load_all_schedules() -> None:
    async with AsyncSessionLocal() as db:
        schedules = await get_active_schedules(db)
        for s in schedules:
            if s.cron_expr:
                await register_schedule(s.id, s.cron_expr)
