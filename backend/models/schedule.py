from sqlalchemy import Column, Integer, Text, Boolean, DateTime, func
from backend.db.base import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    scraper_type = Column(Text, nullable=False)        # 'posts' | 'profiles'
    frequency = Column(Text, nullable=False)           # 'daily' | 'weekly' | 'monthly' | 'on_demand'
    cron_expr = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    batch_mode = Column(Boolean, default=False)
    results_limit = Column(Integer, default=27)
    only_posts_newer_than = Column(Text, nullable=True)
    actor_id = Column(Text, nullable=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
