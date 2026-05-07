from sqlalchemy import Column, DateTime, Integer, Text, UniqueConstraint, func

from backend.db.base import Base


class ScrapeRunProfileProgress(Base):
    __tablename__ = "scrape_run_profile_progress"
    __table_args__ = (
        UniqueConstraint("run_id", "username", name="uq_scrape_run_profile_progress_run_username"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, nullable=False, index=True)
    username = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="pending")
    attempt_count = Column(Integer, nullable=False, default=0)
    items_fetched = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    last_checkpoint_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
