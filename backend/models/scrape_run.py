from sqlalchemy import Column, Integer, Text, DateTime, func
from backend.db.base import Base


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scraper_type = Column(Text, nullable=False)        # 'posts' | 'profiles'
    trigger = Column(Text, nullable=False)             # 'manual' | 'scheduled'
    schedule_id = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Text, default="running")           # 'running' | 'completed' | 'failed'
    embedding_status = Column(Text, default="pending")  # 'pending' | 'completed' | 'failed' | 'skipped' | 'not_started'
    profiles_requested = Column(Integer, default=0)
    items_fetched = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    embedding_error_message = Column(Text, nullable=True)
    raw_logs = Column(Text, nullable=True)              # JSON array of raw scraper logs
    missing_usernames = Column(Text, nullable=True)     # JSON array of requested usernames with no profile data
    resume_payload = Column(Text, nullable=True)        # JSON payload used to resume run after process restart

    # Latest Apify metadata projection per stage.
    apify_posts_actor_id = Column(Text, nullable=True)
    apify_posts_run_id = Column(Text, nullable=True)
    apify_posts_dataset_id = Column(Text, nullable=True)
    apify_posts_started_at = Column(DateTime(timezone=True), nullable=True)
    apify_posts_finished_at = Column(DateTime(timezone=True), nullable=True)
    apify_posts_status = Column(Text, nullable=True)

    apify_profiles_actor_id = Column(Text, nullable=True)
    apify_profiles_run_id = Column(Text, nullable=True)
    apify_profiles_dataset_id = Column(Text, nullable=True)
    apify_profiles_started_at = Column(DateTime(timezone=True), nullable=True)
    apify_profiles_finished_at = Column(DateTime(timezone=True), nullable=True)
    apify_profiles_status = Column(Text, nullable=True)

    # JSON array of Apify stage lifecycle events (actor_call/refetch/status_update).
    apify_stage_history = Column(Text, nullable=True)
