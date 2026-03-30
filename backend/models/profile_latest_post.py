from sqlalchemy import Column, Text, Integer, DateTime, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from backend.db.base import Base


class ProfileLatestPost(Base):
    __tablename__ = "profile_latest_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Text, nullable=False, index=True)  # soft ref — no FK so rows survive profile rewrites
    run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True, index=True)
    position = Column(Integer, nullable=False, default=0)
    post_id = Column(Text)
    short_code = Column(Text)
    post_type = Column(Text)
    product_type = Column(Text)
    url = Column(Text, nullable=False)
    caption = Column(Text)
    hashtags = Column(JSONB, default=list)
    mentions = Column(JSONB, default=list)
    comments_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    video_view_count = Column(Integer, default=0)
    timestamp = Column(DateTime(timezone=True))
    owner_username = Column(Text)
    owner_id = Column(Text)
    is_pinned = Column(Boolean, default=False)
    is_comments_disabled = Column(Boolean, default=False)
    raw_payload = Column(JSONB, default=dict)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())