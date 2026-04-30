from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func, Boolean
from sqlalchemy.dialects.postgresql import JSONB, VECTOR
from backend.db.base import Base


class PostSnapshot(Base):
    __tablename__ = "post_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Text, nullable=False, index=True)  # soft ref — history must survive post table resets
    run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True, index=True)
    owner_username = Column(Text, index=True)
    url = Column(Text, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=True)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    video_view_count = Column(Integer, default=0)
    video_play_count = Column(Integer, default=0)
    type = Column(Text)
    video_url = Column(Text)
    display_url = Column(Text)
    display_storage_path = Column(Text)
    display_storage_url = Column(Text)
    caption = Column(Text)
    product_type = Column(Text)
    input_url = Column(Text)
    hashtags = Column(JSONB, default=list)
    mentions = Column(JSONB, default=list)
    tagged_users = Column(JSONB, default=list)
    coauthor_producers = Column(JSONB, default=list)
    period_label = Column(Text, nullable=False, index=True)
    is_pinned = Column(Boolean, default=False)
    embedding = Column(VECTOR(1536), nullable=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
