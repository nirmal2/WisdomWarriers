from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from backend.db.base import Base


class ProfileSnapshot(Base):
    __tablename__ = "profile_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Text, nullable=False, index=True)   # soft ref — no FK so history survives profile rewrites
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    followers_count = Column(Integer, default=0)
    follows_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    period_label = Column(Text, nullable=False, index=True)
    run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True)
