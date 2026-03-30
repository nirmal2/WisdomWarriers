from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import get_settings
from backend.db.engine import AsyncSessionLocal, create_tables
from backend.repositories.scrape_profile_repo import ensure_scrape_profiles_seeded
from backend.repositories.scrape_run_repo import fail_incomplete_runs
from backend.services.scheduler.setup import start_scheduler, stop_scheduler
from backend.services.scheduler.jobs import load_all_schedules
from backend.routers import scrape, schedules, profiles, posts, analytics, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    settings = get_settings()
    try:
        with open(settings.profiles_file, encoding="utf-8") as f:
            usernames = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        usernames = []
    async with AsyncSessionLocal() as db:
        await ensure_scrape_profiles_seeded(db, usernames)
        await fail_incomplete_runs(db, "Server restarted while scrape was in progress")
        await db.commit()
    start_scheduler()
    await load_all_schedules()
    yield
    stop_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Instagram Analytics API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in [scrape.router, schedules.router, profiles.router, posts.router, analytics.router, chat.router]:
        app.include_router(router)
    return app


app = create_app()
